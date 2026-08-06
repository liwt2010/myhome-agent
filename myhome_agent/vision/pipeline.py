"""视觉管线 v0.2（§54）

v0.2 范围（mock 实现）：
- CameraSource 抽象 + MockCameraSource
- LocalDetector 抽象 + PersonDetector / MotionDetector（mock）
- LLMVisionAnalyzer 抽象 + MockLLMVision
- VisionPipeline：拉流 → 检测 → 视觉事件 → 写入 vision_events

v0.3 计划：真实 OpenCV + YOLO-nano
v0.5 计划：Whisper.cpp + 人脸 embedding
"""
from __future__ import annotations

import json
import logging
import sqlite3
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


# ============================================================
# 数据结构
# ============================================================


@dataclass
class Detection:
    """单次检测结果"""

    kind: str  # 'person' | 'motion' | 'face' | 'fall' | 'fire' | 'cry' | 'package'
    confidence: float
    bbox: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0)  # x, y, w, h 归一化
    attributes: dict = field(default_factory=dict)


@dataclass
class VisionEvent:
    """持续视觉事件"""

    camera_id: str
    household_id: int
    kind: str
    confidence: float
    bbox: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0)
    attributes: dict = field(default_factory=dict)
    snapshot_path: str | None = None
    started_at: int = field(default_factory=lambda: int(time.time()))
    ended_at: int | None = None


@dataclass
class Camera:
    id: str
    name: str
    rtsp_url: str
    location: str | None = None
    capabilities: dict = field(default_factory=dict)
    enabled: bool = True
    household_id: int = 1


@dataclass
class VisionResult:
    """LLM-Vision 分析结果"""

    answer: str
    confidence: float
    detected_objects: list[str] = field(default_factory=list)
    attributes: dict = field(default_factory=dict)


# ============================================================
# Layer 1：协议适配
# ============================================================


class CameraSource(ABC):
    """摄像头拉流抽象"""

    @abstractmethod
    def open(self) -> None: ...

    @abstractmethod
    def read(self) -> tuple[bool, "np.ndarray | None"]: ...

    @abstractmethod
    def close(self) -> None: ...

    @abstractmethod
    def is_opened(self) -> bool: ...


class RTSPCameraSource(CameraSource):
    """v0.3 实现：基于 OpenCV RTSP 拉流

    v0.2 占位：仅做类型声明，不实际拉流
    """

    def __init__(self, rtsp_url: str):
        self.rtsp_url = rtsp_url
        self._cap = None

    def open(self) -> None:
        # v0.3: cv2.VideoCapture(self.rtsp_url)
        logger.info(f"[v0.2 占位] RTSP 拉流待实现: {self.rtsp_url}")
        raise NotImplementedError("v0.3 接入 OpenCV 后启用")

    def read(self):
        return False, None

    def close(self):
        pass

    def is_opened(self) -> bool:
        return False


class MockCameraSource(CameraSource):
    """v0.2 mock 摄像头（用于开发与测试）"""

    def __init__(self, camera_id: str, mock_person: bool = True):
        self.camera_id = camera_id
        self.mock_person = mock_person
        self._opened = False
        self._frame_count = 0
        # mock 周期：每 10 帧出现 1 次人形
        self._cycle = 10

    def open(self) -> None:
        self._opened = True
        logger.debug(f"Mock camera {self.camera_id} opened")

    def read(self) -> tuple[bool, "np.ndarray | None"]:
        self._frame_count += 1
        if self.mock_person and self._frame_count % self._cycle == 0:
            # mock：返回 None 但 is_opened=True 表示有事件
            return True, None
        return False, None

    def close(self) -> None:
        self._opened = False

    def is_opened(self) -> bool:
        return self._opened


# ============================================================
# Layer 2：本地推理
# ============================================================


class LocalDetector(ABC):
    """本地推理器抽象"""

    @abstractmethod
    def detect(self, frame: Any) -> list[Detection]:
        """输入一帧（numpy 数组或 None），返回检测结果"""
        pass

    @property
    @abstractmethod
    def name(self) -> str: ...


