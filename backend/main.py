'''
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

from database import SessionLocal
from models import Entity


app = FastAPI(title="ShadowWatch API")


# Database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def root():
    return {
        "message": "ShadowWatch backend is running"
    }


@app.get("/entities")
def get_entities(db: Session = Depends(get_db)):
    entities = db.query(Entity).all()

    return entities
    '''

# re written by Deepa

from fastapi import FastAPI
from routes import cases, entities, telemetry

app = FastAPI(title="ShadowWatch API")

@app.get("/")
def root():
    return {
        "message": "ShadowWatch backend is running"
    }

# Register the modular endpoints
app.include_router(entities.router)
app.include_router(cases.router)
app.include_router(telemetry.router)