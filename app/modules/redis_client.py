import redis
import json
from typing import Optional, Dict, Any
from datetime import datetime

class RedisClient:
    def __init__(self, host: str = 'redis-server', port: int = 6379, 
                 password: Optional[str] = None, db: int = 0):
        self.client = redis.Redis(
            host=host,
            port=port,
            password=password,
            db=db,
            decode_responses=True
        )

    def store_detection(self, detection_type: str, data: Dict[str, Any]):
        """Store detection data in Redis stream"""
        stream_data = {
            "type": detection_type,
            "data": json.dumps(data),
            "timestamp": datetime.now().isoformat()
        }
        self.client.xadd("detections", stream_data)

    def get_last_detections(self, count: int = 10) -> list:
        """Retrieve last N detections from Redis stream"""
        return self.client.xrevrange("detections", count=count)

    def ping(self) -> bool:
        """Check Redis connection"""
        return self.client.ping()
