from datetime import datetime, timezone
import base64
import hashlib
import os
import secrets
import time
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

from app.db import get_connection, init_db
from app.spectrum import QUESTIONS, calculate_spectrum


ABOUT_MESSAGE = (
    "Spectrum es un test didactico para explorar orientaciones politicas de forma "
    "simple. Sus resultados son aproximaciones educativas, no afiliaciones oficiales "
    "ni diagnosticos politicos definitivos."
)

ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", "*").split(",")
    if origin.strip()
]
SECURITY_SECRET = os.getenv("SECURITY_SECRET", "change-this-before-public-launch")
SESSION_TTL_SECONDS = int(os.getenv("SESSION_TTL_SECONDS", "900"))
RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
RATE_LIMIT_MAX_REQUESTS = int(os.getenv("RATE_LIMIT_MAX_REQUESTS", "12"))

app = FastAPI(title="Spectrum API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class TestInput(BaseModel):
    user_id: str = Field(min_length=2, max_length=80)
    username: str = Field(min_length=2, max_length=80)
    session_token: str = Field(min_length=24, max_length=120)
    answers: list[str] = Field(min_length=10, max_length=10)
    self_label: str = Field(default="NONE", min_length=1, max_length=10)
    card_image: Optional[str] = Field(default=None)

    @field_validator("answers")
    @classmethod
    def validate_answers(cls, answers: list[str]) -> list[str]:
        normalized = [answer.strip().upper() for answer in answers]
        invalid = [answer for answer in normalized if answer not in {"A", "B", "C", "D", "E"}]
        if invalid:
            raise ValueError("Cada respuesta debe ser A, B, C, D o E")
        return normalized


def get_client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def hash_value(value: str) -> str:
    payload = f"{SECURITY_SECRET}:{value}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def prune_expired_data() -> None:
    now = time.time()
    try:
        with get_connection() as conn:
            conn.execute("DELETE FROM sessions WHERE expires_at < ?", (now,))
            conn.execute("DELETE FROM rate_limits WHERE hit_timestamp < ?", (now - RATE_LIMIT_WINDOW_SECONDS,))
            conn.commit()
    except Exception as e:
        print(f"Error pruning expired data: {e}")


def enforce_rate_limit(ip_hash: str) -> None:
    prune_expired_data()
    now = time.time()
    window_start = now - RATE_LIMIT_WINDOW_SECONDS

    with get_connection() as conn:
        cursor = conn.execute(
            "SELECT COUNT(*) FROM rate_limits WHERE ip_hash = ? AND hit_timestamp >= ?",
            (ip_hash, window_start)
        )
        count = cursor.fetchone()[0]

        if count >= RATE_LIMIT_MAX_REQUESTS:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Demasiados intentos. Espera un momento y vuelve a probar.",
            )

        conn.execute(
            "INSERT INTO rate_limits (ip_hash, hit_timestamp) VALUES (?, ?)",
            (ip_hash, now)
        )
        conn.commit()


def create_session_token() -> str:
    prune_expired_data()
    token = secrets.token_urlsafe(32)
    token_hash = hash_value(token)
    expires_at = time.time() + SESSION_TTL_SECONDS

    with get_connection() as conn:
        conn.execute(
            "INSERT INTO sessions (token_hash, expires_at) VALUES (?, ?)",
            (token_hash, expires_at)
        )
        conn.commit()
    return token


def consume_session_token(token: str) -> None:
    prune_expired_data()
    token_hash = hash_value(token)
    now = time.time()

    with get_connection() as conn:
        cursor = conn.execute(
            "SELECT expires_at FROM sessions WHERE token_hash = ?",
            (token_hash,)
        )
        row = cursor.fetchone()
        if not row or row[0] < now:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sesion invalida o vencida. Carga de nuevo el test.",
            )
        conn.execute("DELETE FROM sessions WHERE token_hash = ?", (token_hash,))
        conn.commit()



@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/")
def root() -> FileResponse:
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/about")
def about() -> dict:
    return {
        "name": "Spectrum",
        "type": "Political Thinking Map",
        "version": "1.0.0",
        "message": ABOUT_MESSAGE,
    }


@app.get("/questions")
def get_questions() -> dict:
    return {"questions": QUESTIONS}


@app.post("/session")
def create_test_session(request: Request) -> dict:
    ip_hash = hash_value(get_client_ip(request))
    enforce_rate_limit(ip_hash)
    return {
        "session_token": create_session_token(),
        "expires_in_seconds": SESSION_TTL_SECONDS,
    }


