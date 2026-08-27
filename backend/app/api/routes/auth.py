from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.dependencies import client_ip, get_auth_service, get_current_user
from app.db import get_db
from app.schemas import (
    LoginRequest,
    MessageResponse,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.services.auth_service import AuthError, AuthService
from fastapi import HTTPException, status

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=201)
def register(
    body: RegisterRequest,
    request: Request,
    auth: AuthService = Depends(get_auth_service),
    db: Session = Depends(get_db),
):
    try:
        user = auth.register(body.email, body.password, ip=client_ip(request))
        db.commit()
        db.refresh(user)
        return user
    except AuthError as exc:
        db.rollback()
        raise HTTPException(status.HTTP_400_BAD_REQUEST, exc.message)


@router.post("/login", response_model=TokenResponse)
def login(
    body: LoginRequest,
    request: Request,
    auth: AuthService = Depends(get_auth_service),
    db: Session = Depends(get_db),
):
    try:
        _user, access, refresh = auth.login(body.email, body.password, ip=client_ip(request))
        db.commit()
        return TokenResponse(access_token=access, refresh_token=refresh)
    except AuthError:
        db.rollback()
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")


@router.post("/refresh", response_model=TokenResponse)
def refresh(
    body: RefreshRequest,
    request: Request,
    auth: AuthService = Depends(get_auth_service),
    db: Session = Depends(get_db),
):
    try:
        access, refresh_tok = auth.refresh(body.refresh_token, ip=client_ip(request))
        db.commit()
        return TokenResponse(access_token=access, refresh_token=refresh_tok)
    except AuthError:
        db.rollback()
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")


@router.post("/logout", response_model=MessageResponse)
def logout(
    body: RefreshRequest,
    request: Request,
    auth: AuthService = Depends(get_auth_service),
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    auth.logout(body.refresh_token, user.id, ip=client_ip(request))
    db.commit()
    return MessageResponse(message="Logged out")


@router.get("/me", response_model=UserResponse)
def me(user=Depends(get_current_user)):
    return user
