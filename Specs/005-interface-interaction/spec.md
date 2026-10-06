# Incremento 5 — Interfaz e interacción

## Historias

### HU-15 — Completar tareas sin recargar

Como usuario autenticado, quiero marcar como completada una tarea en progreso
desde el tablero sin recargar la página.

**Criterios de aceptación**

- La interfaz envía el estado `completed` al endpoint existente
  `POST /tasks/<id>/status` mediante `fetch`.
- El estado visible solo permanece actualizado si el servidor confirma la
  transición.
- Ante un error HTTP o de red, la interfaz restaura el badge y el control
  anteriores y muestra un mensaje accesible.

### HU-16 — Reordenar tareas propias

Como usuario autenticado, quiero ordenar mis tareas arrastrándolas en el
tablero y conservar ese orden al volver a cargarlo.

**Criterios de aceptación**

- Se usa la API nativa de Drag and Drop, sin framework SPA ni dependencia.
- El orden manual solo se ofrece en la vista completa de tareas creadas por
  el usuario, sin filtros que oculten tareas ni ordenamiento por prioridad.
- El orden se persiste inmediatamente con `POST /tasks/reorder`.
- El backend solo acepta una permutación completa de tareas activas propiedad
  del usuario autenticado; tareas asignadas, ajenas, eliminadas, incompletas o
  duplicadas no pueden alterar el orden guardado.
- Al fallar la petición, el navegador restaura el orden anterior y avisa al
  usuario.

## Restricciones

- Se conserva Flask/Jinja y JavaScript vanilla.
- Se reutiliza el contrato de estado existente; el único cambio de esquema es
  `tasks.position`, con valor inicial ordenado por fecha de creación para
  conservar el comportamiento existente.
