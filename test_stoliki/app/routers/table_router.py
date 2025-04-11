from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.schemas import Table, TableCreate
from app.services import table_service

router = APIRouter()

@router.get("/tables/", response_model=List[Table])
def read_tables(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    tables = table_service.get_tables(db, skip=skip, limit=limit)
    return tables

@router.post("/tables/", response_model=Table)
def create_table(table: TableCreate, db: Session = Depends(get_db)):
    return table_service.create_table(db=db, table=table)

@router.delete("/tables/{table_id}")
def delete_table(table_id: int, db: Session = Depends(get_db)):
    if table_service.delete_table(db=db, table_id=table_id):
        return {"message": "Table deleted successfully"}
    raise HTTPException(status_code=404, detail="Table not found") 