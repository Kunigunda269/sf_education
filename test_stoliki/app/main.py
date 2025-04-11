from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import table_router, reservation_router
from app.database import engine
from app.models import models

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Restaurant Table Reservation API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(table_router.router)
app.include_router(reservation_router.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to Restaurant Table Reservation API"} 