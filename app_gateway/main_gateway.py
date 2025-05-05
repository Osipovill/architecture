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
    TOKEN_EXPIRE_MINUTES: int = int(os.getenv('TOKEN_EXPIRE_MINUTES', 60))

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
security = HTTPBearer()
app = FastAPI(title="API Gateway")

db_users = {
    "admin": "admin",
    "app_1": "app_1"
}

class UserIn(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class VerifyResponse(BaseModel):
    valid: bool
    username: str

# JWT utilities
def create_jwt_token(username: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": username, "exp": expire}
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm="HS256")

# Dependency to verify JWT
def verify_jwt(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    try:
        payload = jwt.decode(credentials.credentials, settings.JWT_SECRET, algorithms=["HS256"])
        return payload
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")

# User management endpoints
@app.post("/api/users", status_code=status.HTTP_201_CREATED)
async def create_user(user: UserIn):
    if user.username in db_users:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already exists")
    db_users[user.username] = user.password
    return {"msg": "User created successfully", "username": user.username}

@app.post("/api/token", response_model=TokenResponse)
async def login_for_token(user: UserIn):
    # Authenticate user
    pwd = db_users.get(user.username)
    if not pwd or pwd != user.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )
    token = create_jwt_token(user.username)
    return {"access_token": token}

# Verify token endpoint
@app.get("/api/verify", response_model=VerifyResponse)
async def verify_token(user=Depends(verify_jwt)):
    return {"valid": True, "username": user.get("sub")}

# Proxy endpoint
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
        port=8000,
        workers=1
    )
