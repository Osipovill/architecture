from __future__ import annotations

import json
import os
from datetime import datetime, timedelta
from typing import Optional

import httpx
import jwt
import uvicorn
from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    Path,
    Query,
    status,
)
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from pydantic_settings import BaseSettings

# ───────────────────── settings ─────────────────────
class Settings(BaseSettings):
    JWT_SECRET: str
    TOKEN_EXPIRE_MINUTES: int

    # downstream-service URLs
    APP1_URL: str
    APP2_URL: str
    APP3_URL: str            # ← NEW

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
api_users = json.loads(os.getenv("API_USERS", "{}"))

security = HTTPBearer()
app = FastAPI(title="API Gateway")

# ──────────────────── models ────────────────────────
class UserIn(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class VerifyResponse(BaseModel):
    valid: bool
    username: str


# ──────────────────── helpers ───────────────────────
def create_jwt_token(username: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": username, "exp": expire}
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm="HS256")


def verify_jwt(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    try:
        return jwt.decode(credentials.credentials, settings.JWT_SECRET, algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )


# ──────────────────── token endpoints ──────────────
@app.post("/api/token", response_model=TokenResponse)
async def login_for_token(user: UserIn):
    if api_users.get(user.username) != user.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"access_token": create_jwt_token(user.username)}


@app.get("/api/verify", response_model=VerifyResponse)
async def verify_token(user=Depends(verify_jwt)):
    return {"valid": True, "username": user.get("sub")}


# ──────────────────── proxy: App-1 ──────────────────
@app.get("/api/report")
async def proxy_report(
    term: str = Query("введение"),
    start: str = Query("2023-09-01"),
    end: str = Query("2023-10-16"),
    # credentials: HTTPAuthorizationCredentials = Depends(security),
    # user=Depends(verify_jwt)
):
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(
                f"{settings.APP1_URL}/report",
                params={"term": term, "start": start, "end": end},
                # headers={"Authorization": f"Bearer {credentials.credentials}"}
            )
        except httpx.RequestError as e:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))

    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()


# ──────────────────── proxy: App-2 ──────────────────
@app.get("/api/course-attendance/{course_title}")
async def proxy_course_attendance(
    course_title: str,
    year: Optional[int] = Query(None, description="Academic year"),
    semester: Optional[int] = Query(None, ge=1, le=2, description="Semester (1 or 2)"),
    requirements: Optional[str] = Query(None),
    # credentials: HTTPAuthorizationCredentials = Depends(security),
    # user=Depends(verify_jwt)
):
    params = {k: v for k, v in {"year": year, "semester": semester, "requirements": requirements}.items() if v is not None}

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(
                f"{settings.APP2_URL}/api/course-attendance/{course_title}",
                params=params,
                # headers={"Authorization": f"Bearer {credentials.credentials}"}
            )
        except httpx.RequestError as e:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))

    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()


# ──────────────────── proxy: App-3 (NEW) ────────────
@app.get("/api/group-hours/{group_id}")               # ← NEW
async def proxy_group_hours(
    group_id: int = Path(..., ge=1, description="ID группы"),
    # credentials: HTTPAuthorizationCredentials = Depends(security),
    # user=Depends(verify_jwt)
):
    """
    Проксирует запрос к Lab-3 Service (app_3) — отчёт по часам лекций.
    """
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(
                f"{settings.APP3_URL}/api/group-hours/{group_id}",
                # headers={"Authorization": f"Bearer {credentials.credentials}"}
            )
        except httpx.RequestError as e:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))

    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()


# ──────────────────── main ──────────────────────────
if __name__ == "__main__":
    uvicorn.run(
        "app_gateway.main_gateway:app",
        host="127.0.0.1",
        port=80,
        workers=1,
    )
