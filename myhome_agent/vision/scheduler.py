"""多摄像头并发调度 v0.3（§54.4.3）

v0.3 实现：
- MultiCameraScheduler：N 路摄像头并发推理
- ThreadPoolExecutor（per-camera 独立线程）
- 性能监控（每帧延迟、CPU/队列长度）
- 降级策略（CPU > 80% → 降帧到 3 FPS）
- 健康上报（每分钟一次状态）

用法：
    scheduler = MultiCameraScheduler(vision_store, fps=5, max_workers=4)
    scheduler.add_camera("cam_porch", [PersonDetector(), MotionDetector()])
    scheduler.start()
    # ... 运行中 ...
    scheduler.stop()
    scheduler.get_stats()  # 性能统计
"""
from __future__ import annotations

import logging
import threading
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Any

from .pipeline import VisionEvent, VisionPipeline, VisionStore, MockCameraSource
from .sources import CameraSource, FileCameraSource, RTSPCameraSource, MockCameraSource
from .detectors import LocalDetector

logger = logging.getLogger(__name__)


@dataclass
class CameraStats:
    """单摄像头性能统计"""

    camera_id: str
    frames_processed: int = 0
    detections_total: int = 0
    avg_latency_ms: float = 0.0
    last_frame_at: int = 0
    errors: int = 0
    current_fps: float = 0.0


@dataclass
class SchedulerStats:
    """全局调度统计"""

    cameras: dict[str, CameraStats] = field(default_factory=dict)
    total_events: int = 0
    total_errors: int = 0
    cpu_overload_count: int = 0
    started_at: int = 0


