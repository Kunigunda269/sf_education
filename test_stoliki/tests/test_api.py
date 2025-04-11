from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from app.main import app

client = TestClient(app)

def test_create_table():
    response = client.post(
        "/tables/",
        json={"name": "Test Table", "seats": 4, "location": "Test Location"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Table"
    assert data["seats"] == 4
    assert data["location"] == "Test Location"
    return data["id"]

def test_get_tables():
    response = client.get("/tables/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_create_reservation():
    # Create a table first
    table_id = test_create_table()
    
    # Create a reservation
    reservation_time = datetime.now().isoformat()
    response = client.post(
        "/reservations/",
        json={
            "customer_name": "Test Customer",
            "table_id": table_id,
            "reservation_time": reservation_time,
            "duration_minutes": 60
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["customer_name"] == "Test Customer"
    assert data["table_id"] == table_id
    return data["id"]

def test_reservation_conflict():
    # Create a table
    table_id = test_create_table()
    
    # Create first reservation
    reservation_time = datetime.now().isoformat()
    client.post(
        "/reservations/",
        json={
            "customer_name": "Customer 1",
            "table_id": table_id,
            "reservation_time": reservation_time,
            "duration_minutes": 60
        }
    )
    
    # Try to create conflicting reservation
    response = client.post(
        "/reservations/",
        json={
            "customer_name": "Customer 2",
            "table_id": table_id,
            "reservation_time": reservation_time,
            "duration_minutes": 60
        }
    )
    assert response.status_code == 400
    assert "Table is not available" in response.json()["detail"] 