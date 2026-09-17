from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from routes import cases, entities, telemetry, findings, system

app = FastAPI(title='ShadowWatch API')

@app.get('/')
def root():
    return {'message': 'ShadowWatch backend is running'}

@app.exception_handler(SQLAlchemyError)
async def database_error(request: Request, exc: SQLAlchemyError):
    return JSONResponse(status_code=503, content={'detail': 'Database operation unavailable'})

for router in (entities.router, cases.router, telemetry.router, findings.router, system.router):
    app.include_router(router)
