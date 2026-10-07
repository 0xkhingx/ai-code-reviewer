from fastapi import FastAPI

from apps.api.routes import webhooks

app = FastAPI(title="firstpass")
app.include_router(webhooks.router)


@app.get("/health")
def health():
    return {"ok": True}
