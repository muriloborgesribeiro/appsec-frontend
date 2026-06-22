from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import httpx
from jose import jwt

from app.config import BACKEND_URL, TEMPLATES_DIR, SECRET_KEY, ALGORITHM

router = APIRouter(prefix="/duvidas", tags=["duvidas"])
templates = Jinja2Templates(directory=TEMPLATES_DIR)


def _require_user(request: Request) -> dict:
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Login necessario")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return {"username": payload.get("sub"), "role": payload.get("role")}
    except Exception:
        raise HTTPException(status_code=401, detail="Token invalido")


@router.get("/", response_class=HTMLResponse)
async def pagina_duvidas(
    request: Request,
    user: dict = Depends(_require_user),
):
    return templates.TemplateResponse(
        request,
        "duvidas.html",
        {"request": request, "user": user},
    )


@router.post("/enviar")
async def enviar_pergunta(
    request: Request,
    user: dict = Depends(_require_user),
):
    body = await request.json()
    pergunta = body.get("pergunta", "").strip()
    if not pergunta:
        return JSONResponse(
            status_code=400,
            content={"erro": "A pergunta não pode estar vazia"},
        )

    token = request.cookies.get("access_token")
    headers = {"Authorization": f"Bearer {token}"}

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{BACKEND_URL}/api/v1/duvidas",
            json={"pergunta": pergunta},
            headers=headers,
        )

    if resp.status_code < 200 or resp.status_code >= 300:
        try:
            body_erro = resp.json()
            mensagem = body_erro.get("detail") or body_erro.get("erro") or "Erro ao processar"
        except Exception:
            mensagem = f"Erro {resp.status_code} do servidor"
        return JSONResponse(
            status_code=resp.status_code,
            content={"erro": mensagem},
        )

    data = resp.json()
    return JSONResponse(content={"resposta": data.get("resposta", "")})
