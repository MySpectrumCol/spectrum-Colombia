# Spectrum API

API lista para un MVP de produccion del test Spectrum.

## Que incluye

- Motor de calculo Spectrum separado de la API.
- Validacion de 10 respuestas obligatorias, solo `A`, `B`, `C`, `D` o `E`.
- Resumen interpretativo para cada resultado: Centro, Derecha, Izquierda, Ultraderecha y Ultraizquierda.
- Texto listo para compartir en X.
- Token temporal de test para reducir envios automatizados.
- Rate limit basico por IP hasheada.
- Base de datos SQLite para MVP.
- Endpoints `/session`, `/submit`, `/result/{user_id}`, `/about` y `/health`.
- Dockerfile para desplegar en Render, Railway, Fly.io o un VPS.

## Ejecutar localmente

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Abre:

- http://127.0.0.1:8000
- http://127.0.0.1:8000/about
- http://127.0.0.1:8000/docs

## Probar el envio de respuestas

En la documentacion interactiva de FastAPI entra a:

http://127.0.0.1:8000/docs

Primero abre `POST /session`. Copia el `session_token`.

Luego abre `POST /submit` y usa este cuerpo:

```json
{
  "user_id": "usuario123",
  "username": "usuario123",
  "session_token": "pega_aqui_el_token",
  "answers": ["A", "B", "C", "D", "E", "A", "B", "C", "D", "E"]
}
```

## Desplegar en Render

1. Sube esta carpeta a un repositorio de GitHub.
2. En Render crea un nuevo `Web Service`.
3. Conecta el repositorio.
4. Usa estos valores:
   - Runtime: Docker
   - Health check path: `/health`
5. Agrega variables de entorno:
   - `DATABASE_PATH=/data/spectrum.db`
   - `ALLOWED_ORIGINS=*`
   - `SECURITY_SECRET=un_texto_largo_secreto`
6. Crea un persistent disk montado en `/data` para no perder la base de datos.

## Importante antes de conectar X

La integracion con X necesita credenciales reales de desarrollador y debe hacerse con variables de entorno, nunca pegando claves en el codigo.

Para produccion real con muchos usuarios, el siguiente paso recomendado es cambiar SQLite por PostgreSQL.
