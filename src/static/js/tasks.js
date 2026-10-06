/**
 * TaskControl - Interacciones ligeras del tablero sin frameworks.
 */

document.addEventListener("DOMContentLoaded", () => {
    const message = document.querySelector("#task-interaction-message");

    function announce(text, kind = "danger") {
        if (!message) {
            return;
        }
        message.textContent = text;
        message.className = `alert alert-${kind}`;
        message.hidden = false;
    }

    async function readResponse(response) {
        try {
            return await response.json();
        } catch {
            return null;
        }
    }

    document.querySelectorAll(".js-status-form").forEach((form) => {
        const statusInput = form.querySelector('input[name="new_status"]');
        if (!statusInput || statusInput.value !== "completed") {
            return;
        }

        form.addEventListener("submit", async (event) => {
            event.preventDefault();
            if (!confirm("¿Desea marcar esta tarea como completada?")) {
                return;
            }

            const card = form.closest(".task-card");
            const badge = card?.querySelector(".task-status");
            const button = event.submitter || form.querySelector('button[type="submit"]');
            if (!card || !badge || !button) {
                announce("No se pudo actualizar la tarea en esta página. Recargue e inténtelo de nuevo.");
                return;
            }

            const oldBadgeText = badge.textContent;
            const oldBadgeClass = badge.className;
            badge.textContent = "Completada";
            badge.className = "badge badge-completed task-status";
            button.disabled = true;

            try {
                const response = await fetch(form.action, {
                    method: "POST",
                    headers: {
                        "Accept": "application/json",
                        "Content-Type": "application/json",
                    },
                    credentials: "same-origin",
                    body: JSON.stringify({ new_status: "completed" }),
                });
                const result = await readResponse(response);
                if (!response.ok || result?.status !== "completed") {
                    throw new Error(result?.error || "El servidor no confirmó el cambio de estado.");
                }

                card.dataset.status = "completed";
                const reopenForm = document.createElement("form");
                reopenForm.method = "POST";
                reopenForm.action = card.dataset.reopenUrl;
                reopenForm.style.display = "inline";
                const reopenButton = document.createElement("button");
                reopenButton.type = "submit";
                reopenButton.className = "btn btn-sm btn-warning";
                reopenButton.textContent = "↩ Reabrir";
                reopenForm.append(reopenButton);
                form.replaceWith(reopenForm);
                card.querySelector('.task-actions a[href*="/edit"]')?.remove();

                if (new URL(window.location.href).searchParams.get("status") === "in_progress") {
                    card.remove();
                }
                announce("La tarea se marcó como completada.", "success");
            } catch (error) {
                badge.textContent = oldBadgeText;
                badge.className = oldBadgeClass;
                button.disabled = false;
                announce(error.message || "No se pudo actualizar la tarea. Inténtelo de nuevo.");
            }
        });
    });

    const grid = document.querySelector('.task-grid[data-reorder-enabled="true"]');
    if (!grid) {
        return;
    }

    let draggedCard = null;
    let originalOrder = null;
    let dropped = false;

    grid.addEventListener("dragstart", (event) => {
        const handle = event.target.closest(".task-drag-handle");
        if (!handle || grid.dataset.reorderPending === "true") {
            event.preventDefault();
            return;
        }

        draggedCard = handle.closest(".task-card");
        originalOrder = Array.from(grid.querySelectorAll(".task-card"));
        dropped = false;
        if (draggedCard) {
            draggedCard.classList.add("task-card-dragging");
            event.dataTransfer.effectAllowed = "move";
            event.dataTransfer.setData("text/plain", draggedCard.dataset.taskId);
        }
    });

    grid.addEventListener("dragover", (event) => {
        if (!draggedCard) {
            return;
        }

        const target = event.target.closest(".task-card");
        if (!target) {
            if (event.target === grid) {
                event.preventDefault();
                grid.append(draggedCard);
            }
            return;
        }
        if (target === draggedCard) {
            return;
        }

        event.preventDefault();
        const bounds = target.getBoundingClientRect();
        const insertBefore = event.clientY < bounds.top + bounds.height / 2;
        grid.insertBefore(draggedCard, insertBefore ? target : target.nextElementSibling);
    });

    grid.addEventListener("drop", (event) => {
        if (!draggedCard || !originalOrder) {
            return;
        }

        event.preventDefault();
        dropped = true;
        const previousOrder = originalOrder;
        const taskIds = Array.from(grid.querySelectorAll(".task-card"))
            .map((card) => Number(card.dataset.taskId));
        const previousIds = previousOrder.map((card) => Number(card.dataset.taskId));
        if (taskIds.some((id, index) => id !== previousIds[index])) {
            void persistOrder(grid, taskIds, previousOrder, announce);
        }
    });

    grid.addEventListener("dragend", () => {
        if (draggedCard) {
            draggedCard.classList.remove("task-card-dragging");
        }
        if (!dropped && originalOrder) {
            originalOrder.forEach((card) => grid.append(card));
        }
        draggedCard = null;
        originalOrder = null;
        dropped = false;
    });
});

async function persistOrder(grid, taskIds, previousOrder, announce) {
    grid.dataset.reorderPending = "true";
    try {
        const response = await fetch(grid.dataset.reorderUrl, {
            method: "POST",
            headers: {
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            credentials: "same-origin",
            body: JSON.stringify({ task_ids: taskIds }),
        });
        let result = null;
        try {
            result = await response.json();
        } catch {
            result = null;
        }
        const confirmedOrder = Array.isArray(result?.task_ids)
            && result.task_ids.length === taskIds.length
            && result.task_ids.every((id, index) => id === taskIds[index]);
        if (!response.ok || !confirmedOrder) {
            throw new Error(result?.error || "El servidor no confirmó el nuevo orden.");
        }
        announce("El orden de las tareas se guardó.", "success");
    } catch (error) {
        previousOrder.forEach((card) => grid.append(card));
        announce(error.message || "No se pudo guardar el orden. Se restauró el orden anterior.");
    } finally {
        delete grid.dataset.reorderPending;
    }
}