class PersonDetector(LocalDetector):
    """v0.2 mock：随机返回人形检测

    v0.3 替换为 YOLO-nano
    """

    @property
    def name(self) -> str:
        return "person_detector_v0.2_mock"

    def detect(self, frame: Any) -> list[Detection]:
        import random

        if random.random() < 0.3:  # 30% 概率检测到人
            return [
                Detection(
                    kind="person",
                    confidence=0.85,
                    bbox=(0.4, 0.3, 0.2, 0.4),
                    attributes={"mock": True},
                )
            ]
        return []


class MotionDetector(LocalDetector):
    """简单运动检测（背景减除）"""

    @property
    def name(self) -> str:
        return "motion_detector_v0.2"

    def detect(self, frame: Any) -> list[Detection]:
        # v0.2 简化：v0.3 接 OpenCV 背景减除
        return []


# ============================================================
# Layer 3：LLM-Vision 兜底
# ============================================================


class LLMVisionAnalyzer(ABC):
    """LLM-Vision 抽象"""

    @abstractmethod
    def analyze(
        self,
        image: Any,
        prompt: str,
        context: dict | None = None,
    ) -> VisionResult: ...

    @property
    @abstractmethod
    def model(self) -> str: ...


class MockLLMVision(LLMVisionAnalyzer):
    """v0.2 mock LLM-Vision"""

    @property
    def model(self) -> str:
        return "mock-vision-1"

    def analyze(self, image: Any, prompt: str, context: dict | None = None) -> VisionResult:
        # v0.2 mock：固定回复
        return VisionResult(
            answer="（mock 视觉）我看到客厅里有人坐着，似乎在看电视。",
            confidence=0.75,
            detected_objects=["person", "tv"],
            attributes={"mock": True, "prompt": prompt[:50]},
        )


class OpenAIVisionAnalyzer(LLMVisionAnalyzer):
    """v0.3 实现：走 OpenAI GPT-4o（DeepSeek 暂不支持 Vision）"""

    def __init__(self, api_key: str, model: str = "gpt-4o", base_url: str | None = None):
        try:
            import openai
        except ImportError:
            raise ImportError("请 pip install openai")
        self._model = model
        self.client = openai.OpenAI(api_key=api_key, base_url=base_url)

    @property
    def model(self) -> str:
        return self._model

    def analyze(self, image: Any, prompt: str, context: dict | None = None) -> VisionResult:
        import base64

        # image 可以是 numpy 数组或文件路径
        if hasattr(image, "tobytes"):  # numpy 数组
            img_bytes = image.tobytes()
        elif isinstance(image, str):  # 文件路径
            with open(image, "rb") as f:
                img_bytes = f.read()
        else:
            img_bytes = image

        b64 = base64.b64encode(img_bytes).decode()

        resp = self.client.chat.completions.create(
            model=self._model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{b64}"},
                        },
                    ],
                }
            ],
            max_tokens=500,
        )

        return VisionResult(
            answer=resp.choices[0].message.content or "",
            confidence=0.8,  # 简化版：固定
            detected_objects=[],  # v0.3 解析
        )


# ============================================================
# 视觉事件存储
# ============================================================


