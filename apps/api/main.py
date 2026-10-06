from fastapi import FastAPI

from apps.api.routes import webhooks

app = FastAPI(title="AI Code Reviewer")
app.include_router(webhooks.router)


@app.get("/health")
def health():
    return {"ok": True}
