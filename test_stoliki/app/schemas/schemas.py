from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class TableBase(BaseModel):
    name: str
    seats: int = Field(gt=0)
    location: str

class TableCreate(TableBase):
    pass

class Table(TableBase):
    id: int

    class Config:
        from_attributes = True

class ReservationBase(BaseModel):
    customer_name: str
    table_id: int
    reservation_time: datetime
    duration_minutes: int = Field(gt=0)

class ReservationCreate(ReservationBase):
    pass

class Reservation(ReservationBase):
    id: int

    class Config:
        from_attributes = True

class ReservationWithTable(Reservation):
    table: Table 