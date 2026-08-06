"""本地推理器 v0.3（§54.4 真实 YOLO 实现）

v0.3 范围：
- PersonDetector（YOLOv8n 真实推理）
- PoseDetector（YOLOv8n-pose，跌倒检测）
- FireDetector（YOLOv8n-cls 火焰/烟雾分类）
- MotionDetector（OpenCV 背景减除）

依赖：
- ultralytics（pip install ultralytics）
- opencv-python

模型下载（首次运行自动）：
- yolov8n.pt（~6MB，PersonDetector）
- yolov8n-pose.pt（~6MB，PoseDetector）
- 可选：yolov8n-cls.pt（~5MB，FireDetector）
"""
from __future__ import annotations

import logging
import os
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class Detection:
    """单次检测结果"""

    kind: str  # 'person' | 'motion' | 'face' | 'fall' | 'fire' | 'cry' | 'package' | 'pose'
    confidence: float
    bbox: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0)  # x, y, w, h 归一化
    attributes: dict = field(default_factory=dict)
    ts: int = field(default_factory=lambda: int(time.time()))


class LocalDetector(ABC):
    """本地推理器抽象"""

    @abstractmethod
    def detect(self, frame: np.ndarray | None) -> list[Detection]:
        """输入一帧（numpy 数组或 None），返回检测结果"""
        pass

    @property
    @abstractmethod
    def name(self) -> str: ...


# ============================================================
# PersonDetector：YOLOv8n 真实推理
# ============================================================


class PersonDetector(LocalDetector):
    """v0.3 YOLOv8n 真实人形检测

    模型：COCO 预训练 yolov8n.pt
    - 类别 0 = person
    - 类别 2 = car
    - 类别 15-23 = 动物（cat/dog/bird...）

    用法：
        det = PersonDetector(model_path="yolov8n.pt", device="cpu", conf_threshold=0.5)
        detections = det.detect(frame)  # frame: np.ndarray (H, W, 3) BGR
    """

    PERSON_CLASS_ID = 0
    ANIMAL_CLASS_IDS = {15, 16, 17, 18, 19, 20, 21, 22, 23}
    VEHICLE_CLASS_IDS = {2, 3, 5, 7}  # car, motorcycle, bus, truck

    def __init__(
        self,
        model_path: str = "yolov8n.pt",
        device: str = "cpu",
        conf_threshold: float = 0.5,
        imgsz: int = 640,
    ):
        self.model_path = model_path
        self.device = device
        self.conf_threshold = conf_threshold
        self.imgsz = imgsz
        self._model = None
        self._load_error: str | None = None

    def _ensure_loaded(self) -> bool:
        """懒加载 YOLO 模型"""
        if self._model is not None:
            return True
        if self._load_error:
            return False
        try:
            from ultralytics import YOLO

            logger.info(f"加载 YOLO 模型: {self.model_path}")
            self._model = YOLO(self.model_path)
            # 设置设备
            if self.device:
                self._model.to(self.device)
            logger.info(f"YOLO 模型就绪: device={self.device}")
            return True
        except ImportError as e:
            self._load_error = f"未安装 ultralytics: {e}"
            logger.error(self._load_error)
            return False
        except Exception as e:
            self._load_error = f"YOLO 加载失败: {e}"
            logger.error(self._load_error)
            return False

    @property
    def name(self) -> str:
        return f"person_detector_v0.3_yolov8n_{self.device}"

    def detect(self, frame: np.ndarray | None) -> list[Detection]:
        if frame is None:
            return []
        if not self._ensure_loaded():
            return []

        try:
            # YOLO 推理
            results = self._model(
                frame,
                imgsz=self.imgsz,
                conf=self.conf_threshold,
                verbose=False,
            )
        except Exception as e:
            logger.error(f"YOLO 推理失败: {e}")
            return []

        detections: list[Detection] = []
        h, w = frame.shape[:2]
        for r in results:
            boxes = r.boxes
            if boxes is None:
                continue
            for box in boxes:
                cls_id = int(box.cls[0])
                conf = float(box.conf[0])
                xyxy = box.xyxy[0].cpu().numpy()  # [x1, y1, x2, y2]
                x1, y1, x2, y2 = xyxy
                # 归一化
                bbox = (x1 / w, y1 / h, (x2 - x1) / w, (y2 - y1) / h)

                if cls_id == self.PERSON_CLASS_ID:
                    detections.append(
                        Detection(
                            kind="person",
                            confidence=conf,
                            bbox=tuple(bbox),  # type: ignore
                            attributes={"class_id": cls_id, "model": "yolov8n"},
                        )
                    )
                elif cls_id in self.ANIMAL_CLASS_IDS:
                    class_name = self._model.names.get(cls_id, "animal")
                    detections.append(
                        Detection(
                            kind="animal",
                            confidence=conf,
                            bbox=tuple(bbox),  # type: ignore
                            attributes={"class": class_name},
                        )
                    )
                elif cls_id in self.VEHICLE_CLASS_IDS:
                    class_name = self._model.names.get(cls_id, "vehicle")
                    detections.append(
                        Detection(
                            kind="vehicle",
                            confidence=conf,
                            bbox=tuple(bbox),  # type: ignore
                            attributes={"class": class_name},
                        )
                    )

        return detections


