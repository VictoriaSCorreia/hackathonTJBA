from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.schemas.user import UserRead
from app.services.user_service import UserService
from app.api.deps import get_db, get_current_guest

router = APIRouter()

@router.post('/sessions', response_model=UserRead, status_code=201)
def create_guest_session(db: Session = Depends(get_db)):
    service = UserService(db)
    return service.create_guest()

@router.get('/me', response_model=UserRead)
def read_me(current_user = Depends(get_current_guest)):
    return current_user
