import cv2
import time
import threading
import numpy as np
from ultralytics import YOLO
from queue import Queue
from typing import Dict, Any
from .redis_client import RedisClient

class DetectionPipeline:
    def __init__(self, config: Dict[str, Any], frame_queue: Queue,
                 redis_client: RedisClient, stop_event: threading.Event):
        self.config = config
        self.frame_queue = frame_queue
        self.redis = redis_client
        self.stop_event = stop_event
        self.models = self._load_models()
        self.output_queue = Queue()

    def _load_models(self):
        """Load YOLO models based on configuration"""
        return {
            'object': YOLO('yolov8n.pt'),
            'pose': YOLO('yolov8n-pose.pt'),
            'world': YOLO('yolov8s-world.pt')
        }

    def start(self):
        """Main detection processing loop"""
        while not self.stop_event.is_set():
            if not self.frame_queue.empty():
                frame = self.frame_queue.get()
                processed_frame = self.process_frame(frame)
                self.output_queue.put(processed_frame)
            time.sleep(0.001)

    def process_frame(self, frame: np.ndarray) -> np.ndarray:
        """Run all detection types on a frame"""
        # Object detection
        if 'object_detection' in self.config:
            results = self.models['object'](
                frame,
                classes=list(self.config['object_detection']['classes'].keys()),
                conf=min(self.config['object_detection']['classes'].values())
            )
            for result in results:
                self._process_object_results(result)
                frame = self._draw_boxes(frame, result)

        # Pose estimation
        if 'pose_estimation' in self.config:
            results = self.models['pose'](
                frame,
                conf=self.config['pose_estimation']['confidence']
            )
            for result in results:
                self._process_pose_results(result)
                frame = self._draw_keypoints(frame, result)

        # YOLO World detection
        if 'yolo_world' in self.config:
            self.models['world'].set_classes(self.config['yolo_world']['target_texts'])
            results = self.models['world'](
                frame,
                conf=self.config['yolo_world']['confidence']
            )
            for result in results:
                self._process_world_results(result)
                frame = self._draw_boxes(frame, result)

        return frame

    def _process_object_results(self, result):
        """Process and store object detection results"""
        for box in result.boxes:
            class_id = int(box.cls)
            class_name = result.names[class_id]
            confidence = float(box.conf)
            if confidence >= self.config['object_detection']['classes'].get(class_name, 0):
                detection_data = {
                    'type': 'object',
                    'class': class_name,
                    'confidence': confidence,
                    'bbox': box.xywh[0].tolist(),
                    'timestamp': time.time()
                }
                self.redis.store_detection('object', detection_data)

    def _process_pose_results(self, result):
        """Process and store pose estimation results"""
        for box in result.boxes:
            if box.keypoints is not None:
                keypoints = box.keypoints.xy.cpu().numpy().tolist()
                confidences = box.keypoints.conf.cpu().numpy().tolist()
                detection_data = {
                    'type': 'pose',
                    'confidence': float(box.conf),
                    'keypoints': keypoints,
                    'keypoint_confidences': confidences,
                    'timestamp': time.time()
                }
                self.redis.store_detection('pose', detection_data)

    def _process_world_results(self, result):
        """Process and store YOLO World results"""
        for box in result.boxes:
            class_id = int(box.cls)
            class_name = result.names[class_id]
            confidence = float(box.conf)
            detection_data = {
                'type': 'world',
                'class': class_name,
                'confidence': confidence,
                'bbox': box.xywh[0].tolist(),
                'timestamp': time.time()
            }
            self.redis.store_detection('world', detection_data)

    def _draw_boxes(self, frame: np.ndarray, result) -> np.ndarray:
        """Draw bounding boxes and labels on frame"""
        for box in result.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            confidence = float(box.conf)
            class_id = int(box.cls)
            label = f"{result.names[class_id]} {confidence:.2f}"

            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, label, (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        return frame

    def _draw_keypoints(self, frame: np.ndarray, result) -> np.ndarray:
        """Draw pose keypoints and skeleton on frame"""
        for box in result.boxes:
            if box.keypoints is not None:
                keypoints = box.keypoints.xy.cpu().numpy()
                for kp in keypoints[0]:
                    x, y = map(int, kp)
                    cv2.circle(frame, (x, y), 3, (0, 0, 255), -1)
        return frame
