# Research & Technical Decisions: Increment 1 (TaskControl)

## 1. Monolithic Architecture & Modular Layers
- **Decision**: Monolito modular en Flask con Application Factory pattern (`create_app`), configuración por entornos (`DevelopmentConfig`, `TestingConfig`), Blueprints independientes para `auth` y `tasks`, capa de servicios de dominio pura, modelos SQLAlchemy declarativos y templates Jinja2.
- **Rationale**: Cumple directamente con los Principios I y II de la Constitución. Permite testear servicios de forma aislada sin acoplamiento a requests HTTP de Flask y mantener un único proceso desplegable.
- **Alternatives considered**:
  - Flask en un solo archivo plano (`app.py` monolítico sin blueprints): Rechazado porque viola la separación estricta de responsabilidades (Principio II).
  - Microservicios separados para Auth y Tasks: Explícitamente prohibido por el Principio I de la Constitución.

## 2. Password Hashing & Security
- **Decision**: Uso de `werkzeug.security` (`generate_password_hash`, `check_password_hash`) con algoritmo PBKDF2:SHA256 con salt dinámico integrado.
- **Rationale**: Viene incorporado en Werkzeug/Flask, sin dependencias externas pesadas en C, ofrece protección robusta contra ataques de diccionario y rainbow tables, cumpliendo el Principio VII.
- **Alternatives considered**:
  - `bcrypt` o `argon2-cffi`: Muy seguros pero añaden dependencias de compilación binaria en entornos Windows que pueden generar incompatibilidades con Python 3.14. `werkzeug.security` es nativo y robusto.

## 3. Database & Migrations
- **Decision**: SQLAlchemy 2.x con Flask-SQLAlchemy y Flask-Migrate (Alembic) sobre SQLite para desarrollo y pruebas locales.
- **Rationale**: SQLite no requiere servidores externos ni configuración compleja para levantar el entorno con un solo comando (Principio técnico del Stack). Flask-Migrate garantiza migraciones reproducibles y declarativas (Principio VI).
- **Alternatives considered**:
  - `db.create_all()` sin migraciones: Rechazado porque viola el Principio VI (Integridad de datos y migraciones).

## 4. Structured Audit Logging
- **Decision**: Servicio centralizado `AuditService` que persiste eventos en una tabla relacional `AuditLog` y los canaliza concurrentemente mediante el módulo estándar `logging` con formato JSON estructurado.
- **Rationale**: Asegura la inmutabilidad y verificabilidad inmediata requerida por el Principio VIII de la Constitución, permitiendo a los tests automatizados inspeccionar registros de auditoría directamente en la base de datos de pruebas.
- **Alternatives considered**:
  - Logging exclusivo en archivo de texto plano: Dificulta validaciones automatizadas en tests unitarios.
  - Triggers a nivel de base de datos: Agrega complejidad innecesaria (viola Principio V - Simplicidad).

## 5. Testing Framework & Methodology
- **Decision**: `pytest` con fixtures dedicadas para cliente de pruebas (`client`), aplicación configurada en modo testing (`test_app`) y base de datos aislada en memoria/transaccional.
- **Rationale**: Estándar de la industria en Python, excelente soporte para parametrización, aserciones expresivas y cumplimiento riguroso del enfoque Test-First (Principio IV).
