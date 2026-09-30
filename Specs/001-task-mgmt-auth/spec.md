# Feature Specification: Gestión Básica de Tareas con Autenticación de Usuarios

**Feature Branch**: `001-task-mgmt-auth`

**Created**: 2026-09-29

**Status**: Ready

**Input**: User description: "Primer incremento funcional de TaskControl: gestión básica de tareas con autenticación de usuarios (HU-01 a HU-04 y HU-12 a HU-13)"

## Clarifications

### Session 2026-09-29
- Q: ¿Cuál es el formato estándar para la fecha límite de las tareas? → A: Formato de fecha ISO `YYYY-MM-DD`.
- Q: ¿Cómo se maneja la persistencia de sesión del usuario? → A: Sesión estándar de Flask basada en cookies firmadas y seguras con expiración configurable.
- Q: ¿Qué mecanismo se utiliza para el hash de contraseñas? → A: Algoritmo seguro PBKDF2/SHA-256 a través de `werkzeug.security`.


## User Scenarios & Testing *(mandatory)*

### User Story 1 - Registro de Usuario (HU-12) (Priority: P1)
Como nuevo usuario del sistema, quiero registrarme proporcionando mi correo electrónico y una contraseña segura, para tener mi propia cuenta privada en TaskControl.

**Why this priority**: Es el punto de entrada al sistema que asegura el aislamiento de datos por usuario y la confidencialidad.

**Independent Test**: Se puede probar registrando un usuario con credenciales válidas y verificando que el usuario queda persistido con contraseña cifrada (hash) y puede ser autenticado.

**Acceptance Scenarios**:
1. **Given** un visitante en la página de registro, **When** ingresa un correo con formato válido no registrado previamente y una contraseña válida, **Then** el sistema crea la cuenta con la contraseña en hash y redirige al inicio de sesión o al tablero principal.
2. **Given** un visitante en la página de registro, **When** ingresa un correo electrónico que ya existe en el sistema, **Then** el sistema rechaza el registro e informa claramente que el correo ya se encuentra en uso.
3. **Given** un visitante en la página de registro, **When** ingresa datos con formato de correo inválido o campos vacíos, **Then** el sistema no procesa el registro y muestra los errores de validación.

---

### User Story 2 - Inicio y Cierre de Sesión (HU-13) (Priority: P1)
Como usuario registrado, quiero iniciar y cerrar sesión de manera segura para acceder a mis tareas y proteger mi información al terminar.

**Why this priority**: Permite la autenticación y el control de acceso en backend en todas las operaciones privadas del sistema.

**Independent Test**: Iniciar sesión con credenciales correctas, verificar que la sesión se mantiene activa para consultar recursos protegidos, y verificar que tras cerrar sesión las rutas protegidas deniegan el acceso.

**Acceptance Scenarios**:
1. **Given** un usuario registrado con credenciales correctas, **When** ingresa su correo y contraseña en el formulario de acceso, **Then** el sistema inicia una sesión autenticada y le da acceso a su tablero de tareas.
2. **Given** un usuario con sesión activa, **When** solicita cerrar sesión, **Then** el sistema destruye la sesión y redirige a la pantalla pública de inicio de sesión.
3. **Given** un usuario no autenticado, **When** intenta acceder directamente a una ruta protegida de gestión de tareas, **Then** el servidor backend deniega el acceso y redirige a iniciar sesión.

---

### User Story 3 - Creación de Tareas (HU-01) (Priority: P2)
Como usuario autenticado, quiero registrar una nueva tarea con título obligatorio, descripción opcional y fecha límite opcional, para llevar control de mis pendientes.

**Why this priority**: Representa la funcionalidad medular de captura de trabajo del sistema.

**Independent Test**: Crear una tarea autenticado con título válido y comprobar que se guarda con estado inicial "pendiente", asociada al usuario y con registro en el log de auditoría.

**Acceptance Scenarios**:
1. **Given** un usuario autenticado, **When** ingresa un título no vacío y opcionalmente descripción y fecha límite, **Then** la tarea se guarda con estado "pendiente", vinculada a dicho usuario, y se emite un log de auditoría con actor, acción, entidad y marca de tiempo.
2. **Given** un usuario autenticado, **When** intenta crear una tarea con el título vacío o compuesto solo por espacios en blanco, **Then** el sistema rechaza la creación y exige un título válido.

