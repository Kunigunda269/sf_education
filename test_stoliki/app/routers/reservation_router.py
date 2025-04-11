from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.schemas import Reservation, ReservationCreate, ReservationWithTable
from app.services import reservation_service

router = APIRouter()

@router.get("/reservations/", response_model=List[ReservationWithTable])
def read_reservations(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    reservations = reservation_service.get_reservations(db, skip=skip, limit=limit)
    return reservations

@router.post("/reservations/", response_model=ReservationWithTable)
def create_reservation(reservation: ReservationCreate, db: Session = Depends(get_db)):
    db_reservation = reservation_service.create_reservation(db=db, reservation=reservation)
    if db_reservation is None:
        raise HTTPException(status_code=400, detail="Table is not available for the specified time")
    return db_reservation

@router.delete("/reservations/{reservation_id}")
def delete_reservation(reservation_id: int, db: Session = Depends(get_db)):
    if reservation_service.delete_reservation(db=db, reservation_id=reservation_id):
        return {"message": "Reservation deleted successfully"}
    raise HTTPException(status_code=404, detail="Reservation not found") 