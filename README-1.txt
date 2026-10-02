##Instalación del SPECKIT

##Pre-requisitos:

- Python instalado - comando: python --version
- uv instalado - comando: uv --version	
- pip instalado - comando: pip --versión
- git instalado - comando: git --version

Si algún requisito no se cumple se debe instalar la herramienta correspondiente y verificas las variables de entorno de la sesión del sistema operativo.

##Instalación del Speckit

Usa el comando:
uv tool install specify-cli --from git+https://github.com/github/spec-kit.git


##Creación del proyecto para Antigravity

1. Crea la carpeta del proyecto

2. Abrir VsCode desde la carpeta

3. Subir el entorno virtual del Python
	- Comando: python -m venv venv
Este comando deberá crear la carpeta venv en el workspace del proyecto

3.1 Activar el entorno virtual 
	- Se posicionan en el directorio del proyecto y le indican el comando:
	   venv\Scripts\activate
       

4. Verificar el entorno de VSCode 	
	- Ctrl+Shift+P → escribe 'Python: Select Interpreter' → elige el que esté dentro de 
	.\venv\Scripts\python.exe. Esto le dice a VS Code (y a todas sus extensiones, incluido
	 AGY) cuál Python es el del proyecto.

5. Crear el proyecto Speckit específico para AGY
	- Comando: specify init . --integration agy --script ps --force 

5.1. Copiar el archivo backlog.md /.specify/memory


En la carpeta del proyecto van a abrir la consola de Antigravity con el comando agy, esto lo pueden hacer dentro del mismo entorno de VS Code o por la terminal normal del sistema operativo, en cuyo caso antes de ejecutar el agy, deben estar seguros de que se encuentran en la carpeta del proyecto. Los comandos descritos a continuación se ejecutan en la consola de Antigravity.


6. Correr la constitución del proyecto:
	- Comando: /speckit-constitution Crea la constitución del proyecto TaskControl, una aplicación de control de tareas construida con arquitectura monolítica: backend en Python con Flask, y JavaScript del lado del cliente para interactividad, sin frontend framework pesado por defecto.

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


7. Correr la especificación del primer incremento del Backlog
	- Comando: /speckit-specify Especifica el primer incremento funcional de TaskControl: gestión básica de
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


8. Correr la clarificación del incremento
	- Comando: /speckit-clarify (Normalmente no requiere de prompt)

9. Correr el plan. Conviene darle contexto explícito, porque el plan traduce la especificación en decisiones técnicas concretas (estructura de carpetas, modelos, endpoints) y sin guía el agente puede tomar decisiones que no cuadren con la constitución.

	-  Comando: /speckit-plan Genera el plan técnico de implementación para el primer incremento de TaskControl (registro, login/logout, creación, listado, cambio de estado y edición de tareas), siguiendo estrictamente la constitución del proyecto. El plan debe definir:

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



10. Revisa tú mismo el plan generado antes de seguir: ¿respeta la estructura de carpetas del Principio II? ¿El esquema de User y Task tiene sentido? ¿Los endpoints cubren las 6 historias sin inventar funcionalidad de fuera de alcance? No avances a tasks si algo aquí no te convence  es mucho más barato corregir el plan que corregir código ya generado.

11.Comando: /speckit-checklist esto es opcional pero recomendable para verificar que el plan este completo.

12. Comando: /speckit-tasks Convierte el plan en unidades de trabajo pequeñas y verificables independientemente se supone que cada tarea debería corresponder a algo que se pueda implementar y probar de forma aislada

13. Comando: /speckit-analyze Antes de generar código, corre este análisis cruzado, se valida que no haya un requisito de la spec que el plan ignoró, o una tarea que no corresponde a ninguna historia. Es el punto de control más importante de todo el flujo, justo antes de que el agente empiece a escribir código real.

14. Comando: /speckit-implement. Con todo validado, ejecuta la implementación. Según la disciplina test-first de la constitución, cada tarea debería venir con su prueba.

15. Una vez termine la implementación del primer incremento van a validar el resultado del desarrollo para ello deben hacer lo siguiente: 
	-  En la consola de comando (Power Shell - Command) verificar que el entorno virtual de Python esta activo en caso de no estar activo lo deben 
	   activar con el comando venv\Scripts\activate
	-  Verificar que en la carpeta del proyecto exista el archivo requirements.txt y ejecutar pip install -r requirements.txt esto garantiza
	   que no haya dependencias faltantes en el proyecto
	-  Van a ejecutar las migraciones con el comando flask db upgrade
	-  Por último se ejecuta flask run, esto debería levantar el servidor web en la URL http://127.0.0.1:5000 para validar la funcionalidad del
	   desarrollo
	-  Por último vamos a validar la ejecución de las pruebas, esto lo debió realizar el agente pero no esta demás que hagamos las validaciones 
	   para comprobar, en caso de que exista alguna prueba fallida se debe indicar al agente para que se corrija (No se interviene el código por
	   parte nuestra) esta comprobación se hace con el comando en la consola de Powershell o del Command 
	   Comando: pytest -v


16. Lo que sigue es continuar con los demás incrementos repitiendo el ciclo para cada uno de ellos:
	-  /speckit-specify
	-  /speckit-clarify
	-  /speckit-plan
	-  /speckit-checklist (Opcional)
	-  /speckit-tasks 
	-  /speckit-analyze
	-  /speckit-implement 

Tengan en cuenta que ya no se hace el /speckit-constitution 