---

### User Story 4 - Listado y Filtrado de Tareas Propias (HU-02) (Priority: P2)
Como usuario autenticado, quiero consultar la lista de mis tareas mostrando título, estado y fecha límite, y filtrarlas por estado, para visualizar el avance de mis actividades.

**Why this priority**: Da visibilidad inmediata del trabajo del usuario y asegura que nunca se mezclen datos entre diferentes usuarios.

**Independent Test**: Con varios usuarios con tareas en base de datos, comprobar que el usuario A solo visualiza sus tareas y puede filtrarlas por pendiente, en progreso o completada.

**Acceptance Scenarios**:
1. **Given** un usuario autenticado con tareas creadas en diferentes estados, **When** consulta su listado de tareas, **Then** observa únicamente sus tareas con título, estado y fecha límite.
2. **Given** un usuario autenticado, **When** aplica un filtro por estado ("pendiente", "en progreso" o "completada"), **Then** el sistema muestra exclusivamente las tareas que coincidan con dicho estado.
3. **Given** tareas pertenecientes al Usuario B, **When** el Usuario A consulta su listado de tareas, **Then** ninguna tarea del Usuario B aparece en el resultado.

---

### User Story 5 - Transición y Cambio de Estado de Tareas (HU-03) (Priority: P3)
Como usuario autenticado, quiero cambiar el estado de mis tareas siguiendo el flujo de avance permitido (pendiente -> en progreso -> completada), para reflejar el progreso del trabajo.

**Why this priority**: Gestiona el ciclo de vida del flujo de trabajo de cada tarea.

**Independent Test**: Cambiar el estado de una tarea de "pendiente" a "en progreso" y luego a "completada", comprobando que cada transición genera un registro de auditoría y que no se permiten transiciones inválidas directas hacia atrás desde "completada".

**Acceptance Scenarios**:
1. **Given** una tarea en estado "pendiente" perteneciente al usuario, **When** el usuario cambia su estado a "en progreso", **Then** el estado se actualiza y se registra la auditoría.
2. **Given** una tarea en estado "en progreso" perteneciente al usuario, **When** el usuario cambia su estado a "completada", **Then** el estado se actualiza y se registra la auditoría.
3. **Given** una tarea en estado "completada", **When** el usuario intenta cambiarla directamente a "pendiente", **Then** el sistema rechaza la transición por estar fuera del flujo permitido en este incremento (sin reapertura).

---

### User Story 6 - Edición de Tareas Existentes (HU-04) (Priority: P3)
Como usuario autenticado, quiero editar el título, descripción o fecha límite de una tarea propia existente, para mantener la información al día.

**Why this priority**: Permite corregir o actualizar detalles sin perder el identificador ni la continuidad de la tarea.

**Independent Test**: Modificar los campos editables de una tarea propia y verificar que se aplican las mismas reglas de validación que en la creación.

**Acceptance Scenarios**:
1. **Given** una tarea existente perteneciente al usuario autenticado, **When** el usuario actualiza el título con texto válido, o altera la descripción o fecha límite, **Then** los datos se guardan correctamente.
2. **Given** una tarea existente perteneciente al usuario, **When** el usuario intenta borrar el título dejando un campo vacío, **Then** el sistema rechaza la edición manteniendo los datos previos.
3. **Given** una tarea perteneciente a otro usuario, **When** un usuario intenta modificarla, **Then** el sistema deniega la operación con un error de autorización.

---

### Edge Cases