class MultiCameraScheduler:
    """v0.3 多摄像头并发调度器

    设计：
    - 1 个主线程（协调 + 监控）
    - N 个 worker 线程（每摄像头 1 个，固定 5 FPS）
    - 共享 VisionStore
    - 失败隔离（单摄像头故障不影响其他）
    """

    def __init__(
        self,
        store: VisionStore,
        *,
        fps: int = 5,
        max_workers: int = 4,
        cpu_overload_threshold: float = 0.8,
        degrade_fps: int = 3,
    ):
        self.store = store
        self.fps = fps
        self.current_fps = fps
        self.max_workers = max_workers
        self.cpu_overload_threshold = cpu_overload_threshold
        self.degrade_fps = degrade_fps

        self._pipelines: dict[str, VisionPipeline] = {}
        self._sources: dict[str, CameraSource] = {}
        self._executor: ThreadPoolExecutor | None = None
        self._threads: dict[str, threading.Thread] = {}
        self._stop_flag = threading.Event()
        self._stats = SchedulerStats()
        self._event_callbacks: list = []
        self._lock = threading.Lock()

    def add_camera(
        self,
        camera_id: str,
        source: CameraSource,
        detectors: list[LocalDetector],
    ) -> None:
        """注册一台摄像头"""
        with self._lock:
            if camera_id in self._pipelines:
                logger.warning(f"camera {camera_id} 已存在，覆盖")
            self._sources[camera_id] = source
            pipeline = VisionPipeline(
                store=self.store,
                camera_id=camera_id,
                source=source,
                detectors=detectors,
                fps=self.current_fps,
            )
            self._pipelines[camera_id] = pipeline
            self._stats.cameras[camera_id] = CameraStats(camera_id=camera_id)
            logger.info(f"已注册摄像头: {camera_id} source={source.source_type}")

    def remove_camera(self, camera_id: str) -> None:
        """移除一台摄像头"""
        with self._lock:
            if camera_id in self._pipelines:
                self._sources[camera_id].close()
                del self._pipelines[camera_id]
                del self._sources[camera_id]
                del self._stats.cameras[camera_id]

    def on_event(self, callback) -> None:
        """注册事件回调（视觉事件触发时）"""
        self._event_callbacks.append(callback)

    def start(self) -> None:
        """启动调度器（启动所有摄像头 worker 线程）"""
        if self._executor is not None:
            return
        self._stop_flag.clear()
        self._stats.started_at = int(time.time())

        for cam_id, pipeline in self._pipelines.items():
            t = threading.Thread(
                target=self._camera_worker,
                args=(cam_id,),
                daemon=True,
                name=f"vision-{cam_id}",
            )
            self._threads[cam_id] = t
            t.start()
        logger.info(f"scheduler 启动: {len(self._pipelines)} 路摄像头 @ {self.current_fps} FPS")

    def stop(self) -> None:
        """停止调度器"""
        self._stop_flag.set()
        for source in self._sources.values():
            try:
                source.close()
            except Exception:
                pass
        for t in self._threads.values():
            t.join(timeout=2.0)
        self._threads.clear()
        logger.info("scheduler 已停止")

    def get_stats(self) -> dict:
        """获取性能统计（用于 PWA 监控面板）"""
        return {
            "current_fps": self.current_fps,
            "camera_count": len(self._pipelines),
            "total_events": self._stats.total_events,
            "total_errors": self._stats.total_errors,
            "cpu_overload_count": self._stats.cpu_overload_count,
            "uptime_seconds": int(time.time()) - self._stats.started_at if self._stats.started_at else 0,
            "cameras": {
                cid: {
                    "frames_processed": s.frames_processed,
                    "detections_total": s.detections_total,
                    "avg_latency_ms": round(s.avg_latency_ms, 2),
                    "current_fps": round(s.current_fps, 2),
                    "errors": s.errors,
                    "last_frame_at": s.last_frame_at,
                }
                for cid, s in self._stats.cameras.items()
            },
        }

    def _camera_worker(self, camera_id: str) -> None:
        """单摄像头 worker 循环"""
        pipeline = self._pipelines[camera_id]
        source = self._sources[camera_id]
        interval = 1.0 / self.current_fps
        logger.info(f"worker {camera_id} 启动")

        while not self._stop_flag.is_set():
            loop_start = time.time()
            try:
                if not source.is_opened():
                    source.open()
                events = pipeline.run_once()
                # 更新统计
                with self._lock:
                    stats = self._stats.cameras[camera_id]
                    stats.frames_processed += 1
                    if events:
                        stats.detections_total += len(events)
                        self._stats.total_events += len(events)
                        for cb in self._event_callbacks:
                            try:
                                cb(camera_id, events)
                            except Exception as e:
                                logger.error(f"event callback 失败: {e}")
                    latency_ms = (time.time() - loop_start) * 1000
                    # 指数移动平均
                    if stats.avg_latency_ms == 0:
                        stats.avg_latency_ms = latency_ms
                    else:
                        stats.avg_latency_ms = 0.9 * stats.avg_latency_ms + 0.1 * latency_ms
                    stats.last_frame_at = int(time.time())
            except Exception as e:
                logger.error(f"worker {camera_id} 异常: {e}")
                with self._lock:
                    self._stats.cameras[camera_id].errors += 1
                    self._stats.total_errors += 1
                time.sleep(1.0)
                continue

            # 睡眠到下一帧
            elapsed = time.time() - loop_start
            sleep_for = max(0, interval - elapsed)
            time.sleep(sleep_for)

        logger.info(f"worker {camera_id} 退出")

    def check_cpu_and_degrade(self) -> bool:
        """检查 CPU 负载，必要时降帧

        v0.3 简化：基于平均延迟判断（>200ms → 降帧）
        真实 v0.3.1 接 psutil.cpu_percent
        """
        if not self._stats.cameras:
            return False
        avg_latencies = [s.avg_latency_ms for s in self._stats.cameras.values() if s.avg_latency_ms > 0]
        if not avg_latencies:
            return False
        max_latency = max(avg_latencies)
        # 帧率对应延迟：5 FPS = 200ms 预算，3 FPS = 333ms
        target_latency = 1000.0 / self.current_fps
        if max_latency > target_latency * 1.5 and self.current_fps > self.degrade_fps:
            self.current_fps = self.degrade_fps
            self._stats.cpu_overload_count += 1
            logger.warning(
                f"CPU 过载（最大延迟 {max_latency:.0f}ms > 预算 {target_latency:.0f}ms），降帧到 {self.current_fps} FPS"
            )
            return True
        return False


# ============================================================
# 工具：从 VisionStore 自动构建 Scheduler
# ============================================================


def build_scheduler_from_store(
    store: VisionStore,
    *,
    fps: int = 5,
    max_workers: int = 4,
) -> MultiCameraScheduler:
    """从 VisionStore 加载所有摄像头并构建 scheduler

    用法：
        scheduler = build_scheduler_from_store(store, fps=5)
        # 自动加载 PersonDetector + MotionDetector
        scheduler.start()
    """
    from .detectors import PersonDetector, MotionDetector, FireDetector

    scheduler = MultiCameraScheduler(store, fps=fps, max_workers=max_workers)
    cameras = store.list_cameras(household_id=1)

    for cam in cameras:
        # 根据 capabilities 选择检测器
        detectors: list[LocalDetector] = [MotionDetector()]
        if cam.capabilities.get("person"):
            detectors.append(PersonDetector(device="cpu"))
        if cam.capabilities.get("fire"):
            detectors.append(FireDetector())
        if cam.capabilities.get("pose"):
            from .detectors import PoseDetector
            detectors.append(PoseDetector(device="cpu"))

        # 选 source
        if cam.rtsp_url.startswith("rtsp://"):
            source: CameraSource = RTSPCameraSource(cam.rtsp_url)
        elif cam.rtsp_url.startswith("mock://") or cam.rtsp_url == "":
            source = MockCameraSource(cam.id)
        else:
            # 文件或未知协议
            source = MockCameraSource(cam.id)

        scheduler.add_camera(cam.id, source, detectors)

    return scheduler
