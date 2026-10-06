from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field

from app.product.auth import auth_service
from app.product.billing import billing_service


router = APIRouter()


class Credentials(BaseModel):
    email: str = Field(min_length=5, max_length=254)
    password: str = Field(min_length=10, max_length=200)


class Registration(Credentials):
    display_name: str = Field(min_length=2, max_length=80)


def bearer_token(authorization: str = Header(default="")) -> str:
    scheme, _, token = authorization.partition(" ")
    if scheme.casefold() != "bearer" or not token:
        raise HTTPException(status_code=401, detail="Sign in is required.")
    return token


def current_user(token: str = Depends(bearer_token)) -> dict[str, object]:
    try:
        return auth_service.authenticate(token)
    except PermissionError as error:
        raise HTTPException(status_code=401, detail=str(error)) from error


@router.post("/auth/register")
def register(request: Registration) -> dict[str, str]:
    try:
        return auth_service.register(request.email, request.password, request.display_name)
    except PermissionError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.post("/auth/login")
def login(request: Credentials) -> dict[str, str]:
    try:
        return auth_service.login(request.email, request.password)
    except PermissionError as error:
        raise HTTPException(status_code=401, detail=str(error)) from error


@router.post("/auth/logout")
def logout(token: str = Depends(bearer_token)) -> dict[str, bool]:
    auth_service.logout(token)
    return {"logged_out": True}


@router.get("/account/me")
def account(user: dict[str, object] = Depends(current_user)) -> dict[str, object]:
    return {"user": user, "billing": billing_service.account(str(user["id"]))}