# ============================================================
# PoseDetector：YOLOv8n-pose 跌倒检测
# ============================================================


class PoseDetector(LocalDetector):
    """v0.3 YOLOv8n-pose 跌倒检测

    算法：
    - 检测人体 17 个关键点（COCO pose）
    - 计算躯干垂直度（shoulder-hip 中心连线 vs 垂直轴）
    - 计算身体纵横比（bounding box w/h）
    - 双重判定：纵横比 < 0.7 + 躯干倾角 > 60° → 跌倒

    模型：yolov8n-pose.pt（~6MB）
    """

    # COCO 17 keypoints
    KEYPOINT_NAMES = [
        "nose", "left_eye", "right_eye", "left_ear", "right_ear",
        "left_shoulder", "right_shoulder", "left_elbow", "right_elbow",
        "left_wrist", "right_wrist", "left_hip", "right_hip",
        "left_knee", "right_knee", "left_ankle", "right_ankle",
    ]
    SHOULDER_IDS = [5, 6]
    HIP_IDS = [11, 12]

    def __init__(
        self,
        model_path: str = "yolov8n-pose.pt",
        device: str = "cpu",
        conf_threshold: float = 0.5,
        fall_aspect_threshold: float = 0.7,
        fall_angle_threshold: float = 60.0,
    ):
        self.model_path = model_path
        self.device = device
        self.conf_threshold = conf_threshold
        self.fall_aspect_threshold = fall_aspect_threshold
        self.fall_angle_threshold = fall_angle_threshold
        self._model = None
        self._load_error: str | None = None

    def _ensure_loaded(self) -> bool:
        if self._model is not None:
            return True
        if self._load_error:
            return False
        try:
            from ultralytics import YOLO

            logger.info(f"加载 YOLO-pose 模型: {self.model_path}")
            self._model = YOLO(self.model_path)
            if self.device:
                self._model.to(self.device)
            return True
        except Exception as e:
            self._load_error = f"YOLO-pose 加载失败: {e}"
            logger.error(self._load_error)
            return False

    @property
    def name(self) -> str:
        return f"pose_detector_v0.3_yolov8n_pose_{self.device}"

    def detect(self, frame: np.ndarray | None) -> list[Detection]:
        if frame is None or not self._ensure_loaded():
            return []

        try:
            results = self._model(frame, conf=self.conf_threshold, verbose=False)
        except Exception as e:
            logger.error(f"YOLO-pose 推理失败: {e}")
            return []

        detections: list[Detection] = []
        h, w = frame.shape[:2]

        for r in results:
            if r.keypoints is None:
                continue
            boxes = r.boxes
            kpts_data = r.keypoints.data  # shape: (N, 17, 3) - x, y, conf

            for i, (box, kpts) in enumerate(zip(boxes, kpts_data)):
                conf = float(box.conf[0])
                xyxy = box.xyxy[0].cpu().numpy()
                x1, y1, x2, y2 = xyxy
                bbox = (x1 / w, y1 / h, (x2 - x1) / w, (y2 - y1) / h)
                aspect = (y2 - y1) / max(x2 - x1, 1)

                # 提取关键点（CPU tensor → numpy）
                kpts_np = kpts.cpu().numpy()  # (17, 3)
                fall_score = self._is_fall(kpts_np, aspect, h, w)

                attrs = {
                    "class_id": 0,
                    "model": "yolov8n-pose",
                    "aspect_ratio": round(aspect, 3),
                    "fall_score": round(fall_score, 3),
                    "keypoints": {name: (round(x, 1), round(y, 1), round(c, 2))
                                  for name, (x, y, c) in zip(self.KEYPOINT_NAMES, kpts_np)},
                }

                if fall_score > 0.7:
                    detections.append(
                        Detection(
                            kind="fall_detected",
                            confidence=conf * fall_score,
                            bbox=tuple(bbox),  # type: ignore
                            attributes=attrs,
                        )
                    )
                else:
                    detections.append(
                        Detection(
                            kind="person_pose",
                            confidence=conf,
                            bbox=tuple(bbox),  # type: ignore
                            attributes=attrs,
                        )
                    )

        return detections

    def _is_fall(self, kpts: np.ndarray, aspect: float, h: int, w: int) -> float:
        """计算跌倒分数 [0.0-1.0]"""
        scores = []

        # 1. 纵横比评分（身体横躺 → 跌倒）
        if aspect < self.fall_aspect_threshold:
            scores.append(min(1.0, (self.fall_aspect_threshold - aspect) / 0.3))
        else:
            scores.append(0.0)

        # 2. 躯干倾角评分
        try:
            # 肩膀中心 + 髋部中心 → 躯干向量
            shoulders = kpts[self.SHOULDER_IDS, :2]  # (2, 2)
            hips = kpts[self.HIP_IDS, :2]  # (2, 2)

            # 平均可见关键点
            shoulder_visible = np.mean(kpts[self.SHOULDER_IDS, 2] > 0.3)
            hip_visible = np.mean(kpts[self.HIP_IDS, 2] > 0.3)

            if shoulder_visible > 0.5 and hip_visible > 0.5:
                shoulder_center = np.mean(shoulders, axis=0)
                hip_center = np.mean(hips, axis=0)
                trunk_vector = shoulder_center - hip_center
                # 与垂直轴的夹角（垂直向下为 (0, 1)）
                vertical = np.array([0.0, 1.0])
                cos_angle = np.dot(trunk_vector, vertical) / (
                    np.linalg.norm(trunk_vector) + 1e-6
                )
                angle = np.degrees(np.arccos(np.clip(cos_angle, -1, 1)))
                if angle > self.fall_angle_threshold:
                    scores.append(min(1.0, (angle - self.fall_angle_threshold) / 30.0))
                else:
                    scores.append(0.0)
            else:
                scores.append(0.5)  # 不可见时给中等分
        except Exception:
            scores.append(0.0)

        return float(np.mean(scores))


