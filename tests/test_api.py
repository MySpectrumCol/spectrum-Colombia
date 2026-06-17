import os
import pytest
from fastapi.testclient import TestClient

# Configurar ruta de base de datos temporal para pruebas
os.environ["DATABASE_PATH"] = "test_spectrum.db"

from app.main import app
from app.db import init_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    init_db()
    yield
    # Limpiar base de datos de pruebas tras finalizar
    if os.path.exists("test_spectrum.db"):
        try:
            os.remove("test_spectrum.db")
        except OSError:
            pass


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_get_questions():
    response = client.get("/questions")
    assert response.status_code == 200
    assert "questions" in response.json()
    assert len(response.json()["questions"]) == 10


def test_full_test_flow():
    import uuid
    uid = f"test_user_{uuid.uuid4().hex}"
    
    # 1. Crear sesión
    response = client.post("/session")
    assert response.status_code == 200
    session_data = response.json()
    assert "session_token" in session_data
    token = session_data["session_token"]

    # 2. Enviar respuestas con etiqueta propia
    payload = {
        "user_id": uid,
        "username": uid,
        "session_token": token,
        "answers": ["A", "A", "A", "A", "A", "A", "A", "A", "A", "A"],
        "self_label": "C",
    }
    response = client.post("/submit", json=payload)
    assert response.status_code == 201
    result_data = response.json()
    assert result_data["dominant"] == "Ultraderecha"
    assert "mirror_feedback" in result_data
    assert "sorpresa" in result_data["mirror_feedback"].lower()

    # 3. Consultar resultados mediante JSON API
    response = client.get(f"/result/{uid}", headers={"Accept": "application/json"})
    assert response.status_code == 200
    assert response.json()["dominant"] == "Ultraderecha"
    assert response.json()["self_label"] == "C"

    # 4. Consultar estadísticas
    response = client.get("/stats")
    assert response.status_code == 200
    stats = response.json()
    assert stats["total_participants"] >= 1
    assert stats["counts"]["UD"] >= 1
