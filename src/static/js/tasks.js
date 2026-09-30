/**
 * TaskControl - JavaScript del lado del cliente
 * Interactividad ligera para confirmaciones y transiciones de estado
 */

document.addEventListener("DOMContentLoaded", () => {
    // Confirmación al completar o cambiar estados
    const forms = document.querySelectorAll("form");
    forms.forEach((form) => {
        const statusInput = form.querySelector('input[name="new_status"]');
        if (statusInput && statusInput.value === "completed") {
            form.addEventListener("submit", (e) => {
                if (!confirm("¿Desea marcar esta tarea como completada? Recuerde que en este incremento no hay reapertura.")) {
                    e.preventDefault();
                }
            });
        }
    });
});
