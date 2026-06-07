from fastapi import FastAPI


APP_VERSION = "0.1.0"

app = FastAPI(title="FlexSignal AI API", version=APP_VERSION)


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "flexsignal-ai-api",
        "version": APP_VERSION,
    }
