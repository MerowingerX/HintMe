import os
import json
import redis

REDIS_URL    = os.getenv("REDIS_URL", "redis://localhost:6379")
WINDOW_SIZE  = int(os.getenv("CONTEXT_WINDOW", "10"))

r = redis.from_url(REDIS_URL, decode_responses=True)


class ContextStore:
    def get(self, chat_id: str) -> list:
        raw = r.get(f"ctx:{chat_id}")
        return json.loads(raw) if raw else []

    def add(self, chat_id: str, message: dict):
        history = self.get(chat_id)
        history.append(message)
        history = history[-WINDOW_SIZE:]
        r.set(f"ctx:{chat_id}", json.dumps(history), ex=86400)

    def clear(self, chat_id: str):
        r.delete(f"ctx:{chat_id}")
