from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.health import router as health_router
from app.routes.imports import router as imports_router
from app.routes.graph import router as graph_router

app = FastAPI(title="Palimpsest API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api")
app.include_router(imports_router, prefix="/api")
app.include_router(graph_router, prefix="/api")
