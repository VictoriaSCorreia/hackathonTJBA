from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.schemas.user import UserCreate, UserRead
from app.services.user_service import UserService
from app.api.deps import get_db

router = APIRouter(prefix='/users')

@router.post('/', response_model=UserRead, status_code=201)
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    service = UserService(db)
    return service.create_user(payload)

@router.get('/{user_id}', response_model=UserRead)
def get_user(user_id: int, db: Session = Depends(get_db)):
    service = UserService(db)
    user = service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail='User not found')
    return user
