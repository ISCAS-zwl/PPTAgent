from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.websocket_manager import manager
import json

router = APIRouter(tags=["websocket"])


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket 连接端点"""
    await manager.connect(websocket)
    try:
        while True:
            # 接收客户端消息
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                message_type = message.get("type")

                # 处理订阅请求
                if message_type == "subscribe":
                    task_id = message.get("task_id")
                    if task_id:
                        await manager.subscribe_task(websocket, task_id)
                        await websocket.send_json({
                            "type": "subscribed",
                            "task_id": task_id,
                        })

                # 处理取消订阅请求
                elif message_type == "unsubscribe":
                    task_id = message.get("task_id")
                    if task_id:
                        await manager.unsubscribe_task(websocket, task_id)
                        await websocket.send_json({
                            "type": "unsubscribed",
                            "task_id": task_id,
                        })

            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON",
                })

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)
