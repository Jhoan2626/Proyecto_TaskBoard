# Plan técnico — Incremento 5

## Diseño

### Completar tareas

`src/static/js/tasks.js` intercepta únicamente el formulario cuya transición
es a `completed`. Antes de llamar al backend actualiza optimistamente el badge;
usa `fetch` con `Accept: application/json`, `Content-Type: application/json` y
credenciales same-origin. Solo considera éxito una respuesta HTTP exitosa que
confirme `status: completed`. La respuesta fallida, inválida o la excepción de
red restaura texto y clases previos, habilita el control y presenta un mensaje
en una región `aria-live`. Si el servidor confirma, se reemplaza el control de
completar por el de reapertura ya existente y se actualiza el estado visible.

### Orden manual

Se utiliza la API nativa HTML Drag and Drop. El control de arrastre solo se
renderiza al ver todas las tareas propias (`scope=mine`) sin filtro de estado,
categoría ni prioridad. Así el navegador siempre envía al servidor el conjunto
completo de tareas que se pueden ordenar en esa vista.

`POST /tasks/reorder` requiere JSON `{ "task_ids": [<id>, ...] }` y responde
`200 { "message": "...", "task_ids": [...] }`. El backend rechaza un cuerpo o
orden inválido con `400`, identificadores ajenos con `403` y una sesión ausente
con `401`. Solo acepta cada ID activo propio exactamente una vez. La
actualización de todas las posiciones se confirma en una transacción. Los
órdenes de propietarios distintos no comparten registros; operaciones
concurrentes de usuarios distintos no se afectan. Para solicitudes
concurrentes del mismo propietario, cada operación válida es una permutación
completa y la última transacción confirmada determina el orden.

### Persistencia y compatibilidad

`Task.position` es entero no nulo con default `0`. La migración Alembic añade
la columna, inicializa las tareas existentes por propietario en el mismo orden
que el listado anterior (`created_at DESC`, `id DESC`) y luego fija default y
not-null. Las nuevas tareas reciben posición anterior a las existentes para
mantener el comportamiento de mostrar primero las tareas recién creadas. La
consulta conserva orden estable por posición, fecha e ID; el ordenamiento por
prioridad existente sigue prevaleciendo cuando se solicita.

## Validación

- Pruebas unitarias: persistencia de orden, posiciones consecutivas, rechazo
  de IDs ajenos, orden incompleto y duplicados.
- Pruebas de integración: respuesta JSON existente al cambiar estado, guardado
  del orden y rechazos de autorización/validación.
- El repositorio no dispone de runner automatizado de JavaScript. Completar una
  tarea y arrastrar tareas con el backend disponible se validan manualmente:
  comprobar persistencia tras recargar y simular respuesta HTTP fallida para
  comprobar la reversión visual y el mensaje.
