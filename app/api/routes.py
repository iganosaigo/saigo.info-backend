from app.api.endpoints import auth, post, user
from fastapi import APIRouter


api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(user.router, prefix="/user", tags=["users"])
api_router.include_router(post.router, prefix="/post", tags=["posts"])