- **Inyección y caracteres especiales**: Entradas de usuario con etiquetas HTML o scripts son sanitizadas y escapadas adecuadamente tanto al persistir como al presentar.
- **Formato de fechas límite**: Si se suministra una fecha con formato inválido o incoherente, el backend rechaza la petición con mensaje explícito.
- **Concurrencia de sesión**: Si la sesión expira o es invalidada mientras el usuario interactúa, la siguiente petición debe exigir reautenticación sin corrupción de datos.
- **Accesos a recursos ajenos (IDOR)**: Cualquier intento de acceder o modificar el ID de una tarea de otro usuario retorna HTTP 403 Forbidden o 404 Not Found.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema DEBE permitir a usuarios no autenticados registrarse mediante correo electrónico y contraseña.
- **FR-002**: El sistema DEBE validar la unicidad y el formato RFC estándar de la dirección de correo electrónico en el registro.
- **FR-003**: El sistema DEBE almacenar las contraseñas exclusivamente en forma de hash criptográfico seguro (PBKDF2/Argon2/bcrypt), nunca en texto plano.
- **FR-004**: El sistema DEBE autenticar usuarios mediante correo y contraseña y mantener la sesión mediante cookies de sesión firmadas y seguras.
- **FR-005**: El sistema DEBE destruir la sesión del usuario cuando éste solicite explícitamente el cierre de sesión.
- **FR-006**: El sistema DEBE verificar en el backend la existencia de una sesión activa válida en todas las rutas de creación, consulta, cambio de estado y edición de tareas.
- **FR-007**: El sistema DEBE permitir a un usuario autenticado crear tareas con un título obligatorio no vacío, descripción opcional y fecha límite opcional.
- **FR-008**: Toda tarea recién creada DEBE inicializarse con el estado "pendiente".
- **FR-009**: El sistema DEBE asociar de forma inmutable la autoría/propiedad de la tarea al usuario autenticado que la creó.
- **FR-010**: El sistema DEBE listar únicamente las tareas pertenecientes al usuario actualmente autenticado.
- **FR-011**: El sistema DEBE permitir filtrar el listado de tareas por estado ("pendiente", "en progreso", "completada" o todas).
- **FR-012**: El sistema DEBE restringir los cambios de estado a transiciones válidas: de "pendiente" a "en progreso", y de "en progreso" a "completada". No se permite transición directa de "completada" a "pendiente".
- **FR-013**: El sistema DEBE permitir la edición de título, descripción y fecha límite únicamente sobre tareas pertenecientes al usuario autenticado, aplicando las mismas validaciones de campos obligatorios que en la creación.
- **FR-014**: El sistema DEBE registrar un log estructurado de auditoría en cada operación que cree o altere el estado de una tarea, conteniendo: `actor_id`, `action`, `entity_type`, `entity_id` y `timestamp` en formato UTC.

### Key Entities *(include if feature involves data)*

- **User**: Representa un usuario registrado del sistema. Atributos: `id`, `email` (único, validado), `password_hash`, `created_at`.
- **Task**: Representa una actividad o tarea gestionada. Atributos: `id`, `user_id` (clave foránea a User), `title` (cadena no vacía), `description` (texto opcional), `due_date` (fecha opcional), `status` (enum: 'pending', 'in_progress', 'completed'), `created_at`, `updated_at`.
- **AuditLog**: Representa el registro de auditoría de modificaciones de tareas. Atributos: `id`, `actor_id` (User ID), `action` (cadena descriptiva, e.g., 'CREATE', 'STATUS_CHANGE', 'UPDATE'), `entity_type` ('Task'), `entity_id` (Task ID), `details` (información complementaria), `timestamp` (UTC datetime).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Un usuario nuevo puede completar el registro e iniciar sesión en menos de 30 segundos.
- **SC-002**: El 100% de las tareas consultadas en el listado corresponden de forma estricta y verificada al usuario autenticado.
- **SC-003**: El 100% de las operaciones de modificación de tareas quedan registradas en el log de auditoría con sus 4 atributos requeridos (actor, acción, entidad, timestamp).
- **SC-004**: Ninguna contraseña se almacena o expone en texto plano bajo ninguna circunstancia.
- **SC-005**: La totalidad de las pruebas unitarias y de integración que verifican las 6 historias de usuario pasan satisfactoriamente.

## Assumptions

- **A-001**: Los usuarios acceden a través de un navegador web moderno con soporte para cookies de sesión y JavaScript estándar.
- **A-002**: Las funcionalidades de borrado de tareas (HU-05), reapertura (HU-06), categorías (HU-08), prioridades (HU-07) y drag & drop (HU-16) quedan explícitamente postergadas para incrementos futuros según el Backlog.
- **A-003**: En este primer incremento, el log de auditoría se almacena de forma persistente y estructurada en base de datos para trazabilidad inmediata y verificabilidad en pruebas.
