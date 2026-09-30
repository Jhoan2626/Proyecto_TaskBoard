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


6. Correr la constitución del proyecto:
	- Comando /speckit-constitution (Prompt constitucion_gestor_tareas.txt)

7. Correr la especificación del primer incremento del Backlog
	- Comando /speckit-specify (Prompt specify_increment_1.txt)

8. Correr la clarificación del incremento
	- Comando /speckit-clarify (Normalmente no requiere de prompt)

9. Correr el plan. Conviene darle contexto explícito, porque el plan traduce la especificación en decisiones técnicas concretas (estructura de carpetas, modelos, endpoints) y sin guía el agente puede tomar decisiones que no cuadren con la constitución.
	-  Comando /speckit-plan (Prompt plan_increment_1.txt)

10. Revisa tú mismo el plan generado antes de seguir: ¿respeta la estructura de carpetas del Principio II? ¿El esquema de User y Task tiene sentido? ¿Los endpoints cubren las 6 historias sin inventar funcionalidad de fuera de alcance? No avances a tasks si algo aquí no te convence  es mucho más barato corregir el plan que corregir código ya generado.

11.Comando: /speckit-checklist esto es opcional pero recomendable para verificar que el plan este completo.

12. Comando: /speckit-tasks Convierte el plan en unidades de trabajo pequeñas y verificables independientemente se supone que cada tarea debería corresponder a algo que se pueda implementar y probar de forma aislada

13. Comando: /speckit-analyze Antes de generar código, corre este análisis cruzado, se valida que no haya un requisito de la spec que el plan ignoró, o una tarea que no corresponde a ninguna historia. Es el punto de control más importante de todo el flujo, justo antes de que el agente empiece a escribir código real.

14. Comando: /speckit-implement. Con todo validado, ejecuta la implementación. Según la disciplina test-first de la constitución, cada tarea debería venir con su prueba.




