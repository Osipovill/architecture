import os
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
import httpx
from pydantic import BaseSettings

# ----------------- CONFIGURATION -----------------
class Settings(BaseSettings):
    # Секрет для подписи JWT, задаётся через переменные окружения
    JWT_SECRET: str = os.getenv("JWT_SECRET", "your_jwt_secret")
    # Внутренний адрес сервиса ЛР1 в Docker-сети
    APP1_URL: str = os.getenv("APP1_URL", "http://app_1:8000")

settings = Settings()
security = HTTPBearer()
app = FastAPI(title="API Gateway")

# ----------------- AUTH DEPENDENCY -----------------
def verify_jwt(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        return payload
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )

# ----------------- ROUTES -----------------
@app.get("/api/report")
async def proxy_report(
    term: str,
    start: str,
    end: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    user=Depends(verify_jwt)
):
    """
    Proxy endpoint for Lab #1 report.
    Validates JWT and forwards request to the Lab1 service.
    """
    # Проксируем запрос в сервис ЛР1
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(
                f"{settings.APP1_URL}/report",
                params={"term": term, "start": start, "end": end},
                headers={"Authorization": f"Bearer {credentials.credentials}"}
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Error contacting Lab1 service: {e}"
            )
    if resp.status_code != 200:
        raise HTTPException(
            status_code=resp.status_code,
            detail=resp.text
        )
    return resp.json()