# ============================================================
# FireDetector：火焰/烟雾视觉复核
# ============================================================


class FireDetector(LocalDetector):
    """v0.3 火焰/烟雾视觉复核

    方法：基于 HSV 颜色空间 + YOLO-cls 分类（可选）
    - v0.3.1: 纯 HSV 阈值（无 ML 依赖）
    - v0.3.2: YOLO-cls 分类（更高精度）

    用于配合 §3.19 smoke_visual_verify 规则，降低烟雾传感器误报。
    """

    def __init__(
        self,
        model_path: str | None = None,  # None = 纯 HSV
        conf_threshold: float = 0.6,
    ):
        self.model_path = model_path
        self.conf_threshold = conf_threshold
        self._model = None

        # HSV 火焰阈值（经验值）
        self.fire_hsv_lower = np.array([0, 100, 200])     # 红色-橙色
        self.fire_hsv_upper = np.array([25, 255, 255])
        self.smoke_hsv_lower = np.array([0, 0, 100])      # 灰色
        self.smoke_hsv_upper = np.array([180, 50, 200])

    @property
    def name(self) -> str:
        if self.model_path:
            return f"fire_detector_v0.3_yolov8n_cls"
        return "fire_detector_v0.3_hsv"

    def detect(self, frame: np.ndarray | None) -> list[Detection]:
        if frame is None:
            return []

        try:
            import cv2

            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

            # 火焰掩码
            fire_mask = cv2.inRange(hsv, self.fire_hsv_lower, self.fire_hsv_upper)
            fire_ratio = np.sum(fire_mask > 0) / fire_mask.size

            # 烟雾掩码
            smoke_mask = cv2.inRange(hsv, self.smoke_hsv_lower, self.smoke_hsv_upper)
            smoke_ratio = np.sum(smoke_mask > 0) / smoke_mask.size

            detections: list[Detection] = []

            # 火焰判定（>5% 像素）
            if fire_ratio > 0.05:
                # 找最大连通区域
                contours, _ = cv2.findContours(
                    fire_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
                )
                if contours:
                    largest = max(contours, key=cv2.contourArea)
                    x, y, w, h = cv2.boundingRect(largest)
                    fh, fw = frame.shape[:2]
                    conf = min(0.95, 0.5 + fire_ratio)
                    if conf >= self.conf_threshold:
                        detections.append(
                            Detection(
                                kind="fire_detected",
                                confidence=conf,
                                bbox=(x / fw, y / fh, w / fw, h / fh),
                                attributes={
                                    "fire_ratio": round(fire_ratio, 4),
                                    "model": "hsv",
                                },
                            )
                        )

            # 烟雾判定（>15% 像素）
            if smoke_ratio > 0.15:
                conf = min(0.9, 0.5 + smoke_ratio / 2)
                if conf >= self.conf_threshold:
                    detections.append(
                        Detection(
                            kind="smoke_detected",
                            confidence=conf,
                            bbox=(0.0, 0.0, 1.0, 1.0),  # 烟雾通常占满
                            attributes={
                                "smoke_ratio": round(smoke_ratio, 4),
                                "model": "hsv",
                            },
                        )
                    )

            return detections
        except ImportError:
            logger.error("缺少 opencv-python，无法做火焰检测")
            return []


