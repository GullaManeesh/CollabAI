from fastapi import APIRouter, Depends, HTTPException, status
from pymongo.errors import DuplicateKeyError
from bson import ObjectId
import random
from datetime import datetime

from backend.models.auth import UserRegister, UserLogin, UserResponse, TokenResponse
from backend.auth import get_password_hash, verify_password, create_access_token
from backend.dependencies import get_current_user
import backend.database as db

router = APIRouter(prefix="/auth", tags=["auth"])

AVATAR_COLORS = [
    "#4F8DF5", # signal blue
    "#9B7BF0", # agent purple
    "#E0A458", # warn gold
    "#4FB07A", # ok green
    "#EC5E5E", # coral
    "#F554A4", # pink
    "#10B981", # emerald
    "#F59E0B"  # amber
]

def get_avatar_color_for_email(email: str) -> str:
    # Deterministic color choice based on email hash
    idx = abs(hash(email)) % len(AVATAR_COLORS)
    return AVATAR_COLORS[idx]

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserRegister):
    email_clean = user_in.email.lower().strip()
    
    # Check if user exists
    existing = await db.users_col.find_one({"email": email_clean})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )
        
    password_hash = get_password_hash(user_in.password)
    avatar_color = get_avatar_color_for_email(email_clean)
    
    user_doc = {
        "name": user_in.name.strip(),
        "email": email_clean,
        "password_hash": password_hash,
        "avatar_color": avatar_color,
        "created_at": datetime.utcnow()
    }
    
    try:
        result = await db.users_col.insert_one(user_doc)
        user_id = str(result.inserted_id)
    except DuplicateKeyError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )
        
    token = create_access_token(data={"sub": user_id})
    
    return TokenResponse(
        token=token,
        user=UserResponse(
            id=user_id,
            name=user_doc["name"],
            email=user_doc["email"],
            avatar_color=user_doc["avatar_color"]
        )
    )

@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    email_clean = credentials.email.lower().strip()
    
    user = await db.users_col.find_one({"email": email_clean})
    if not user or not verify_password(credentials.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
        
    user_id = str(user["_id"])
    token = create_access_token(data={"sub": user_id})
    
    return TokenResponse(
        token=token,
        user=UserResponse(
            id=user_id,
            name=user["name"],
            email=user["email"],
            avatar_color=user["avatar_color"]
        )
    )

@router.get("/me", response_model=UserResponse)
async def me(current_user: dict = Depends(get_current_user)):
    return UserResponse(
        id=current_user["id"],
        name=current_user["name"],
        email=current_user["email"],
        avatar_color=current_user["avatar_color"]
    )
