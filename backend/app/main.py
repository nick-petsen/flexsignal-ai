from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.energy import router as energy_router


APP_VERSION = "0.1.0"
LOCAL_DEVELOPMENT_CORS_ORIGINS = (
    "http://localhost:3000",
    "http://127.0.0.1:3000",
)

app = FastAPI(title="FlexSignal AI API", version=APP_VERSION)
app.add_middleware(
    CORSMiddleware,
    allow_origins=LOCAL_DEVELOPMENT_CORS_ORIGINS,
    allow_methods=("GET", "OPTIONS"),
)
app.include_router(energy_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "flexsignal-ai-api",
        "version": APP_VERSION,
    }
