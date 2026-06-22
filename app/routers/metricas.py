from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import httpx
from jose import jwt

from app.config import BACKEND_URL, TEMPLATES_DIR, SECRET_KEY, ALGORITHM

router = APIRouter(prefix="/metricas", tags=["metricas"])
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
async def pagina_metricas(
    request: Request,
    user: dict = Depends(_require_user),
):
    token = request.cookies.get("access_token")
    headers = {"Authorization": f"Bearer {token}"}

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{BACKEND_URL}/api/v1/metricas",
            headers=headers,
        )

    metricas = resp.json() if resp.status_code == 200 else {}
    erros = []
    if resp.status_code == 404:
        erros.append("Metricas nao encontradas. Execute setup.py no backend primeiro.")

    return templates.TemplateResponse(
        request,
        "metricas.html",
        {
            "request": request,
            "user": user,
            "metricas": metricas,
            "modelos_disponiveis": {"knn_model.joblib": True, "svm_model.joblib": True},
            "imagens_disponiveis": {
                "confusao_knn": True,
                "confusao_svm": True,
                "roc_knn": True,
                "roc_svm": True,
                "roc_comparativa": True,
                "pr_comparativa": True,
            },
            "erros": erros,
        },
    )
