# Bitácora de Prompts — Proyecto TaskControl (TaskBoard)

Este documento registra y centraliza todos los **prompts**, instrucciones y comandos utilizados a lo largo del ciclo de vida del proyecto **TaskControl**, aplicando la metodología de **Desarrollo Orientado por Especificaciones (Spec-Driven Development / Speckit)** con el asistente de Inteligencia Artificial (Antigravity).

---

## Índice

1. [Fase 0: Configuración Inicial y Constitución](#fase-0-configuración-inicial-y-constitución)
2. [Incremento 1: Gestión Básica de Tareas y Autenticación](#incremento-1-gestión-básica-de-tareas-y-autenticación)
3. [Incremento 2: Cierre de Gestión de Tareas y Recuperación de Acceso](#incremento-2-cierre-de-gestión-de-tareas-y-recuperación-de-acceso)
4. [Incremento 3: Organización y Priorización](#incremento-3-organización-y-priorización)
5. [Incremento 4: Colaboración](#incremento-4-colaboración)
6. [Incremento 5: Interfaz e Interacción (JavaScript)](#incremento-5-interfaz-e-interacción-javascript)
7. [Prompts de Soporte, Git y Calidad](#prompts-de-soporte-git-y-calidad)
8. [Plantilla para Nuevos Registros](#plantilla-para-nuevos-registros)

---

## Fase 0: Configuración Inicial y Constitución

### 0.1 Inicialización de Speckit
```bash
specify init . --integration agy --script ps --force
```

### 0.2 Prompt de Constitución del Proyecto
* **Comando:** `/speckit-constitution`
* **Objetivo:** Establecer los principios rectores, arquitectura, stack tecnológico y reglas de gobernanza del monolito.

```markdown
Crea la constitución del proyecto TaskControl, una aplicación de control de tareas construida con arquitectura monolítica: backend en Python con Flask, y JavaScript del lado del cliente para interactividad, sin frontend framework pesado por defecto.

Toma como referencia el backlog del proyecto en .specify/memory/backlog.md para mantener consistencia de alcance y numeración de historias (HU-XX) con el resto del roadmap del proyecto.

Los principios que debe fijar la constitución son:

1. Monolito por diseño: un único repositorio, un único proceso desplegable, una
   única base de datos relacional. No se introducen microservicios ni colas de
   mensajes salvo que una especificación futura demuestre con evidencia que el
   monolito no puede sostener un requisito concreto.

2. Separación de responsabilidades dentro del monolito: capas claramente
   separadas entre modelos de datos, lógica de negocio (servicios), rutas HTTP
   (blueprints de Flask) y presentación (plantillas Jinja2 + JavaScript).
   Ninguna capa accede a otra saltándose la inmediatamente inferior.

3. Contrato explícito entre backend y JavaScript: toda interacción cliente-
   servidor pasa por endpoints HTTP con contrato definido (ruta, método,
   payload de entrada/salida, códigos de error), documentado antes de
   implementarse.

4. Test-first para toda la lógica de negocio: creación, transición de estado y
   eliminación de tareas, reglas de asignación y validaciones se especifican
   primero como prueba automatizada que debe fallar, luego se implementa el
   código que la hace pasar. Esto es bloqueante para la capa de dominio.

5. Simplicidad sobre generalidad prematura: ninguna abstracción, capa de
   configuración o sistema de plugins se introduce sin un requisito ya
   especificado que lo justifique.

6. Integridad de datos: todo cambio de esquema se hace mediante migraciones
   versionadas y reproducibles (Flask-Migrate/Alembic), nunca modificaciones
   manuales directas.

7. Seguridad por defecto: toda entrada de usuario se valida y sanitiza en el
   backend independientemente de la validación en JavaScript; autenticación y
   autorización se verifican en cada endpoint que modifique datos; no se
   almacenan secretos en el repositorio.

8. Observabilidad mínima viable: toda operación que modifique el estado de una
   tarea queda registrada en un log estructurado con actor, acción, entidad y
   marca de tiempo, desde el primer incremento funcional.

Incluye también restricciones técnicas del stack: Python 3.11+, Flask como
único framework web (no se introduce Django, FastAPI ni ningún otro sin
enmienda de esta constitución), base de datos relacional vía SQLAlchemy como
ORM, JavaScript sin framework SPA por defecto salvo justificación explícita, y
entorno levantable con un solo comando. Cierra también una sección de
gobernanza que defina el procedimiento de enmienda con versionado semántico
(MAYOR/MENOR/PARCHE).
```

---

## Incremento 1: Gestión Básica de Tareas y Autenticación

**Historias cubiertas:** HU-01 a HU-04, HU-12, HU-13  
**Rama:** `implementacion-1`

### 1.1 Especificación (`/speckit-specify`)
```markdown
Especifica el primer incremento funcional de TaskControl: gestión básica de
tareas con autenticación de usuarios. Este incremento cubre HU-01 a HU-04 y HU-12–HU-13 del backlog del proyecto.
Alcance funcional:

1. Registro de usuario (HU-12): un usuario nuevo se registra con correo y
   contraseña. La contraseña se almacena con hash, nunca en texto plano. Se
   valida formato de correo y unicidad (no se permite registrar el mismo
   correo dos veces).
2. Inicio y cierre de sesión (HU-13): un usuario registrado inicia sesión con
   correo y contraseña, y puede cerrar sesión. Toda ruta que modifique tareas
   verifica sesión activa en el backend — no basta con ocultar botones en el
   frontend.
3. Creación de tareas (HU-01): un usuario autenticado crea una tarea con
   título (obligatorio, no vacío), descripción (opcional) y fecha límite
   (opcional). La tarea se crea con estado inicial "pendiente". Se registra el
   actor y el timestamp de creación en un log de auditoría.
4. Listado de tareas (HU-02): un usuario ve el listado de sus propias tareas,
   mostrando título, estado y fecha límite. El listado se puede filtrar por
   estado. Solo aparecen tareas del usuario autenticado — nunca tareas de
   otros usuarios.
5. Cambio de estado (HU-03): un usuario cambia el estado de una tarea entre
   pendiente, en progreso y completada. Las transiciones válidas están
   explícitamente definidas; no se puede pasar de "completada" a "pendiente"
   sin una transición explícita de reapertura (esa transición de reapertura
   queda fuera de este incremento — se especifica en un incremento posterior
   junto con HU-06). Cada cambio de estado queda registrado en el log de
   auditoría.
6. Edición de tareas (HU-04): un usuario edita título, descripción o fecha
   límite de una tarea propia existente. No se permite editar una tarea
   eliminada. Los cambios se validan con las mismas reglas que la creación.

Fuera de alcance explícito de este incremento (se especifican después):
eliminación de tareas (HU-05), reapertura de tareas completadas (HU-06),
prioridad y categorías (HU-07, HU-08), indicación de tareas vencidas (HU-09),
asignación y notificaciones (HU-10, HU-11), recuperación de contraseña
(HU-14), interacción sin recarga de página y drag-and-drop (HU-15, HU-16).
Esta especificación debe ser consistente con la constitución del proyecto:
Flask como único framework backend, separación entre modelos, servicios,
rutas y presentación, contrato de endpoints documentado antes de
implementarse, pruebas automatizadas en rojo antes de implementar la lógica
de dominio, validación y sanitización de toda entrada en el backend
independientemente del frontend, y registro estructurado de toda operación
que modifique el estado de una tarea.
```

### 1.2 Clarificación (`/speckit-clarify`)
* Ejecución interactiva para afinar detalles de validación de correo, transiciones válidas y estructura de sesión.

### 1.3 Plan Técnico (`/speckit-plan`)
```markdown
Genera el plan técnico de implementación para el primer incremento de TaskControl (registro, login/logout, creación, listado, cambio de estado y edición de tareas), siguiendo estrictamente la constitución del proyecto. El plan debe definir:

1. Estructura de carpetas del monolito, separando modelos, servicios, rutas
   (blueprints de Flask) y presentación (plantillas + JavaScript), tal como
   exige el Principio II de la constitución.

2. Modelos de datos con SQLAlchemy: al menos User (correo, hash de
   contraseña) y Task (título, descripción, fecha límite, estado, usuario
   propietario, timestamps de auditoría). Indica las relaciones entre ellos.

3. El contrato de cada endpoint HTTP necesario para las 6 historias de este
   incremento: ruta, método, payload de entrada, payload de salida y códigos
   de error — según exige el Principio III antes de implementar cualquier
   ruta.

4. Estrategia de autenticación y manejo de sesión en Flask (verificación de
   sesión activa en backend en cada endpoint que modifique tareas, no solo
   en el frontend — Principio VII).

5. Estrategia de migraciones con Flask-Migrate/Alembic para crear el esquema
   inicial (Principio VI).

6. Estrategia de logging estructurado para el log de auditoría exigido por
   el Principio VIII: qué campos registra cada evento (actor, acción,
   entidad, timestamp) y dónde se centraliza esa lógica para no duplicarla
   en cada ruta.

7. Estrategia de pruebas: qué se prueba a nivel de modelo/servicio (bloqueante
   según el Principio IV) versus qué se prueba a nivel de ruta HTTP.

No incluyas en el plan nada de las historias fuera de alcance de este
incremento (eliminación, reapertura, prioridad, categorías, asignación,
notificaciones, recuperación de contraseña, interacción sin recarga,
drag-and-drop) — esas se planificarán en incrementos posteriores.
```

### 1.4 Verificación e Implementación
* `/speckit-checklist`: Verificación de integridad y consistencia del plan.
* `/speckit-tasks`: Descomposición en tareas verificables e independientes.
* `/speckit-analyze`: Análisis cruzado de cobertura spec-plan-tasks.
* `/speckit-implement`: Implementación de código y pruebas automatizadas (29 tests aprobados).

---

## Incremento 2: Cierre de Gestión de Tareas y Recuperación de Acceso

**Historias cubiertas:** HU-05 (eliminar tarea), HU-06 (reabrir tarea), HU-14 (recuperar contraseña)  
**Rama:** `implementacion-2`

### 2.1 Especificación (`/speckit-specify`)
```markdown
Especifica el segundo incremento funcional de TaskControl: cierre de la
gestión básica de tareas y recuperación de acceso. Este incremento cubre
HU-05, HU-06 y HU-14 del backlog, y asume que el Incremento 1 (registro,
login/logout, creación, listado, cambio de estado y edición de tareas) ya
está implementado y en producción.

Alcance funcional:

1. Eliminación de tareas (HU-05): un usuario elimina una tarea propia. La
   eliminación es lógica (soft delete), nunca física — la tarea deja de
   aparecer en el listado por defecto pero su registro y su historial de
   auditoría se preservan. No se permite eliminar una tarea que ya fue
   eliminada.

2. Reapertura de tareas (HU-06): un usuario reabre una tarea que había sido
   marcada como completada por error, devolviéndola a un estado activo. La
   reapertura queda registrada en el log de auditoría como un evento
   distinto de la creación original y distinto de un cambio de estado
   ordinario — debe poder distinguirse en el historial que esa tarea fue
   reabierta, no solo "cambiada de estado".

3. Recuperación de contraseña (HU-14): un usuario que olvidó su contraseña
   puede solicitar restablecerla mediante su correo registrado, sin que esto
   revele si ese correo existe o no en el sistema (para no filtrar qué
   correos están registrados). El mecanismo de restablecimiento debe
   invalidar la posibilidad de reutilizarse después de usado una vez o tras
   expirar.

Fuera de alcance explícito de este incremento: prioridad y categorías de
tareas (HU-07, HU-08), indicación de tareas vencidas (HU-09), asignación y
notificaciones (HU-10, HU-11), interacción sin recarga de página y
drag-and-drop (HU-15, HU-16).

Esta especificación debe ser consistente con la constitución del proyecto:
soft delete preserva el log de auditoría (Principio VI), toda transición de
estado queda registrada (Principio VIII), y el mecanismo de recuperación de
contraseña no introduce almacenamiento de secretos en texto plano ni en el
repositorio (Principio VII).
```

### 2.2 Clarificación (`/speckit-clarify`)
* Definición de estrategia para entrega de correos de recuperación (simulación/consola en desarrollo) y tiempo de expiración del token.

### 2.3 Plan Técnico (`/speckit-plan`)
```markdown
Genera el plan técnico de implementación para el Incremento 2 de TaskControl
(eliminación lógica de tareas, reapertura de tareas completadas, recuperación
de contraseña), siguiendo estrictamente la constitución del proyecto y
construyendo sobre los modelos y blueprints ya definidos en el plan del
Incremento 1.

El plan debe definir:

1. Cómo se extiende el modelo Task existente para soportar soft delete (por
   ejemplo, un campo de marca de eliminación con timestamp) sin romper las
   consultas y endpoints ya implementados en el Incremento 1 — el listado de
   tareas (HU-02) debe seguir excluyendo por defecto las eliminadas.

2. Cómo se distingue en el log de auditoría un evento de reapertura de un
   cambio de estado ordinario, y qué transición de estado específica
   habilita esta reapertura sobre la máquina de estados ya definida en el
   Incremento 1.

3. El contrato de los nuevos endpoints HTTP necesarios: eliminar tarea,
   reabrir tarea, solicitar restablecimiento de contraseña, y confirmar
   restablecimiento con el token recibido — ruta, método, payload de
   entrada/salida y códigos de error de cada uno.

4. El modelo de datos y la estrategia de expiración para los tokens de
   restablecimiento de contraseña (vida útil, invalidación tras uso, y cómo
   se evita que un correo no registrado reciba una respuesta distinta a uno
   registrado).

5. Cómo se envía el correo de restablecimiento en este entorno de desarrollo
   (indica si se simula con un log/consola o si se integra un servicio real
   de correo, y justifica la elección según el alcance de un proyecto
   académico).

6. Las migraciones necesarias sobre el esquema existente para los campos
   nuevos (Principio VI), sin romper los datos ya creados por el Incremento 1.

7. Qué pruebas automatizadas son bloqueantes a nivel de modelo/servicio
   (Principio IV): en particular, que una tarea eliminada no aparezca en el
   listado, que no se pueda eliminar dos veces, y que un token de
   restablecimiento usado o expirado sea rechazado.
```

### 2.4 Tareas y Ejecución
* `/speckit-tasks`
* `/speckit-analyze`
* `/speckit-implement`

---

## Incremento 3: Organización y Priorización

**Historias cubiertas:** HU-07 (prioridad), HU-08 (categorías), HU-09 (tareas vencidas)  
**Rama prevista:** `implementacion-3`

### 3.1 Especificación (`/speckit-specify`)
```markdown
Especifica el tercer incremento funcional de TaskControl: organización y
priorización de tareas. Este incremento cubre HU-07, HU-08 y HU-09 del
backlog, y asume que los Incrementos 1 y 2 ya están implementados.

Alcance funcional:

1. Prioridad de tareas (HU-07): toda tarea tiene una prioridad (alta, media,
   baja) con un valor por defecto definido explícitamente. El listado de
   tareas (ya existente desde HU-02) se puede ordenar por prioridad, además
   de los filtros por estado ya existentes. Un usuario puede cambiar la
   prioridad de una tarea propia en cualquier momento.

2. Categorías o proyectos (HU-08): un usuario puede crear categorías para
   agrupar tareas relacionadas. Una tarea pertenece a máximo una categoría
   (o a ninguna). Eliminar una categoría no elimina las tareas que
   pertenecían a ella — quedan sin categoría, nunca se eliminan en cascada.

3. Indicación de tareas vencidas (HU-09): el sistema calcula si una tarea
   está vencida (fecha límite superada y no completada) y lo expone en el
   listado. Este cálculo se hace exclusivamente en el backend, nunca en
   JavaScript, para evitar inconsistencias por zona horaria del cliente. Una
   tarea eliminada o completada nunca se marca como vencida aunque su fecha
   límite haya pasado.

Fuera de alcance explícito de este incremento: asignación y notificaciones
(HU-10, HU-11), interacción sin recarga de página y drag-and-drop (HU-15,
HU-16).

Esta especificación debe ser consistente con la constitución del proyecto:
separación de capas al introducir el nuevo concepto de categoría como
entidad propia (Principio II), y cálculo de vencimiento resuelto en el
backend como parte del contrato de datos que recibe el frontend (Principio
III).
```

### 3.2 Plan Técnico (`/speckit-plan`)
```markdown
Genera el plan técnico de implementación para el Incremento 3 de TaskControl
(prioridad, categorías, indicación de tareas vencidas), siguiendo
estrictamente la constitución del proyecto y construyendo sobre los modelos
y blueprints ya definidos en los planes de los Incrementos 1 y 2.

El plan debe definir:

1. Cómo se extiende el modelo Task para incluir prioridad (con su valor por
   defecto) y una relación opcional a una nueva entidad Category.

2. El modelo de datos de Category: campos mínimos, y la regla de que
   eliminar una categoría desvincula sus tareas en vez de eliminarlas
   (define si esto se implementa con una clave foránea nullable y qué
   ocurre a nivel de base de datos al eliminar la categoría).

3. El contrato de los nuevos endpoints: cambiar prioridad de una tarea,
   crear/listar/eliminar categorías, asignar una tarea a una categoría, y
   cómo se extiende el endpoint de listado de tareas (ya existente) para
   soportar ordenamiento por prioridad y filtrado por categoría sin romper
   los filtros por estado ya implementados.

4. Dónde y cómo se calcula el indicador de "vencida" — como un campo
   derivado en la respuesta del endpoint de listado, nunca persistido como
   columna que haya que mantener sincronizada, y explícitamente excluyendo
   tareas completadas o eliminadas de ese cálculo.

5. Las migraciones necesarias para los campos y la tabla nuevos (Principio
   VI), sin romper los datos existentes de tareas creadas en incrementos
   anteriores (todas deben quedar con la prioridad por defecto).

6. Qué pruebas automatizadas son bloqueantes a nivel de modelo/servicio
   (Principio IV): en particular, que el ordenamiento por prioridad sea
   correcto, que eliminar una categoría no elimine sus tareas, y que una
   tarea completada nunca se marque como vencida.
```

---

## Incremento 4: Colaboración

**Historias cubiertas:** HU-10 (asignación), HU-11 (notificación interna)  
**Rama prevista:** `implementacion-4`

### 4.1 Especificación (`/speckit-specify`)
```markdown
Especifica el cuarto incremento funcional de TaskControl: colaboración entre
usuarios. Este incremento cubre HU-10 y HU-11 del backlog, y asume que los
Incrementos 1 a 3 ya están implementados.

Alcance funcional:

1. Asignación de tareas (HU-10): un usuario puede asignar una tarea propia a
   otro usuario existente del sistema (nunca a un correo que no esté
   registrado). El usuario asignado ve esa tarea en su propio listado de
   tareas, de la misma forma que ve las suyas propias — define si el
   listado distingue visualmente entre "mis tareas creadas" y "tareas
   asignadas a mí", o si se presentan sin distinción. El cambio de
   asignación queda registrado en el log de auditoría.

2. Notificación interna de asignación (HU-11): cuando a un usuario se le
   asigna una tarea, recibe una notificación dentro de la aplicación (no por
   correo ni push externo) que puede consultar sin tener que revisar
   manualmente el listado completo de tareas. Define cómo se marca una
   notificación como leída y si persiste tras leerse o se descarta.

Fuera de alcance explícito de este incremento: interacción sin recarga de
página y drag-and-drop (HU-15, HU-16), que se especifican en el incremento
final.

Esta especificación debe ser consistente con la constitución del proyecto:
toda reasignación queda auditada con actor y timestamp (Principio VIII), y
la verificación de que solo se puede asignar a usuarios existentes se valida
en el backend, no solo en un selector del frontend (Principio VII).
```

### 4.2 Plan Técnico (`/speckit-plan`)
```markdown
Genera el plan técnico de implementación para el Incremento 4 de TaskControl
(asignación de tareas a otros usuarios, notificaciones internas de
asignación), siguiendo estrictamente la constitución del proyecto y
construyendo sobre los modelos y blueprints ya definidos en los planes
anteriores.

El plan debe definir:

1. Cómo se extiende el modelo Task para distinguir entre el usuario
   propietario/creador y el usuario asignado (si son campos separados o el
   mismo campo se reinterpreta — justifica la decisión).

2. El modelo de datos de Notification: a quién pertenece, a qué tarea
   referencia, su estado de leída/no leída, y su timestamp de creación.

3. El contrato de los nuevos endpoints: asignar/reasignar una tarea a un
   usuario, listar notificaciones del usuario autenticado, marcar una
   notificación como leída, y cómo se extiende el endpoint de listado de
   tareas para incluir las asignadas al usuario actual además de las que
   creó.

4. Cómo y en qué punto del flujo de asignación se crea la notificación
   correspondiente (por ejemplo, como parte del mismo servicio que procesa
   la asignación, para que ambas operaciones sean atómicas).

5. La validación en backend de que el usuario destino de una asignación
   exista y esté activo, rechazando explícitamente asignaciones a correos
   no registrados (Principio VII).

6. Las migraciones necesarias para los campos y la tabla nuevos (Principio
   VI).

7. Qué pruebas automatizadas son bloqueantes a nivel de modelo/servicio
   (Principio IV): en particular, que asignar una tarea genere exactamente
   una notificación, que no se pueda asignar a un usuario inexistente, y que
   el listado del usuario asignado incluya la tarea.
```

---

## Incremento 5: Interfaz e Interacción (JavaScript)

**Historias cubiertas:** HU-15 (completar sin recargar), HU-16 (drag-and-drop)  
**Rama prevista:** `implementacion-5`

### 5.1 Especificación (`/speckit-specify`)
```markdown
Especifica el quinto y último incremento funcional de TaskControl: mejoras
de interacción en el frontend mediante JavaScript. Este incremento cubre
HU-15 y HU-16 del backlog, y asume que todos los incrementos anteriores (1 a
4) ya están implementados y expuestos como endpoints HTTP con contrato
definido.

Alcance funcional:

1. Completar tareas sin recargar la página (HU-15): desde el listado de
   tareas, un usuario marca una tarea como completada mediante una
   interacción de JavaScript que llama al endpoint de cambio de estado ya
   existente (del Incremento 1), sin recargar la página completa. Si la
   petición al backend falla, la interfaz revierte el cambio visual
   mostrado y presenta un mensaje de error al usuario — nunca debe quedar
   la interfaz mostrando un estado que el backend no confirmó.

2. Reordenar tareas arrastrándolas (HU-16): un usuario reordena
   visualmente sus tareas en el listado mediante arrastrar y soltar
   (drag and drop). El nuevo orden se persiste en el backend inmediatamente
   después de soltar el elemento, de forma que si el usuario recarga la
   página el orden se mantiene.

Como este es el incremento final de JavaScript, no introduce ningún
endpoint nuevo de backend — reutiliza exclusivamente los contratos ya
definidos en incrementos anteriores (cambio de estado) y requiere, como
único elemento nuevo de backend, un campo de orden persistente por tarea
para HU-16.

Esta especificación debe ser consistente con la constitución del proyecto:
no se introduce ningún framework SPA (React, Vue, Angular) salvo
justificación explícita, manteniéndose en JavaScript vanilla o una librería
ligera de interactividad (restricción técnica del stack), y toda llamada al
backend sigue el contrato de endpoints ya documentado (Principio III).
```

### 5.2 Plan Técnico (`/speckit-plan`)
```markdown
Genera el plan técnico de implementación para el Incremento 5 de TaskControl
(completar tareas sin recargar la página, reordenar tareas con
drag-and-drop), siguiendo estrictamente la constitución del proyecto.

El plan debe definir:

1. La estrategia de JavaScript para la interacción sin recarga: si se usa
   fetch nativo contra el endpoint de cambio de estado ya existente, qué
   maneja la respuesta de error, y cómo se revierte visualmente el cambio
   optimista en caso de fallo — justifica por qué no se introduce ningún
   framework adicional, según la restricción técnica del stack.

2. La librería o técnica elegida para drag-and-drop (nativa del navegador
   con la API de Drag and Drop, o una librería ligera si se justifica), y
   por qué no excede el límite de "sin framework SPA pesado" de la
   constitución.

3. El único cambio de backend necesario: un campo de orden persistente en
   el modelo Task, y el contrato del endpoint (nuevo o extendido) que
   recibe el nuevo orden tras soltar un elemento — ruta, método, payload de
   entrada/salida y códigos de error.

4. Cómo se evita que dos usuarios reordenando sus propias tareas en
   paralelo generen inconsistencias (dado que el orden es por usuario, no
   global, confirma que la validación de propiedad de cada tarea se aplica
   igual que en los endpoints anteriores — Principio VII).

5. La migración necesaria para el campo de orden (Principio VI), con un
   valor por defecto coherente para las tareas ya existentes de incrementos
   anteriores.

6. Qué pruebas automatizadas son bloqueantes: a nivel de servicio, que
   persistir un nuevo orden actualice correctamente los valores de todas
   las tareas afectadas; a nivel de JavaScript, que una respuesta de error
   del backend revierta el estado visual (puede probarse manualmente si no
   hay infraestructura de pruebas de frontend en el proyecto — indícalo
   explícitamente si ese es el caso).
```

---

## Prompts de Soporte, Git y Calidad

### Control de Versiones (Git)
* **Vincular repositorio remoto y subir Incremento 1:**
  ```bash
  git remote add origin https://github.com/Jhoan2626/Proyecto_TaskBoard.git
  git fetch origin
  git checkout -b implementacion-1
  git push -u origin implementacion-1
  ```
* **Crear rama de trabajo para Incremento 2:**
  ```bash
  git checkout -b implementacion-2
  ```

### Validación y Ejecución
* **Ejecución de migraciones:**
  ```bash
  flask db upgrade
  ```
* **Ejecución de pruebas automatizadas:**
  ```bash
  pytest -v
  ```
* **Ejecución de servidor local:**
  ```bash
  flask run
  ```

---

## Plantilla para Nuevos Registros

Para registrar nuevos prompts a medida que avance el desarrollo, utiliza la siguiente estructura:

```markdown
### [Nombre del Prompt o Acción]
* **Fecha:** YYYY-MM-DD
* **Comando o Herramienta:** (ej. /speckit-specify, /speckit-plan, prompt libre)
* **Objetivo:** Descripción concisa del resultado esperado.
* **Prompt:**
> [Texto del prompt aquí]
* **Resultado o Artefactos Generados:**
  - Enlaces o nombres de archivos creados/modificados.
```
