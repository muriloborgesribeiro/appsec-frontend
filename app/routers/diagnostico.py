from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import httpx
from jose import jwt

from app.config import BACKEND_URL, TEMPLATES_DIR, SECRET_KEY, ALGORITHM

router = APIRouter(prefix="/diagnosticos", tags=["diagnostico"])
templates = Jinja2Templates(directory=TEMPLATES_DIR)


def _get_user(request: Request) -> dict | None:
    token = request.cookies.get("access_token")
    if not token:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return {"username": payload.get("sub"), "role": payload.get("role")}
    except Exception:
        return None


def _require_user(request: Request) -> dict:
    user = _get_user(request)
    if not user:
        raise HTTPException(status_code=302, detail="Login necessario")
    return user


def _require_role(*roles: str):
    async def _checker(request: Request):
        user = _require_user(request)
        if user["role"] not in roles:
            raise HTTPException(status_code=403, detail="Permissao insuficiente")
        return user

    return _checker


@router.get("/", response_class=HTMLResponse)
async def formulario(request: Request, user: dict = Depends(_require_user)):
    return templates.TemplateResponse(
        request,
        "index.html",
        {"request": request, "user": user},
    )


@router.post("/avaliar")
async def avaliar(
    request: Request,
    user: dict = Depends(_require_role("admin", "professional")),
):
    form = await request.form()
    dados = {
        "dor_migratoria": form.get("dor_migratoria") == "on",
        "anorexia": form.get("anorexia") == "on",
        "nauseas_vomitos": form.get("nauseas_vomitos") == "on",
        "dor_fid": form.get("dor_fid") == "on",
        "descompressao_dolorosa": form.get("descompressao_dolorosa") == "on",
        "temperatura": float(form.get("temperatura", 36.5)),
        "leucocitos": float(form.get("leucocitos", 8000)),
        "neutrofilia": form.get("neutrofilia") == "on",
    }

    token = request.cookies.get("access_token")
    headers = {"Authorization": f"Bearer {token}"}

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{BACKEND_URL}/api/v1/diagnosticos",
            json=dados,
            headers=headers,
        )

    if resp.status_code != 201:
        return templates.TemplateResponse(
            request,
            "resultado.html",
            {
                "request": request,
                "user": user,
                "erro": f"Erro ao processar: {resp.json().get('detail', 'desconhecido')}",
            },
        )

    resultado = resp.json()

    sintomas_items = [
        ("Dor migratória para FID", dados.get("dor_migratoria", False)),
        ("Anorexia (perda de apetite)", dados.get("anorexia", False)),
        ("Náuseas ou vômitos", dados.get("nauseas_vomitos", False)),
        ("Dor à palpação em FID", dados.get("dor_fid", False)),
    ]
    sinais_items = [
        ("Descompressão dolorosa (Blumberg)", dados.get("descompressao_dolorosa", False)),
        (f"Temperatura: {dados.get('temperatura', 36.5)} °C", True),
        (f"Leucócitos: {dados.get('leucocitos', 8000)} /mm³", True),
        ("Neutrofilia (desvio à esquerda)", dados.get("neutrofilia", False)),
    ]

    return templates.TemplateResponse(
        request,
        "resultado.html",
        {
            "request": request,
            "user": user,
            "alvarado": resultado.get("alvarado", {}),
            "knn": resultado.get("knn", {}),
            "svm": resultado.get("svm", {}),
            "sintomas": sintomas_items,
            "sinais": sinais_items,
        },
    )


@router.get("/historico", response_class=HTMLResponse)
async def historico(
    request: Request,
    user: dict = Depends(_require_role("admin", "professional", "viewer")),
    data_inicio: str = None,
    data_fim: str = None,
    classificacao: str = None,
    resultado_knn: str = None,
    resultado_svm: str = None,
):
    token = request.cookies.get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    params = {}
    if data_inicio:
        params["data_inicio"] = data_inicio
    if data_fim:
        params["data_fim"] = data_fim
    if classificacao:
        params["classificacao"] = classificacao
    if resultado_knn:
        params["resultado_knn"] = resultado_knn
    if resultado_svm:
        params["resultado_svm"] = resultado_svm

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{BACKEND_URL}/api/v1/diagnosticos",
            headers=headers,
            params=params,
        )

    registros = []
    if resp.status_code == 200:
        registros = resp.json().get("items", [])

    return templates.TemplateResponse(
        request,
        "historico.html",
        {
            "request": request,
            "user": user,
            "registros": registros,
            "filtros": {
                "data_inicio": data_inicio,
                "data_fim": data_fim,
                "classificacao": classificacao,
                "resultado_knn": resultado_knn,
                "resultado_svm": resultado_svm,
            },
        },
    )


@router.delete("/{diagnostico_id}")
async def remover(
    request: Request,
    diagnostico_id: int,
    user: dict = Depends(_require_role("admin", "professional")),
):
    token = request.cookies.get("access_token")
    headers = {"Authorization": f"Bearer {token}"}

    async with httpx.AsyncClient() as client:
        resp = await client.delete(
            f"{BACKEND_URL}/api/v1/diagnosticos/{diagnostico_id}",
            headers=headers,
        )

    if resp.status_code == 204:
        return JSONResponse(status_code=204, content=None)

    if resp.status_code == 404:
        return JSONResponse(
            status_code=404,
            content={"detail": "Diagnóstico não encontrado"},
        )

    return JSONResponse(
        status_code=resp.status_code,
        content={"detail": "Erro ao remover diagnóstico"},
    )
