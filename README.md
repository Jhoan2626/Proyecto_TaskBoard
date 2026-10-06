# Proyecto_TaskBoard
aqui vamos a realizar el proyecto de task board correspondiente a el desarrollo horientado por especificaciones 

## Puesta en marcha (TaskControl)

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt

# Crea/actualiza el esquema de taskcontrol.db (obligatorio antes del primer arranque)
flask --app app.py db upgrade

flask --app app.py run          # http://127.0.0.1:5000
pytest                          # incluye tests/test_auditoria_completa.py
```

Si `/register` muestra `No existe la tabla: users`, la base de datos no tiene el esquema: ejecute `flask --app app.py db upgrade`.

La historia de migraciones (`migrations/versions`) debe mantener una única cabeza; la prueba de auditoría verifica que
`flask db upgrade` construye el esquema completo y que los modelos no difieren de las migraciones (`flask db check`).