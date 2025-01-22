import cv2
import json
import redis
import threading
import os
import time
from queue import Queue
from typing import Dict, Any
from datetime import datetime
from utils.config_loader import load_config
from modules.detection import DetectionPipeline
from modules.stream import StreamHandler
from modules.redis_client import RedisClient

def main():
    # Load configuration
    config = load_config("config/config.json")
    
    # Initialize Redis connection
    redis_client = RedisClient(
        host="redis-server",
        password=config.get("redis_password", "your_secure_password")
    )
    
    # Create frame queue and event flags
    frame_queue = Queue(maxsize=10)
    stop_event = threading.Event()
    
    # Initialize detection pipeline
    detection_pipe = DetectionPipeline(
        config=config,
        frame_queue=frame_queue,
        redis_client=redis_client,
        stop_event=stop_event
    )
    
    # Initialize stream handler
    stream_handler = StreamHandler(
        rtsp_url=os.getenv("RTSP_URL"),
        frame_queue=frame_queue,
        stop_event=stop_event,
        sampling_ratio=config["frame_sampling_ratio"]
    )
    
    # Start threads
    stream_thread = threading.Thread(target=stream_handler.start)
    detection_thread = threading.Thread(target=detection_pipe.start)
    
    stream_thread.start()
    detection_thread.start()
    
    # Wait for termination
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        stop_event.set()
        stream_thread.join()
        detection_thread.join()

if __name__ == "__main__":
    main()
