from fastapi import APIRouter

router = APIRouter()

@router.post("/register")
async def register():
    return {"message": "Register endpoint - coming soon"}

@router.post("/login")
async def login():
    return {"message": "Login endpoint - coming soon"}

@router.get("/me")
async def get_current_user():
    return {"message": "Get current user endpoint - coming soon"}