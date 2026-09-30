<!--
Sync Impact Report:
- Version change: Initial template -> 1.0.0
- Ratified: 2026-09-29
- Added principles:
  - I. Monolito por diseño
  - II. Separación de responsabilidades dentro del monolito
  - III. Contrato explícito entre backend y JavaScript
  - IV. Test-First para la lógica de negocio (No negociable)
  - V. Simplicidad sobre generalidad prematura (YAGNI)
  - VI. Integridad de datos y migraciones
  - VII. Seguridad por defecto
  - VIII. Observabilidad mínima viable
- Added sections:
  - Restricciones Técnicas del Stack
  - Gobernanza y Procedimiento de Enmienda
- Deferred items: None
-->

# TaskControl Constitution

## Core Principles

### I. Monolito por diseño
El sistema TaskControl se construye como un único repositorio, un único proceso desplegable y una única base de datos relacional. Queda explícitamente prohibida la introducción de microservicios, buses o colas de mensajes distribuidas, salvo que una especificación técnica futura demuestre con evidencia de carga o acoplamiento que la arquitectura monolítica no puede satisfacer un requisito concreto del sistema.

### II. Separación de responsabilidades dentro del monolito
El código debe estructurarse en capas estrictamente aisladas:
1. **Modelos de datos**: Definición de entidades, tipos y relaciones SQLAlchemy.
2. **Lógica de negocio (Servicios)**: Operaciones de dominio, transiciones de estado, reglas de validación y cálculo.
3. **Rutas HTTP (Blueprints de Flask)**: Controladores web y endpoints REST que reciben requests, delegan en servicios y devuelven respuestas HTTP.
4. **Presentación**: Plantillas HTML con motor Jinja2 y JavaScript ligero cliente.
Ninguna capa superior puede acceder a otra capa saltándose la inmediatamente inferior (por ejemplo, los controladores/rutas no ejecutan consultas SQLAlchemy directas ni manipulan el estado sin pasar por la capa de servicio).

### III. Contrato explícito entre backend y JavaScript
Toda interacción entre el cliente (JavaScript) y el servidor (Flask) debe realizarse a través de endpoints HTTP con contrato formalmente definido y documentado antes de su implementación (especificando ruta, método HTTP, parámetros/cuerpo JSON de entrada, formato y estructura de salida, y códigos de estado HTTP / respuestas de error).

### IV. Test-First para la lógica de negocio (No negociable)
La creación de tareas, transiciones de estado válidas, eliminación de tareas, asignaciones y reglas de negocio críticas deben especificarse primero como pruebas automatizadas unitarias/de integración que fallen (Red), para posteriormente escribir el código de producción que las satisfaga (Green) y refactorizar (Refactor). La existencia y paso exitoso de dichas pruebas automatizadas es condición bloqueante para dar por concluida cualquier funcionalidad del dominio.

### V. Simplicidad sobre generalidad prematura (YAGNI)
Ninguna abstracción, capa de configuración genérica, patrón de fábrica innecesario o sistema extensible de plugins puede introducirse en el código base sin la existencia de un requisito funcional o técnico ya especificado en el Backlog que lo justifique de forma inmediata.

### VI. Integridad de datos y migraciones
Todo cambio en el modelo o esquema de la base de datos debe gestionarse de forma reproducible, declarativa y versionada a través de herramientas de migración (Flask-Migrate / Alembic). Quedan expresamente prohibidas las modificaciones directas o manuales sobre la base de datos de entornos de prueba o producción.

### VII. Seguridad por defecto
1. Toda entrada de usuario (parámetros de consulta, formularios, payloads JSON) debe validarse y sanitizarse exhaustivamente en el backend, sin confiar jamás de forma exclusiva en validaciones del lado del cliente.
2. La autenticación y autorización deben validarse en el backend en todos y cada uno de los endpoints que modifiquen, consulten o administren datos.
3. Las contraseñas se almacenan obligatoriamente con algoritmos de hashing seguros (p. ej. Argon2, bcrypt o Werkzeug security hash), nunca en texto plano.
4. Jamás se versionan secretos, llaves criptográficas o credenciales en el repositorio de código.

### VIII. Observabilidad mínima viable
Toda operación que altere el estado de una tarea (creación, edición, transición de estado, reapertura, eliminación o reasignación) debe registrarse en un log de auditoría estructurado. Cada evento debe incluir inequívocamente:
- **Actor**: Identificador del usuario que ejecuta la acción.
- **Acción**: Tipo de operación efectuada (p. ej. `TASK_CREATED`, `STATUS_CHANGED`).
- **Entidad**: Identificador y tipo de la entidad afectada (`Task`, ID).
- **Marca de tiempo (Timestamp)**: Fecha y hora en formato ISO 8601 UTC.

## Restricciones Técnicas del Stack

- **Lenguaje**: Python 3.11 o superior.
- **Framework Web**: Flask como framework backend exclusivo (queda prohibido introducir Django, FastAPI u otros frameworks sin una enmienda constitucional formal).
- **Persistencia / ORM**: Base de datos relacional (SQLite para desarrollo/testing, PostgreSQL para producción) administrada mediante SQLAlchemy como ORM.
- **Migraciones**: Flask-Migrate (Alembic).
- **Frontend / Cliente**: Plantillas Jinja2 y JavaScript nativo/modular, sin frameworks SPA pesados (como React, Angular o Vue) por defecto, manteniendo la interactividad fluida y progresiva.
- **Reproducibilidad y Ejecución**: El entorno de desarrollo y ejecución de pruebas debe poder levantarse con un único comando documentado (`python -m venv` / `pip install -r requirements.txt` / `flask run`).

## Gobernanza y Procedimiento de Enmienda

1. La presente Constitución prevalece sobre cualquier otra convención, decisión temporal o práctica de desarrollo informal en el proyecto TaskControl.
2. Todo Pull Request y revisión de código debe comprobar activamente el cumplimiento irrestricto de estos principios antes de su fusión.
3. Cualquier modificación a esta Constitución requiere una propuesta formal de enmienda documentada, justificación técnica y actualización del versionado semántico:
   - **MAJOR**: Modificaciones que eliminen principios fundamentales o redefinan de forma incompatible la arquitectura o gobernanza.
   - **MINOR**: Incorporación de nuevos principios, secciones o directrices ampliadas sin contradecir los existentes.
   - **PATCH**: Ajustes tipográficos, correcciones de redacción o clarificaciones menores que no alteren el alcance de las reglas.

**Version**: 1.0.0 | **Ratified**: 2026-09-29 | **Last Amended**: 2026-09-29
