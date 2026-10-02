# TaskControl — Prompts de Spec Kit para los Incrementos 2 a 5

Este documento complementa el Incremento 1 (HU-01 a HU-04 + HU-12–HU-13, ya
especificado) con los cuatro incrementos restantes del backlog. Cada uno
incluye el prompt de `/speckit-specify` y, a continuación, el prompt de
`/speckit-plan` correspondiente.

**Orden recomendado**: seguir la numeración de incrementos tal como está, ya
que cada uno asume que el anterior ya quedó implementado y probado.

---

## Incremento 2 — Cierre de gestión de tareas y recuperación de acceso

**Historias cubiertas**: HU-05 (eliminar tarea), HU-06 (reabrir tarea),
HU-14 (recuperar contraseña)

### Prompt de `/speckit-specify`

```
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

### Prompt de `/speckit-plan`

```
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

---

## Incremento 3 — Organización y priorización

**Historias cubiertas**: HU-07 (prioridad), HU-08 (categorías), HU-09
(indicación de tareas vencidas)

### Prompt de `/speckit-specify`

```
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

### Prompt de `/speckit-plan`

```
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

## Incremento 4 — Colaboración

**Historias cubiertas**: HU-10 (asignación), HU-11 (notificación interna)

### Prompt de `/speckit-specify`

```
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

### Prompt de `/speckit-plan`

```
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

## Incremento 5 — Interfaz e interacción (JavaScript)

**Historias cubiertas**: HU-15 (completar sin recargar), HU-16
(drag-and-drop)

### Prompt de `/speckit-specify`

```
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

### Prompt de `/speckit-plan`

```
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

## Resumen de incrementos

| Incremento | Historias | Épica(s) |
|---|---|---|
| 1 (ya hecho) | HU-01 a HU-04, HU-12, HU-13 | Gestión de tareas + Cuentas y acceso |
| 2 | HU-05, HU-06, HU-14 | Gestión de tareas (cierre) + Cuentas y acceso (cierre) |
| 3 | HU-07, HU-08, HU-09 | Organización y priorización |
| 4 | HU-10, HU-11 | Colaboración |
| 5 | HU-15, HU-16 | Interfaz e interacción (JavaScript) |

**Recomendación**: correr `/speckit-clarify` antes de `/speckit-plan` en cada
incremento — varias decisiones quedaron deliberadamente abiertas en estas
especificaciones (por ejemplo, cómo se distingue "mis tareas" de "tareas
asignadas a mí" en el Incremento 4) para que el propio proceso de
clarificación las resuelva con el agente, en vez de que queden fijadas de
antemano sin que el estudiante participe en esa decisión.
