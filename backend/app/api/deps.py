from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login-oauth")

def get_current_user(
    db: Session = Depends(get_db), 
    token: str = Depends(oauth2_scheme)
) -> User:
    """
    Decodes the JWT token and fetches the User from the database.
    Raises credentials exception if the token is invalid or user does not exist.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    subject = decode_access_token(token)
    if subject is None:
        raise credentials_exception
        
    user = db.query(User).filter(User.id == subject).first()
    if user is None:
        # Try checking by email if subject was email
        user = db.query(User).filter(User.email == subject).first()
        if user is None:
            raise credentials_exception
            
    return user
