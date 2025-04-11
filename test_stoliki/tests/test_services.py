import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base, get_db
from app.models.models import Table, Reservation
from app.services import table_service, reservation_service
from app.schemas.schemas import TableCreate, ReservationCreate

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture
def db_session():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

def test_create_table(db_session):
    table = TableCreate(name="Test Table", seats=4, location="Test Location")
    db_table = table_service.create_table(db_session, table)
    assert db_table.name == "Test Table"
    assert db_table.seats == 4
    assert db_table.location == "Test Location"

def test_get_tables(db_session):
    table1 = TableCreate(name="Table 1", seats=4, location="Location 1")
    table2 = TableCreate(name="Table 2", seats=6, location="Location 2")
    table_service.create_table(db_session, table1)
    table_service.create_table(db_session, table2)
    
    tables = table_service.get_tables(db_session)
    assert len(tables) == 2
    assert tables[0].name == "Table 1"
    assert tables[1].name == "Table 2"

def test_create_reservation(db_session):
    # Create a table first
    table = TableCreate(name="Test Table", seats=4, location="Test Location")
    db_table = table_service.create_table(db_session, table)
    
    # Create a reservation
    reservation_time = datetime.now()
    reservation = ReservationCreate(
        customer_name="Test Customer",
        table_id=db_table.id,
        reservation_time=reservation_time,
        duration_minutes=60
    )
    
    db_reservation = reservation_service.create_reservation(db_session, reservation)
    assert db_reservation is not None
    assert db_reservation.customer_name == "Test Customer"
    assert db_reservation.table_id == db_table.id

def test_reservation_conflict(db_session):
    # Create a table
    table = TableCreate(name="Test Table", seats=4, location="Test Location")
    db_table = table_service.create_table(db_session, table)
    
    # Create first reservation
    reservation_time = datetime.now()
    reservation1 = ReservationCreate(
        customer_name="Customer 1",
        table_id=db_table.id,
        reservation_time=reservation_time,
        duration_minutes=60
    )
    reservation_service.create_reservation(db_session, reservation1)
    
    # Try to create conflicting reservation
    reservation2 = ReservationCreate(
        customer_name="Customer 2",
        table_id=db_table.id,
        reservation_time=reservation_time + timedelta(minutes=30),
        duration_minutes=60
    )
    db_reservation2 = reservation_service.create_reservation(db_session, reservation2)
    assert db_reservation2 is None 