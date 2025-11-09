from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import User as UserModel
from schemas import User, UserUpdate
from routers.auth import get_current_user

router = APIRouter()

@router.get("/me", response_model=User)
async def read_user_me(current_user: UserModel = Depends(get_current_user)):
    return current_user

@router.put("/me", response_model=User)
async def update_user_me(
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    # Update user fields
    if user_update.name is not None:
        current_user.name = user_update.name
    if user_update.phone_number is not None:
        current_user.phone_number = user_update.phone_number
    if user_update.birth_date is not None:
        current_user.birth_date = user_update.birth_date
    
    db.commit()
    db.refresh(current_user)
    return current_user
