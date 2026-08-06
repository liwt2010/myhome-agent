"""摄像头健康监控 v0.3

- 每 60s 巡检所有摄像头
- 检测到离线 → 写 audit + 通知 admin
- 自动恢复 → 记录 + 通知
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass

from .pipeline import VisionStore
from .scheduler import MultiCameraScheduler

logger = logging.getLogger(__name__)


@dataclass
class CameraHealth:
    """单摄像头健康状态"""

    camera_id: str
    is_online: bool
    last_seen_at: int
    consecutive_failures: int
    last_error: str | None = None


class CameraHealthMonitor:
    """v0.3 摄像头健康监控"""

    def __init__(
        self,
        store: VisionStore,
        scheduler: MultiCameraScheduler,
        *,
        check_interval_seconds: int = 60,
        offline_threshold_seconds: int = 90,
    ):
        self.store = store
        self.scheduler = scheduler
        self.check_interval = check_interval_seconds
        self.offline_threshold = offline_threshold_seconds
        self._last_check = 0
        self._notified_offline: set[str] = set()

    def check_once(self) -> list[CameraHealth]:
        """一次健康检查"""
        now = int(time.time())
        results: list[CameraHealth] = []
        stats = self.scheduler.get_stats()

        for cam_id, cam_stats in stats.get("cameras", {}).items():
            last_frame = cam_stats.get("last_frame_at", 0)
            is_online = (now - last_frame) < self.offline_threshold

            health = CameraHealth(
                camera_id=cam_id,
                is_online=is_online,
                last_seen_at=last_frame,
                consecutive_failures=cam_stats.get("errors", 0),
            )

            if not is_online and cam_id not in self._notified_offline:
                # 刚转离线
                self._notify_offline(cam_id, last_frame)
                self._notified_offline.add(cam_id)
            elif is_online and cam_id in self._notified_offline:
                # 刚恢复
                self._notify_recovered(cam_id)
                self._notified_offline.discard(cam_id)

            results.append(health)

        self._last_check = now
        return results

    def _notify_offline(self, camera_id: str, last_seen_at: int) -> None:
        """通知管理员摄像头离线"""
        logger.warning(f"[health] 摄像头离线: {camera_id} last_seen={last_seen_at}")
        # 写 audit
        self.store._conn().execute(
            """INSERT INTO events (kind, household_id, detail, ts)
               VALUES (?, 1, ?, strftime('%s', 'now'))""",
            ("camera_offline", f'{{"camera_id": "{camera_id}", "last_seen_at": {last_seen_at}}}'),
        )
        self.store._conn().commit()

    def _notify_recovered(self, camera_id: str) -> None:
        """通知摄像头恢复"""
        logger.info(f"[health] 摄像头恢复: {camera_id}")
        self.store._conn().execute(
            """INSERT INTO events (kind, household_id, detail, ts)
               VALUES (?, 1, ?, strftime('%s', 'now'))""",
            ("camera_online", f'{{"camera_id": "{camera_id}"}}'),
        )
        self.store._conn().commit()

    def run_forever(self) -> None:
        """永久循环（后台线程）"""
        logger.info(f"健康监控启动 interval={self.check_interval}s")
        while True:
            try:
                self.check_once()
            except Exception as e:
                logger.error(f"健康监控异常: {e}")
            time.sleep(self.check_interval)
