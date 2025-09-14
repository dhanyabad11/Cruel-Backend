from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def get_portals():
    return {"message": "Get portals endpoint - coming soon"}

@router.post("/")
async def connect_portal():
    return {"message": "Connect portal endpoint - coming soon"}

@router.post("/{portal_id}/sync")
async def sync_portal(portal_id: int):
    return {"message": f"Sync portal {portal_id} endpoint - coming soon"}