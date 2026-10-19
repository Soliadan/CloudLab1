
from fastapi import FastAPI

app = FastAPI(title="CloudLab1 API")


@app.get("/")
def home():
    return {"message": "Welcome to CloudLab1 API"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/tasks")
def get_tasks():
    return {"tasks": []}
