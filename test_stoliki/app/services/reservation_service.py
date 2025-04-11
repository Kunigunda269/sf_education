from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.models import Reservation
from app.schemas.schemas import ReservationCreate
from typing import List, Optional
from datetime import datetime, timedelta

def get_reservations(db: Session, skip: int = 0, limit: int = 100) -> List[Reservation]:
    return db.query(Reservation).offset(skip).limit(limit).all()

def get_reservation(db: Session, reservation_id: int) -> Optional[Reservation]:
    return db.query(Reservation).filter(Reservation.id == reservation_id).first()

def is_table_available(db: Session, table_id: int, reservation_time: datetime, duration_minutes: int) -> bool:
    end_time = reservation_time + timedelta(minutes=duration_minutes)
    
    conflicting_reservations = db.query(Reservation).filter(
        and_(
            Reservation.table_id == table_id,
            Reservation.reservation_time < end_time,
            Reservation.reservation_time + timedelta(minutes=Reservation.duration_minutes) > reservation_time
        )
    ).first()
    
    return conflicting_reservations is None

def create_reservation(db: Session, reservation: ReservationCreate) -> Optional[Reservation]:
    if not is_table_available(db, reservation.table_id, reservation.reservation_time, reservation.duration_minutes):
        return None
        
    db_reservation = Reservation(**reservation.model_dump())
    db.add(db_reservation)
    db.commit()
    db.refresh(db_reservation)
    return db_reservation

def delete_reservation(db: Session, reservation_id: int) -> bool:
    reservation = get_reservation(db, reservation_id)
    if reservation:
        db.delete(reservation)
        db.commit()
        return True
    return False 