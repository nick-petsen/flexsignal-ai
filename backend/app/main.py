from fastapi import FastAPI

from app.api.energy import router as energy_router


APP_VERSION = "0.1.0"

app = FastAPI(title="FlexSignal AI API", version=APP_VERSION)
app.include_router(energy_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "flexsignal-ai-api",
        "version": APP_VERSION,
    }
