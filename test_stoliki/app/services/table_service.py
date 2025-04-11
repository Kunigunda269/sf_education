from sqlalchemy.orm import Session
from app.models.models import Table
from app.schemas.schemas import TableCreate
from typing import List, Optional

def get_tables(db: Session, skip: int = 0, limit: int = 100) -> List[Table]:
    return db.query(Table).offset(skip).limit(limit).all()

def get_table(db: Session, table_id: int) -> Optional[Table]:
    return db.query(Table).filter(Table.id == table_id).first()

def create_table(db: Session, table: TableCreate) -> Table:
    db_table = Table(**table.model_dump())
    db.add(db_table)
    db.commit()
    db.refresh(db_table)
    return db_table

def delete_table(db: Session, table_id: int) -> bool:
    table = get_table(db, table_id)
    if table:
        db.delete(table)
        db.commit()
        return True
    return False 