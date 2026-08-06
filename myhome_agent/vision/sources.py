"""摄像头源 v0.3（§54.2.3 真实 RTSP 拉流）

v0.3 实现：
- RTSPCameraSource（基于 OpenCV cv2.VideoCapture）
- FileCameraSource（用于测试，回放 mp4）
- MockCameraSource（v0.2 兼容）
- 断流检测 + 自动重连（v0.3.B 增强）
"""
from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


class CameraSource(ABC):
    """摄像头拉流抽象"""

    @abstractmethod
    def open(self) -> bool: ...

    @abstractmethod
    def read(self) -> tuple[bool, np.ndarray | None]: ...

    @abstractmethod
    def close(self) -> None: ...

    @abstractmethod
    def is_opened(self) -> bool: ...

    @property
    @abstractmethod
    def source_type(self) -> str: ...


class RTSPCameraSource(CameraSource):
    """v0.3 基于 OpenCV 的 RTSP 拉流

    用法：
        source = RTSPCameraSource("rtsp://user:pass@192.168.1.100:554/stream1")
        source.open()
        ok, frame = source.read()  # frame: np.ndarray BGR
        source.close()

    特性：
    - FFMPEG 后端（支持更多 RTSP 变种）
    - 失败重试（指数退避）
    - 帧超时（防止卡死）
    """

    def __init__(
        self,
        rtsp_url: str,
        *,
        timeout_ms: int = 5000,
        retry_initial_seconds: float = 1.0,
        retry_max_seconds: float = 60.0,
    ):
        self.rtsp_url = rtsp_url
        self.timeout_ms = timeout_ms
        self.retry_initial = retry_initial_seconds
        self.retry_max = retry_max_seconds
        self._cap: Any = None
        self._consecutive_failures = 0
        self._last_attempt_at = 0.0
        self._next_retry_at = 0.0

    @property
    def source_type(self) -> str:
        return "rtsp"

    def open(self) -> bool:
        """打开 RTSP 流（v0.3 真实实现）"""
        if self._cap is not None and self._cap.isOpened():
            return True

        try:
            import cv2
        except ImportError:
            logger.error("缺少 opencv-python，无法打开 RTSP 流")
            return False

        try:
            # FFMPEG 后端
            self._cap = cv2.VideoCapture(self.rtsp_url, cv2.CAP_FFMPEG)
            # 设置超时
            self._cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, self.timeout_ms)
            self._cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, self.timeout_ms)
            # 降低缓冲区（减少延迟）
            self._cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

            if not self._cap.isOpened():
                logger.warning(f"RTSP 打开失败: {self.rtsp_url}")
                self._consecutive_failures += 1
                self._schedule_retry()
                return False

            logger.info(f"RTSP 已连接: {self._redact_url(self.rtsp_url)}")
            self._consecutive_failures = 0
            return True
        except Exception as e:
            logger.error(f"RTSP 打开异常: {e}")
            self._consecutive_failures += 1
            self._schedule_retry()
            return False

    def read(self) -> tuple[bool, np.ndarray | None]:
        """读一帧"""
        now = time.time()
        if now < self._next_retry_at:
            return False, None

        if self._cap is None or not self._cap.isOpened():
            if not self.open():
                return False, None

        try:
            ok, frame = self._cap.read()
            if not ok or frame is None:
                self._consecutive_failures += 1
                if self._consecutive_failures >= 3:
                    logger.warning("RTSP 连续失败 3 次，触发重连")
                    self.close()
                    self._schedule_retry()
                return False, None
            self._consecutive_failures = 0
            return True, frame
        except Exception as e:
            logger.error(f"RTSP 读帧异常: {e}")
            self._consecutive_failures += 1
            return False, None

    def close(self) -> None:
        if self._cap is not None:
            try:
                self._cap.release()
            except Exception:
                pass
            self._cap = None
            logger.debug("RTSP 已关闭")

    def is_opened(self) -> bool:
        return self._cap is not None and self._cap.isOpened()

    def _schedule_retry(self) -> None:
        """指数退避重连"""
        delay = min(self.retry_max, self.retry_initial * (2 ** self._consecutive_failures))
        self._next_retry_at = time.time() + delay
        logger.info(f"下次重连: {delay:.1f}s 后")

    @staticmethod
    def _redact_url(url: str) -> str:
        """日志脱敏：rtsp://user:pass@ip → rtsp://***@ip"""
        import re
        return re.sub(r"://[^@]+@", "://***@", url)


class FileCameraSource(CameraSource):
    """v0.3 文件摄像头（用于测试：mp4 视频文件）"""

    def __init__(self, file_path: str, loop: bool = True):
        self.file_path = file_path
        self.loop = loop
        self._cap: Any = None

    @property
    def source_type(self) -> str:
        return "file"

    def open(self) -> bool:
        try:
            import cv2
            self._cap = cv2.VideoCapture(self.file_path)
            return self._cap.isOpened()
        except ImportError:
            logger.error("缺少 opencv-python")
            return False

    def read(self) -> tuple[bool, np.ndarray | None]:
        if self._cap is None:
            if not self.open():
                return False, None
        ok, frame = self._cap.read()
        if not ok and self.loop:
            # 循环
            self._cap.set(1, 0)  # cv2.CAP_PROP_POS_FRAMES = 1
            ok, frame = self._cap.read()
        return ok, frame if ok else (False, None)

    def close(self) -> None:
        if self._cap is not None:
            self._cap.release()
            self._cap = None

    def is_opened(self) -> bool:
        return self._cap is not None and self._cap.isOpened()


class MockCameraSource(CameraSource):
    """v0.2 mock 摄像头（v0.3 保留供开发用）"""

    def __init__(self, camera_id: str = "mock", mock_event: bool = True):
        self.camera_id = camera_id
        self.mock_event = mock_event
        self._opened = False
        self._frame_count = 0
        self._cycle = 10

    @property
    def source_type(self) -> str:
        return "mock"

    def open(self) -> bool:
        self._opened = True
        return True

    def read(self) -> tuple[bool, np.ndarray | None]:
        self._frame_count += 1
        if self.mock_event and self._frame_count % self._cycle == 0:
            return True, None
        return False, None

    def close(self) -> None:
        self._opened = False

    def is_opened(self) -> bool:
        return self._opened
