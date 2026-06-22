import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.config import TEMPLATES_DIR, STATIC_DIR, CORS_ORIGINS

templates = Jinja2Templates(directory=TEMPLATES_DIR)

_WEB_PATHS = {
    "/auth/login-page",
    "/diagnosticos/",
    "/diagnosticos/historico",
    "/metricas/",
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="APPSPEC Frontend — Sistema de Apoio ao Diagnóstico de Apendicite",
    description="Frontend Web para o APPSPEC — UFG",
    version="1.2.0",
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.exception_handler(401)
async def unauthorized_handler(request: Request, exc: HTTPException):
    if request.url.path in _WEB_PATHS or not request.url.path.startswith("/api/"):
        return RedirectResponse(url="/auth/login-page")
    return JSONResponse(status_code=401, content={"detail": str(exc.detail)})


@app.exception_handler(403)
async def forbidden_handler(request: Request, exc: HTTPException):
    return templates.TemplateResponse(
        request,
        "403.html",
        {"request": request, "detail": str(exc.detail)},
        status_code=403,
    )


from app.routers import diagnostico, metricas, auth  # noqa: E402

app.include_router(diagnostico.router)
app.include_router(metricas.router)
app.include_router(auth.router)


@app.get("/")
async def root():
    return RedirectResponse(url="/diagnosticos/")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=3000, reload=True)
