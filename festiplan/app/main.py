from fastapi import FastAPI
from app.config import settings
from app.adapters.outbound.persistence.database import Base,engine
from app.adapters.outbound.persistence import models
from app.adapters.inbound.http import festivals,artists,stages,concerts,incidents
from app.adapters.inbound.http.errors import register_error_handlers

Base.metadata.create_all(bind=engine)
app=FastAPI(title=settings.app_name,version="0.1.0",description="API de gestion d'un festival fictif")
register_error_handlers(app)

for router in (festivals.router,artists.router,stages.router,concerts.router,incidents.router): app.include_router(router)

@app.get("/")
def health(): return {"message":"Bienvenue sur FestiPlan","status":"ok"}
