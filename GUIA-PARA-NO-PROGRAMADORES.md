# Guia rapida para arrancar Spectrum en Windows

Ya tienes Python instalado. Ahora haz esto:

1. Abre la carpeta `spectrum-api`.
2. Haz doble clic en `start-windows.bat`.
3. Espera a que termine de instalar lo necesario.
4. Cuando veas que dice `Uvicorn running`, abre:

http://127.0.0.1:8000/docs

Para cerrar el servidor, vuelve a la ventana negra y presiona `Ctrl + C`.

## Prueba sencilla

1. Entra a http://127.0.0.1:8000/docs
2. Abre `POST /session`.
3. Presiona `Try it out`.
4. Presiona `Execute`.
5. Copia el valor de `session_token`.
6. Abre `POST /submit`.
7. Presiona `Try it out`.
8. Pega este ejemplo, reemplazando `pega_aqui_el_token`:

```json
{
  "user_id": "usuario123",
  "username": "usuario123",
  "session_token": "pega_aqui_el_token",
  "answers": ["A", "B", "C", "D", "E", "A", "B", "C", "D", "E"]
}
```

9. Presiona `Execute`.

Si todo salio bien, veras porcentajes, resultado, resumen y texto para compartir.
