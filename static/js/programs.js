let programRoutinesSortable = null;

function getRoutinesCatalog() {
    const el = document.getElementById("routines-catalog");
    if (!el) {
        return [];
    }
    return JSON.parse(el.textContent);
}

function getRoutineCatalogEntry(routineId) {
    const id = String(routineId);
    return getRoutinesCatalog().find((entry) => String(entry.id) === id);
}

function exerciseCountLabel(exerciseCount) {
    if (exerciseCount) {
        return `${exerciseCount} exercises`;
    }
    return "no exercises";
}

function routineRowExists(routineId) {
    const container = document.getElementById("program-routines-sortable");
    if (!container) {
        return false;
    }
    return container.querySelector(`.program-routine-row[data-routine-id="${routineId}"]`) !== null;
}

function fillRoutineRow(row, entry) {
    row.dataset.routineId = String(entry.id);
    row.querySelector("[data-slot='routine-link']").href = `/routines/${entry.id}/`;
    row.querySelector("[data-slot='routine-name']").textContent = entry.name;
    row.querySelector("[data-slot='exercise-count']").textContent = exerciseCountLabel(entry.exercise_count);
}

function appendRoutineRow(routineId) {
    const entry = getRoutineCatalogEntry(routineId);
    const template = document.getElementById("program-routine-row-template");
    const container = document.getElementById("program-routines-sortable");
    if (!entry || routineRowExists(routineId) || !template || !container) {
        return;
    }
    const row = template.content.querySelector(".program-routine-row").cloneNode(true);
    fillRoutineRow(row, entry);
    container.appendChild(row);
}

function removeAddRoutineOption(routineId) {
    const select = document.getElementById("program-add-routine");
    const option = select.querySelector(`option[value="${routineId}"]`);
    if (option) {
        option.remove();
    }
}

function restoreAddRoutineOption(routineId) {
    const entry = getRoutineCatalogEntry(routineId);
    if (!entry) {
        return;
    }
    const select = document.getElementById("program-add-routine");
    if (select.querySelector(`option[value="${entry.id}"]`)) {
        return;
    }
    const option = document.createElement("option");
    option.value = String(entry.id);
    option.textContent = entry.name;
    select.appendChild(option);
}

function initProgramRoutinesSortable() {
    const container = document.getElementById("program-routines-sortable");
    if (!container || typeof Sortable === "undefined") {
        return;
    }
    if (programRoutinesSortable) {
        programRoutinesSortable.destroy();
        programRoutinesSortable = null;
    }
    programRoutinesSortable = new Sortable(container, {
        draggable: ".program-routine-row",
        animation: 150,
    });
}

function addProgramRoutine(req_event) {
    const select = req_event.currentTarget;
    const routineId = select.value;
    if (!routineId) {
        return;
    }
    appendRoutineRow(routineId);
    removeAddRoutineOption(routineId);
    select.value = "";
    initProgramRoutinesSortable();
}

function removeProgramRoutine(req_event) {
    const row = req_event.currentTarget.closest(".program-routine-row");
    if (!row) {
        return;
    }
    const routineId = row.dataset.routineId;
    row.remove();
    restoreAddRoutineOption(routineId);
    initProgramRoutinesSortable();
}

function saveProgram(req_event) {
    const trigger = req_event.currentTarget;
    const ids = [...document.querySelectorAll("#program-routines-sortable .program-routine-row")]
        .map((row) => row.dataset.routineId)
        .join(",");
    trigger.setAttribute("data-routine-ids", ids);
    sendWsRequest("programs/update_program", trigger).then((response) => {
        if (response.status === 302 && response.headers && response.headers.length) {
            window.location.href = response.headers[0][1];
        }
    });
}

document.addEventListener("DOMContentLoaded", initProgramRoutinesSortable);
