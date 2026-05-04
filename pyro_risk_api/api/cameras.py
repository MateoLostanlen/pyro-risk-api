from datetime import datetime

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

router = APIRouter(tags=["cameras"])


class Camera(BaseModel):
    id: int
    name: str
    organization_id: int
    lat: float
    lon: float
    fwi: float | None = None
    fwi_class: str | None = None
    last_refresh_at: datetime | None = None


@router.get("/cameras", response_model=list[Camera])
def list_cameras(request: Request) -> list[Camera]:
    cameras = request.app.state.cameras
    if cameras is None:
        raise HTTPException(status_code=503, detail="cameras not loaded")
    return [Camera(**cam) for cam in cameras]


@router.get("/cameras/{camera_id}", response_model=Camera)
def get_camera(camera_id: int, request: Request) -> Camera:
    cameras = request.app.state.cameras
    if cameras is None:
        raise HTTPException(status_code=503, detail="cameras not loaded")
    for cam in cameras:
        if cam["id"] == camera_id:
            return Camera(**cam)
    raise HTTPException(status_code=404, detail=f"camera {camera_id} not found")
