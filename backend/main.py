from fastapi import FastAPI

app = FastAPI(title="ShadowWatch API")


@app.get("/")
def root():
    return {
        "message": "ShadowWatch backend is running"
    }