class VisionStore:
    """vision_events + cameras 表的 SQLite 存储"""

    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=15)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        with self._conn() as c:
            c.executescript(
                """
                CREATE TABLE IF NOT EXISTS cameras (
                  id TEXT PRIMARY KEY,
                  household_id INTEGER NOT NULL DEFAULT 1,
                  name TEXT NOT NULL,
                  rtsp_url TEXT NOT NULL,
                  location TEXT,
                  capabilities TEXT NOT NULL DEFAULT '{}',
                  enabled INTEGER DEFAULT 1,
                  last_seen_at INTEGER,
                  created_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),
                  encrypted_rtsp_url TEXT
                );
                CREATE INDEX IF NOT EXISTS idx_cameras_household ON cameras(household_id);

                CREATE TABLE IF NOT EXISTS vision_events (
                  id INTEGER PRIMARY KEY,
                  camera_id TEXT NOT NULL,
                  household_id INTEGER NOT NULL DEFAULT 1,
                  kind TEXT NOT NULL,
                  confidence REAL,
                  bbox TEXT,
                  attributes TEXT,
                  snapshot_path TEXT,
                  started_at INTEGER NOT NULL,
                  ended_at INTEGER,
                  ts INTEGER NOT NULL DEFAULT (strftime('%s', 'now'))
                );
                CREATE INDEX IF NOT EXISTS idx_vision_events_camera ON vision_events(camera_id, ts DESC);
                CREATE INDEX IF NOT EXISTS idx_vision_events_household ON vision_events(household_id, ts DESC);
                CREATE INDEX IF NOT EXISTS idx_vision_events_kind ON vision_events(household_id, kind, ts DESC);
                """
            )

    def upsert_camera(self, cam: Camera, *, encrypt_url: bool = True) -> None:
        """v0.3：可选加密 rtsp_url"""
        encrypted = ""
        if encrypt_url and cam.rtsp_url:
            try:
                from .crypto import encrypt
                encrypted = encrypt(cam.rtsp_url)
            except Exception:
                encrypted = ""

        with self._conn() as c:
            c.execute(
                """INSERT OR REPLACE INTO cameras (
                  id, household_id, name, rtsp_url, location, capabilities, enabled, last_seen_at, encrypted_rtsp_url
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    cam.id,
                    cam.household_id,
                    cam.name,
                    cam.rtsp_url,  # 兼容期：仍写明文
                    cam.location,
                    json.dumps(cam.capabilities, ensure_ascii=False),
                    1 if cam.enabled else 0,
                    int(time.time()),
                    encrypted,
                ),
            )

    def get_camera(self, camera_id: str) -> Camera | None:
        """v0.3：取摄像头（自动解密 rtsp_url）"""
        with self._conn() as c:
            row = c.execute(
                "SELECT * FROM cameras WHERE id = ?", (camera_id,)
            ).fetchone()
        if not row:
            return None
        # v0.3 优先用 encrypted_rtsp_url
        rtsp_url = row["rtsp_url"]
        if row.get("encrypted_rtsp_url") if hasattr(row, "get") else row["encrypted_rtsp_url"]:
            try:
                from .crypto import decrypt
                rtsp_url = decrypt(row["encrypted_rtsp_url"])
            except Exception:
                pass
        return Camera(
            id=row["id"],
            name=row["name"],
            rtsp_url=rtsp_url,
            location=row["location"],
            capabilities=json.loads(row["capabilities"] or "{}"),
            enabled=bool(row["enabled"]),
            household_id=row["household_id"],
        )

    def list_cameras(self, household_id: int = 1) -> list[Camera]:
        with self._conn() as c:
            rows = c.execute(
                "SELECT * FROM cameras WHERE enabled = 1 AND household_id = ?",
                (household_id,),
            ).fetchall()
        return [
            Camera(
                id=r["id"],
                name=r["name"],
                rtsp_url=r["rtsp_url"],
                location=r["location"],
                capabilities=json.loads(r["capabilities"] or "{}"),
                enabled=bool(r["enabled"]),
                household_id=r["household_id"],
            )
            for r in rows
        ]

    def log_event(self, ev: VisionEvent) -> int:
        with self._conn() as c:
            cur = c.execute(
                """INSERT INTO vision_events (
                  camera_id, household_id, kind, confidence, bbox, attributes, snapshot_path, started_at, ended_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    ev.camera_id,
                    ev.household_id,
                    ev.kind,
                    ev.confidence,
                    json.dumps(ev.bbox),
                    json.dumps(ev.attributes, ensure_ascii=False),
                    ev.snapshot_path,
                    ev.started_at,
                    ev.ended_at,
                ),
            )
            return cur.lastrowid

    def recent_events(
        self,
        camera_id: str | None = None,
        kind: str | None = None,
        household_id: int = 1,
        since_seconds: int = 300,
    ) -> list[dict]:
        cutoff = int(time.time()) - since_seconds
        sql = "SELECT * FROM vision_events WHERE household_id = ? AND started_at >= ?"
        params: list[Any] = [household_id, cutoff]
        if camera_id:
            sql += " AND camera_id = ?"
            params.append(camera_id)
        if kind:
            sql += " AND kind = ?"
            params.append(kind)
        sql += " ORDER BY started_at DESC"
        with self._conn() as c:
            rows = c.execute(sql, params).fetchall()
        return [dict(r) for r in rows]


