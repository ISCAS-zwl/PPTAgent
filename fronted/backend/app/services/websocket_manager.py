import json
from typing import Dict, Set
from fastapi import WebSocket
from app.models.task import WebSocketMessage


class ConnectionManager:
    """WebSocket 连接管理器"""

    def __init__(self):
        # 存储所有活跃的 WebSocket 连接
        self.active_connections: Set[WebSocket] = set()
        # 存储任务订阅关系 task_id -> set of websockets
        self.task_subscriptions: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket):
        """接受新的 WebSocket 连接"""
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        """断开 WebSocket 连接"""
        self.active_connections.discard(websocket)
        # 清理订阅
        for task_id, subscribers in list(self.task_subscriptions.items()):
            subscribers.discard(websocket)
            if not subscribers:
                del self.task_subscriptions[task_id]

    async def subscribe_task(self, websocket: WebSocket, task_id: str):
        """订阅任务更新"""
        if task_id not in self.task_subscriptions:
            self.task_subscriptions[task_id] = set()
        self.task_subscriptions[task_id].add(websocket)

    async def unsubscribe_task(self, websocket: WebSocket, task_id: str):
        """取消订阅任务"""
        if task_id in self.task_subscriptions:
            self.task_subscriptions[task_id].discard(websocket)
            if not self.task_subscriptions[task_id]:
                del self.task_subscriptions[task_id]

    async def send_to_task_subscribers(self, task_id: str, message: WebSocketMessage):
        """向任务的所有订阅者发送消息"""
        if task_id in self.task_subscriptions:
            message_json = message.model_dump_json()
            disconnected = set()
            for websocket in self.task_subscriptions[task_id]:
                try:
                    await websocket.send_text(message_json)
                except Exception as e:
                    print(f"Error sending message to websocket: {e}")
                    disconnected.add(websocket)

            # 清理断开的连接
            for websocket in disconnected:
                self.disconnect(websocket)

    async def broadcast(self, message: WebSocketMessage):
        """广播消息给所有连接"""
        message_json = message.model_dump_json()
        disconnected = set()
        for websocket in self.active_connections:
            try:
                await websocket.send_text(message_json)
            except Exception as e:
                print(f"Error broadcasting to websocket: {e}")
                disconnected.add(websocket)

        # 清理断开的连接
        for websocket in disconnected:
            self.disconnect(websocket)


# 全局连接管理器实例
manager = ConnectionManager()
