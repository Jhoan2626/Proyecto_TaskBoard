# Tareas de implementación — Incremento 5

**Rama**: `implementacion-5` | **Historias**: HU-15, HU-16

## Fase 1: Contratos y pruebas bloqueantes

- [X] T501 Agregar pruebas de servicio para persistencia de orden, IDs ajenos,
  órdenes incompletos y duplicados en `tests/unit/test_services.py`.
- [X] T502 Agregar pruebas HTTP para cambio de estado JSON, persistencia de orden
  y validación/propiedad en `tests/integration/test_task_routes.py`.

## Fase 2: Persistencia y servicio

- [X] T503 Agregar `Task.position` y migración Alembic con backfill por usuario
  conservando el orden existente.
- [X] T504 Persistir posición inicial de tareas nuevas y ordenar el listado por
  posición, conservando filtros y ordenamiento por prioridad.
- [X] T505 Implementar `TaskService.reorder_user_tasks` con validación de
  permutación completa, propiedad, tareas activas y commit único.
- [X] T506 Exponer `POST /tasks/reorder` con contrato JSON y códigos de error
  para autenticación, validación y propiedad.

## Fase 3: Interacción de interfaz

- [X] T507 Añadir actualización de estado completado vía `fetch`, confirmación
  del servidor, reversión ante errores y anuncio accesible en `tasks.js`.
- [X] T508 Añadir drag-and-drop nativo, persistencia inmediata y restauración
  del orden anterior ante errores.
- [X] T509 Actualizar `tasks/list.html` y estilos para habilitar el arrastre
  solo en una vista sin filtros que oculte tareas.

## Fase 4: Validación y documentación

- [X] T510 Documentar especificación, contrato HTTP, decisiones y estrategia de
  pruebas manuales en este directorio.
- [X] T511 Ejecutar pruebas específicas y regresión del proyecto, validar
  sintaxis JS y revisar el diff.