# ============================================================
# VisionPipeline：拉流 → 检测 → 事件
# ============================================================


class VisionPipeline:
    """视觉管线（v0.2 简化版）

    用法：
        store = VisionStore("data/myhome.db")
        source = MockCameraSource("cam_living_room")
        detectors = [PersonDetector()]
        pipeline = VisionPipeline(store, source, detectors, fps=5)
        pipeline.run_once()  # 跑一帧
    """

    def __init__(
        self,
        store: VisionStore,
        camera_id: str,
        source: CameraSource,
        detectors: list[LocalDetector],
        fps: int = 5,
    ):
        self.store = store
        self.camera_id = camera_id
        self.source = source
        self.detectors = detectors
        self.fps = fps
        self._running_events: dict[str, VisionEvent] = {}
        self._llm_vision: LLMVisionAnalyzer | None = None

    def set_llm_vision(self, analyzer: LLMVisionAnalyzer) -> None:
        self._llm_vision = analyzer

    def run_once(self) -> list[VisionEvent]:
        """跑一帧，返回本帧产生的视觉事件"""
        if not self.source.is_opened():
            self.source.open()

        ok, frame = self.source.read()
        if not ok:
            return []

        # 跑所有检测器
        detections: list[Detection] = []
        for det in self.detectors:
            detections.extend(det.detect(frame))

        # 转换为视觉事件
        new_events: list[VisionEvent] = []
        now = int(time.time())
        for d in detections:
            event_key = f"{self.camera_id}:{d.kind}"
            if event_key in self._running_events:
                # 已有持续事件
                self._running_events[event_key].ended_at = now
            else:
                # 新事件
                ev = VisionEvent(
                    camera_id=self.camera_id,
                    household_id=1,  # v0.2 简化
                    kind=d.kind,
                    confidence=d.confidence,
                    bbox=d.bbox,
                    attributes=d.attributes,
                    started_at=now,
                )
                self._running_events[event_key] = ev
                new_events.append(ev)
                # 写库
                self.store.log_event(ev)
                logger.info(
                    f"vision: cam={self.camera_id} kind={d.kind} conf={d.confidence:.2f}"
                )

        return new_events

    def run_forever(self) -> None:
        """永久循环（后台线程）"""
        interval = 1.0 / self.fps
        logger.info(f"vision pipeline {self.camera_id} 启动 fps={self.fps}")
        while True:
            try:
                self.run_once()
            except Exception as e:
                logger.error(f"vision pipeline 异常: {e}")
            time.sleep(interval)


# ============================================================
# 默认摄像头配置（v0.2 demo 用）
# ============================================================


def seed_demo_cameras(store: VisionStore, household_id: int = 1) -> int:
    """v0.2 demo 数据：3 个 mock 摄像头"""
    demo_cameras = [
        Camera(
            id="cam_porch",
            name="门口",
            rtsp_url="rtsp://demo:xxx@192.168.1.100:554/stream1",
            location="门口",
            capabilities={"motion": True, "person": True, "face": False, "fire": False, "package": True},
            household_id=household_id,
        ),
        Camera(
            id="cam_living_room",
            name="客厅",
            rtsp_url="rtsp://demo:xxx@192.168.1.101:554/stream1",
            location="客厅",
            capabilities={"motion": True, "person": True, "pose": True, "face": True},
            household_id=household_id,
        ),
        Camera(
            id="cam_kitchen",
            name="厨房",
            rtsp_url="rtsp://demo:xxx@192.168.1.102:554/stream1",
            location="厨房",
            capabilities={"motion": True, "person": True, "fire": True},
            household_id=household_id,
        ),
    ]
    for cam in demo_cameras:
        store.upsert_camera(cam)
    return len(demo_cameras)
