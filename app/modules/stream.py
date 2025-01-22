import cv2
import time
import threading
from queue import Queue
from typing import Optional

class StreamHandler:
    def __init__(self, rtsp_url: str, frame_queue: Queue, 
                 stop_event: threading.Event, sampling_ratio: int = 5):
        self.rtsp_url = rtsp_url
        self.frame_queue = frame_queue
        self.stop_event = stop_event
        self.sampling_ratio = sampling_ratio
        self.cap: Optional[cv2.VideoCapture] = None
        self.latest_frame = None

    def start(self):
        """Main stream handling loop"""
        self.cap = cv2.VideoCapture(self.rtsp_url)
        frame_count = 0
        
        while not self.stop_event.is_set():
            ret, frame = self.cap.read()
            if not ret:
                time.sleep(0.1)
                continue

            frame_count += 1
            self.latest_frame = frame
            
            if frame_count % self.sampling_ratio == 0:
                if not self.frame_queue.full():
                    self.frame_queue.put(frame.copy())
                else:
                    try:
                        self.frame_queue.get_nowait()
                    except:
                        pass
            
            time.sleep(0.001)  # Prevent CPU overloading

        self.cap.release()

    def get_latest_frame(self):
        """Get most recent frame without queuing"""
        return self.latest_frame
