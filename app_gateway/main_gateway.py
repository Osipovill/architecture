import json
import os

import uvicorn
from datetime import datetime, timedelta

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from pydantic_settings import BaseSettings

import jwt
import httpx

# Settings
class Settings(BaseSettings):
    JWT_SECRET: str = os.getenv('JWT_SECRET', 'super_s3cr3t_key')
    APP1_URL: str = os.getenv('APP1_URL', 'http://127.0.0.1:8001')
    TOKEN_EXPIRE_MINUTES: int = int(os.getenv('TOKEN_EXPIRE_MINUTES') or 60)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

api_users = json.loads(os.getenv('API_USERS'))

settings = Settings()
security = HTTPBearer()
app = FastAPI(title="API Gateway")


class UserIn(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class VerifyResponse(BaseModel):
    valid: bool
    username: str

def create_jwt_token(username: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": username, "exp": expire}
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm="HS256")

def verify_jwt(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    try:
        payload = jwt.decode(credentials.credentials, settings.JWT_SECRET, algorithms=["HS256"])
        return payload
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")


# ---TOKENS ENDPOINTS---
@app.post("/api/token", response_model=TokenResponse)
async def login_for_token(user: UserIn):
    pwd = api_users.get(user.username)
    if not pwd or pwd != user.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )
    token = create_jwt_token(user.username)
    return {"access_token": token}


@app.get("/api/verify", response_model=VerifyResponse)
async def verify_token(user=Depends(verify_jwt)):
    return {"valid": True, "username": user.get("sub")}


# ---PROXY ENDPOINTS---
@app.get("/api/report")
async def proxy_report(
    term: str,
    start: str,
    end: str,
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


if __name__ == "__main__":
    uvicorn.run(
        "app_gateway.main_gateway:app",
        host="127.0.0.1",
        port=80,
        workers=1
    )