@app.post("/submit", status_code=status.HTTP_201_CREATED)
def submit_test(data: TestInput, request: Request) -> dict:
    ip_hash = hash_value(get_client_ip(request))
    enforce_rate_limit(ip_hash)
    consume_session_token(data.session_token)

    result = calculate_spectrum(data.answers, data.self_label)
    percentages = result["percentages"]
    created_at = datetime.now(timezone.utc).isoformat()

    # Guardar la imagen de la tarjeta si se proporciona
    card_image_path = None
    if data.card_image:
        try:
            # Remover encabezado de data url si existe
            encoded = data.card_image
            if "," in encoded:
                encoded = encoded.split(",", 1)[1]
            image_data = base64.b64decode(encoded)
            cards_dir = os.path.join(STATIC_DIR, "cards")
            os.makedirs(cards_dir, exist_ok=True)
            # Sanitizar user_id para evitar Path Traversal
            safe_user_id = "".join(c for c in data.user_id if c.isalnum() or c in ("-", "_"))
            filename = f"{safe_user_id}.png"
            filepath = os.path.join(cards_dir, filename)
            with open(filepath, "wb") as f:
                f.write(image_data)
            card_image_path = f"/static/cards/{filename}"
        except Exception as e:
            print(f"Error saving card image: {e}")

    with get_connection() as conn:
        existing = conn.execute(
            "SELECT user_id FROM results WHERE user_id = ?",
            (data.user_id,),
        ).fetchone()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Este usuario ya completo el test",
            )

        # Contar intentos previos con el mismo nombre de usuario (sin importar mayúsculas/minúsculas)
        cursor = conn.execute(
            "SELECT COUNT(*) FROM results WHERE LOWER(username) = LOWER(?)",
            (data.username,)
        )
        prev_attempts = cursor.fetchone()[0]
        attempt_number = prev_attempts + 1

        conn.execute(
            """
            INSERT INTO results (
                user_id, username, ud, d, c, i, ui, dominant_axis, dominant,
                summary, share_text, ip_hash, created_at, self_label, card_image_path, attempt_number
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data.user_id,
                data.username,
                percentages["UD"],
                percentages["D"],
                percentages["C"],
                percentages["I"],
                percentages["UI"],
                result["dominant_axis"],
                result["dominant"],
                result["summary"],
                result["share_text"],
                ip_hash,
                created_at,
                data.self_label,
                card_image_path,
                attempt_number,
            ),
        )
        conn.commit()

    return {
        "user_id": data.user_id,
        "username": data.username,
        "result": percentages,
        "dominant_axis": result["dominant_axis"],
        "dominant": result["dominant"],
        "summary": result["summary"],
        "mirror_feedback": result["mirror_feedback"],
        "share_text": result["share_text"],
        "created_at": created_at,
        "self_label": data.self_label,
        "card_image_path": card_image_path,
        "attempt_number": attempt_number,
    }


@app.get("/stats")
def get_stats() -> dict:
    with get_connection() as conn:
        cursor = conn.execute("SELECT dominant_axis, COUNT(*) as count FROM results GROUP BY dominant_axis")
        rows = cursor.fetchall()

    stats = {axis: 0 for axis in ["UD", "D", "C", "I", "UI", "MIXED"]}
    total = 0
    for row in rows:
        axis = row["dominant_axis"]
        if axis in stats:
            stats[axis] = row["count"]
            total += row["count"]

    percentages = {}
    for axis, count in stats.items():
        percentages[axis] = round(count / total * 100, 2) if total > 0 else 0.0

    return {
        "total_participants": total,
        "counts": stats,
        "percentages": percentages
    }


class CardUploadInput(BaseModel):
    card_image: str


@app.post("/result/{user_id}/card")
def upload_card(user_id: str, data: CardUploadInput) -> dict:
    card_image_path = None
    try:
        encoded = data.card_image
        if "," in encoded:
            encoded = encoded.split(",", 1)[1]
        image_data = base64.b64decode(encoded)
        cards_dir = os.path.join(STATIC_DIR, "cards")
        os.makedirs(cards_dir, exist_ok=True)
        safe_user_id = "".join(c for c in user_id if c.isalnum() or c in ("-", "_"))
        filename = f"{safe_user_id}.png"
        filepath = os.path.join(cards_dir, filename)
        with open(filepath, "wb") as f:
            f.write(image_data)
        card_image_path = f"/static/cards/{filename}"
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al procesar la imagen: {str(e)}")

    with get_connection() as conn:
        conn.execute(
            "UPDATE results SET card_image_path = ? WHERE user_id = ?",
            (card_image_path, user_id)
        )
        conn.commit()

    return {"status": "ok", "card_image_path": card_image_path}



@app.get("/result/{user_id}")
def get_result(user_id: str, request: Request) -> Any:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM results WHERE user_id = ?",
            (user_id,),
        ).fetchone()

    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No encontrado")

    # Obtener el número de intento con fallback
    attempt_number = 1
    try:
        if "attempt_number" in row.keys() and row["attempt_number"] is not None:
            attempt_number = row["attempt_number"]
    except Exception:
        pass

    # Detectar si la petición viene de un navegador web o crawler de redes sociales
    accept = request.headers.get("accept", "")
    user_agent = request.headers.get("user-agent", "").lower()
    is_crawler = any(bot in user_agent for bot in ["twitterbot", "facebookexternalhit", "whatsapp", "slackbot", "telegrambot"])

    if "text/html" in accept or is_crawler:
        base_url = str(request.base_url).rstrip("/")
        image_path = row["card_image_path"] or "/static/default_card.png"
        image_url = f"{base_url}{image_path}"
        result_url = f"{base_url}/result/{user_id}"

        desc = (
            f"UD {row['ud']}% | D {row['d']}% | C {row['c']}% | "
            f"I {row['i']}% | UI {row['ui']}%"
        )

        html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Spectrum Colombia - Resultado de {row['username']} (Intento #{attempt_number})</title>
  
  <!-- Twitter Card metadata -->
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="¡Hice el Test Spectrum Colombia y salí {row['dominant']} (Intento #{attempt_number})!">
  <meta name="twitter:description" content="{desc}. Descubre si tu etiqueta coincide con tus respuestas reales.">
  <meta name="twitter:image" content="{image_url}">
  
  <!-- Open Graph metadata (Facebook/WhatsApp/Discord) -->
  <meta property="og:type" content="website">
  <meta property="og:title" content="Test Spectrum Colombia - {row['dominant']} (Intento #{attempt_number})">
  <meta property="og:description" content="{desc}. Descubre tu verdadera posición política.">
  <meta property="og:image" content="{image_url}">
  <meta property="og:url" content="{result_url}">

  <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="/static/styles.css">
  <style>
    body {{
      background: var(--paper);
      color: var(--ink);
      font-family: 'Outfit', sans-serif;
    }}
  </style>
</head>
<body class="shared-result-page">
  <main class="shell">
    <section class="result">
      <p class="eyebrow">Spectrum Colombia</p>
      <div class="result-card axis-{row['dominant_axis']}" style="background-image: url('{image_url}'); background-size: cover; background-position: center; border: 1px solid var(--line);">
        <!-- La imagen de fondo contiene toda la información de la tarjeta -->
      </div>
      
      <div class="bars" style="margin-top: 24px;">
        <div class="bar"><span>UD</span><span class="track"><span class="fill" style="width:{row['ud']}%"></span></span><span>{row['ud']}%</span></div>
        <div class="bar"><span>D</span><span class="track"><span class="fill" style="width:{row['d']}%"></span></span><span>{row['d']}%</span></div>
        <div class="bar"><span>C</span><span class="track"><span class="fill" style="width:{row['c']}%"></span></span><span>{row['c']}%</span></div>
        <div class="bar"><span>I</span><span class="track"><span class="fill" style="width:{row['i']}%"></span></span><span>{row['i']}%</span></div>
        <div class="bar"><span>UI</span><span class="track"><span class="fill" style="width:{row['ui']}%"></span></span><span>{row['ui']}%</span></div>
      </div>
      
      <p class="summary" style="margin-top: 20px;">{row['summary']}</p>
      
      <div class="actions" style="grid-template-columns: 1fr; margin-top: 24px;">
        <a class="primary" href="/" style="display: flex; align-items: center; justify-content: center; text-decoration: none; min-height: 44px; border-radius: 8px; font-weight: 700; color: white; background: var(--ink);">¡Haz el Test Spectrum Tú También!</a>
      </div>
    </section>
  </main>
</body>
</html>
"""
        return HTMLResponse(content=html_content)

    return {
        "user_id": row["user_id"],
        "username": row["username"],
        "result": {
            "UD": row["ud"],
            "D": row["d"],
            "C": row["c"],
            "I": row["i"],
            "UI": row["ui"],
        },
        "dominant_axis": row["dominant_axis"],
        "dominant": row["dominant"],
        "summary": row["summary"],
        "share_text": row["share_text"],
        "created_at": row["created_at"],
        "self_label": row["self_label"],
        "card_image_path": row["card_image_path"],
        "attempt_number": attempt_number
    }