# ============================================================
# MotionDetector：OpenCV 背景减除
# ============================================================


class MotionDetector(LocalDetector):
    """v0.3 简单运动检测（MOG2 背景减除）

    用法：构造时传 background_frame，第一帧
    """

    def __init__(self, conf_threshold: float = 0.3, min_area_ratio: float = 0.02):
        self.conf_threshold = conf_threshold
        self.min_area_ratio = min_area_ratio
        self._bg_subtractor = None

    @property
    def name(self) -> str:
        return "motion_detector_v0.3_mog2"

    def _ensure_subtractor(self):
        if self._bg_subtractor is None:
            try:
                import cv2
                self._bg_subtractor = cv2.createBackgroundSubtractorMOG2(
                    history=200, varThreshold=32, detectShadows=False
                )
            except ImportError:
                logger.error("缺少 opencv-python")
        return self._bg_subtractor

    def detect(self, frame: np.ndarray | None) -> list[Detection]:
        if frame is None:
            return []
        sub = self._ensure_subtractor()
        if sub is None:
            return []

        try:
            import cv2

            fg_mask = sub.apply(frame)
            motion_ratio = np.sum(fg_mask > 0) / fg_mask.size
            if motion_ratio < self.min_area_ratio:
                return []

            contours, _ = cv2.findContours(
                fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )
            detections: list[Detection] = []
            fh, fw = frame.shape[:2]
            for c in contours:
                area = cv2.contourArea(c)
                if area < self.min_area_ratio * fh * fw:
                    continue
                x, y, w, h = cv2.boundingRect(c)
                conf = min(0.95, 0.4 + motion_ratio)
                if conf >= self.conf_threshold:
                    detections.append(
                        Detection(
                            kind="motion",
                            confidence=conf,
                            bbox=(x / fw, y / fh, w / fw, h / fh),
                            attributes={"area": int(area), "motion_ratio": round(motion_ratio, 4)},
                        )
                    )
            return detections
        except Exception as e:
            logger.error(f"MotionDetector 失败: {e}")
            return []
