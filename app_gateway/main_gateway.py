from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl

import jwt
import httpx

class Settings(BaseSettings):
    JWT_SECRET: str
    APP1_URL: AnyHttpUrl

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
security = HTTPBearer()
app = FastAPI(title="API Gateway")

def verify_jwt(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, settings.JWT_SECRET, algorithms=["HS256"])
        return payload
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")

@app.get("/api/report")
async def proxy_report(
    term: str,
    start: str,
    end: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    user=Depends(verify_jwt)
):
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(
                f"{settings.APP1_URL}/report",
                params={"term": term, "start": start, "end": end},
                headers={"Authorization": f"Bearer {credentials.credentials}"}
            )
        except httpx.RequestError as e:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))

    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()
