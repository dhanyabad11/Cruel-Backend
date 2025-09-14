from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def get_deadlines():
    return {"message": "Get deadlines endpoint - coming soon"}

@router.post("/")
async def create_deadline():
    return {"message": "Create deadline endpoint - coming soon"}

@router.put("/{deadline_id}")
async def update_deadline(deadline_id: int):
    return {"message": f"Update deadline {deadline_id} endpoint - coming soon"}

@router.delete("/{deadline_id}")
async def delete_deadline(deadline_id: int):
    return {"message": f"Delete deadline {deadline_id} endpoint - coming soon"}