from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
import subprocess
from loguru import logger

router = APIRouter()

class NotificationRequest(BaseModel):
    title: str
    message: str

@router.post("/notify")
async def send_notification(request: NotificationRequest):
    """
    发送系统桌面通知 (macOS)
    """
    try:
        # Escape quotes to prevent command injection/errors
        title = request.title.replace('"', '\\"')
        message = request.message.replace('"', '\\"')
        
        # macOS osascript command
        script = f'display notification "{message}" with title "{title}" sound name "Ping"'
        
        subprocess.run(['osascript', '-e', script], check=True)
        return {"status": "success", "message": "Notification sent"}
    except Exception as e:
        logger.error(f"Failed to send notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))
