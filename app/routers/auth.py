from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
import httpx

from app.config import BACKEND_URL, TEMPLATES_DIR

router = APIRouter(prefix="/auth", tags=["auth"])
templates = Jinja2Templates(directory=TEMPLATES_DIR)


@router.get("/login-page", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html", {"request": request})


@router.post("/login-web")
async def login_web(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{BACKEND_URL}/auth/login",
            json={"username": username, "password": password},
        )

    if resp.status_code != 200:
        return templates.TemplateResponse(
            request,
            "login.html",
            {
                "request": request,
                "error": "Credenciais invalidas",
            },
        )

    token = resp.json()["access_token"]
    response = RedirectResponse(url="/diagnosticos/", status_code=302)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=3600,
    )
    return response


@router.post("/logout")
async def logout():
    response = RedirectResponse(url="/auth/login-page", status_code=302)
    response.delete_cookie(key="access_token")
    return response
