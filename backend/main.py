from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Cybersecurity API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {"message": "Cybersecurity API is running!"}


@app.get("/api/health")
def health():
    return {"status": "online"}


@app.post("/api/analyze")
def analyze(data: dict):
    return {
        "status": "success",
        "received": data,
        "message": "Analysis request received",
    }