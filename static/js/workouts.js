/* ── State ───────────────────────────────────── */

let workoutCurrentCardIndex = 0;
let workoutCards = [];
let workoutIndicators = [];
let workoutTouchStartX = 0;
let workoutTouchStartY = 0;
let workoutTouchEndX = 0;
let workoutTouchEndY = 0;
let exerciseViewMode = "detail";
let overviewSortables = [];

/* ── Exercise view mode (detail / overview) ──── */

function applyExerciseViewMode() {
    const detailView = document.getElementById("exercise-detail-view");
    const overviewView = document.getElementById("exercise-overview-view");
    const toggleButtons = document.querySelectorAll(".exercise-view-toggle-btn");

    if (detailView) {
        detailView.classList.toggle("hidden", exerciseViewMode !== "detail");
    }
    if (overviewView) {
        overviewView.classList.toggle("hidden", exerciseViewMode !== "overview");
    }
    toggleButtons.forEach((button) => {
        const isActive = button.dataset.view === exerciseViewMode;
        button.classList.toggle("btn-primary", isActive);
        button.classList.toggle("btn-outline", !isActive);
    });
}

function setExerciseViewToggleDisabled(disabled) {
    document.querySelectorAll(".exercise-view-toggle-btn").forEach((button) => {
        button.disabled = disabled;
    });
}

function refreshExerciseView(view, activeExerciseId) {
    const exerciseUi = document.getElementById("workout-exercise-ui");
    if (!exerciseUi) {
        return;
    }
    const trigger = document.createElement("button");
    trigger.setAttribute("data-session-id", exerciseUi.dataset.sessionId);
    trigger.setAttribute("data-view", view);
    if (view === "detail" && activeExerciseId) {
        trigger.setAttribute("data-active-exercise-id", activeExerciseId);
    }
    const endpoint = `${exerciseUi.dataset.endpointNs}/refresh_exercise_view`;
    setExerciseViewToggleDisabled(true);
    sendWsRequest(endpoint, trigger).then((response) => {
        setExerciseViewToggleDisabled(false);
        if (response.json_content?.target && response.json_content?.html) {
            document.querySelector(response.json_content.target).innerHTML =
                response.json_content.html;
        }
        exerciseViewMode = view;
        if (view === "detail") {
            const activeIndex = response.json_content?.active_exercise_index;
            initWorkoutCardsPage(
                activeIndex != null ? Number(activeIndex) : undefined
            );
        } else {
            applyExerciseViewMode();
            initOverviewSortable();
            initOverviewRowTap();
        }
    });
}

function setExerciseView(req_event) {
    const trigger = req_event.currentTarget;
    const view = trigger.dataset.view;
    if (view !== "detail" && view !== "overview") {
        return;
    }
    if (view === exerciseViewMode) {
        return;
    }

    let activeExerciseId = null;
    if (view === "detail") {
        const currentCard = workoutCards[workoutCurrentCardIndex];
        activeExerciseId = currentCard?.dataset.exerciseId ?? null;
    }
    refreshExerciseView(view, activeExerciseId);
}

/* ── Detail carousel ─────────────────────────── */

function initWorkoutCardsPage(activeIndex) {
    const container = document.getElementById("exercise-card-container");
    if (!container) {
        return;
    }

    workoutCards = Array.from(container.querySelectorAll(".exercise-card"));
    workoutIndicators = Array.from(document.querySelectorAll(".carousel-indicator"));
    if (activeIndex != null) {
        workoutCurrentCardIndex = activeIndex;
    } else if (!workoutCards.length) {
        workoutCurrentCardIndex = 0;
    } else if (workoutCurrentCardIndex > workoutCards.length - 1) {
        workoutCurrentCardIndex = workoutCards.length - 1;
    }
    refreshWorkoutNavState();
    bindWorkoutTouch(container);
    applyExerciseViewMode();
}

function refreshWorkoutNavState() {
    const currentNumber = document.getElementById("current-exercise-num");
    const totalNumber = document.getElementById("total-exercises-num");
    const prevBtn = document.getElementById("prev-exercise");
    const nextBtn = document.getElementById("next-exercise");

    if (!workoutCards.length) {
        if (currentNumber) {
            currentNumber.textContent = "0";
        }
        if (totalNumber) {
            totalNumber.textContent = "0";
        }
        if (prevBtn) {
            prevBtn.disabled = true;
        }
        if (nextBtn) {
            nextBtn.disabled = true;
        }
        return;
    }

    workoutCards.forEach((card, index) => {
        card.classList.toggle("hidden", index !== workoutCurrentCardIndex);
    });

    workoutIndicators.forEach((indicator, index) => {
        indicator.classList.toggle("active", index === workoutCurrentCardIndex);
    });

    if (currentNumber) {
        currentNumber.textContent = String(workoutCurrentCardIndex + 1);
    }
    if (totalNumber) {
        totalNumber.textContent = String(workoutCards.length);
    }
    if (prevBtn) {
        prevBtn.disabled = workoutCurrentCardIndex === 0;
    }
    if (nextBtn) {
        nextBtn.disabled = workoutCurrentCardIndex === workoutCards.length - 1;
    }
}

function setWorkoutCardIndex(nextIndex) {
    if (!workoutCards.length) {
        return;
    }
    if (nextIndex < 0 || nextIndex > workoutCards.length - 1) {
        return;
    }
    workoutCurrentCardIndex = nextIndex;
    refreshWorkoutNavState();
}

function showNextWorkoutCard() {
    setWorkoutCardIndex(workoutCurrentCardIndex + 1);
}

function showPreviousWorkoutCard() {
    setWorkoutCardIndex(workoutCurrentCardIndex - 1);
}

function goToWorkoutCard(req_event) {
    const response = req_event.currentTarget.dataset.exerciseIndex;
    if (response == null) {
        return;
    }
    setWorkoutCardIndex(Number(response));
}

function handleWorkoutSwipe() {
    const dx = workoutTouchStartX - workoutTouchEndX;
    const dy = Math.abs(workoutTouchStartY - workoutTouchEndY);
    if (Math.abs(dx) < 80 || dy > Math.abs(dx)) {
        return;
    }
    if (dx > 0) {
        showNextWorkoutCard();
        return;
    }
    showPreviousWorkoutCard();
}

function bindWorkoutTouch(container) {
    container.addEventListener("touchstart", (req_event) => {
        if (!req_event.touches.length) {
            return;
        }
        workoutTouchStartX = req_event.touches[0].clientX;
        workoutTouchStartY = req_event.touches[0].clientY;
    }, { passive: true });

    container.addEventListener("touchend", (req_event) => {
        if (!req_event.changedTouches.length) {
            return;
        }
        workoutTouchEndX = req_event.changedTouches[0].clientX;
        workoutTouchEndY = req_event.changedTouches[0].clientY;
        handleWorkoutSwipe();
    }, { passive: true });
}

/* ── Overview (sort, reorder, tap) ──── */

const OVERVIEW_TAP_MOVE_THRESHOLD = 16;
const OVERVIEW_DRAG_DELAY_MS = 300;

let overviewSortEngagedThisGesture = false;
let overviewTouchHandled = false;
let overviewWiggleMoveListener = null;

function clearAllOverviewRowArmed() {
    document.querySelectorAll("#exercise-overview-view .overview-row-armed").forEach((el) => {
        el.classList.remove("overview-row-armed");
    });
}

function readOverviewExerciseIds() {
    const ids = [];
    document.querySelectorAll("#exercise-overview-view .exercise-overview-sortable").forEach((container) => {
        container.querySelectorAll(".exercise-overview-row").forEach((row) => {
            ids.push(row.dataset.exerciseId);
        });
    });
    return ids;
}

function persistOverviewExerciseOrder() {
    const exerciseUi = document.getElementById("workout-exercise-ui");
    if (!exerciseUi) {
        return;
    }
    const trigger = document.createElement("button");
    trigger.setAttribute("data-session-id", exerciseUi.dataset.sessionId);
    trigger.setAttribute("data-exercise-ids", readOverviewExerciseIds().join(","));
    sendWsRequest(`${exerciseUi.dataset.endpointNs}/reorder_exercises`, trigger);
}

function initOverviewSortable() {
    if (overviewWiggleMoveListener) {
        document.removeEventListener("touchmove", overviewWiggleMoveListener);
        overviewWiggleMoveListener = null;
    }
    overviewSortables.forEach((instance) => instance.destroy());
    overviewSortables = [];
    document.querySelectorAll("#exercise-overview-view .exercise-overview-sortable").forEach((container) => {
        overviewSortables.push(
            new Sortable(container, {
                draggable: ".exercise-overview-row",
                animation: 150,
                delay: OVERVIEW_DRAG_DELAY_MS,
                delayOnTouchOnly: true,
                touchStartThreshold: 10,
                onChoose(evt) {
                    overviewSortEngagedThisGesture = true;
                    const item = evt.item;
                    item.classList.add("overview-row-armed");
                    if (overviewWiggleMoveListener) {
                        document.removeEventListener("touchmove", overviewWiggleMoveListener);
                    }
                    overviewWiggleMoveListener = () => {
                        clearAllOverviewRowArmed();
                        document.removeEventListener("touchmove", overviewWiggleMoveListener);
                        overviewWiggleMoveListener = null;
                    };
                    document.addEventListener("touchmove", overviewWiggleMoveListener, { passive: true });
                },
                onStart() {
                    clearAllOverviewRowArmed();
                },
                onEnd(evt) {
                    clearAllOverviewRowArmed();
                    if (overviewWiggleMoveListener) {
                        document.removeEventListener("touchmove", overviewWiggleMoveListener);
                        overviewWiggleMoveListener = null;
                    }
                    if (evt.oldIndex === evt.newIndex) {
                        return;
                    }
                    persistOverviewExerciseOrder();
                },
            })
        );
    });
}

function overviewRowTapWithinThreshold(startX, startY, endX, endY) {
    return (
        Math.abs(endX - startX) <= OVERVIEW_TAP_MOVE_THRESHOLD &&
        Math.abs(endY - startY) <= OVERVIEW_TAP_MOVE_THRESHOLD
    );
}

function navigateOverviewRowToDetail(row) {
    refreshExerciseView("detail", row.dataset.exerciseId);
}

function initOverviewRowTap() {
    document.querySelectorAll("#exercise-overview-view .exercise-overview-row").forEach((row) => {
        let tapStartX = 0;
        let tapStartY = 0;
        row.addEventListener("touchstart", (e) => {
            overviewSortEngagedThisGesture = false;
            tapStartX = e.touches[0].clientX;
            tapStartY = e.touches[0].clientY;
        }, { passive: true });
        row.addEventListener("touchend", (e) => {
            const endX = e.changedTouches[0].clientX;
            const endY = e.changedTouches[0].clientY;
            row.classList.remove("overview-row-armed");
            if (overviewSortEngagedThisGesture) {
                return;
            }
            if (!overviewRowTapWithinThreshold(tapStartX, tapStartY, endX, endY)) {
                return;
            }
            overviewTouchHandled = true;
            navigateOverviewRowToDetail(row);
        }, { passive: true });
        row.addEventListener("touchcancel", () => {
            row.classList.remove("overview-row-armed");
        }, { passive: true });
        row.addEventListener("click", () => {
            if (overviewTouchHandled) {
                overviewTouchHandled = false;
                return;
            }
            navigateOverviewRowToDetail(row);
        });
    });
}

/* ── Set modal value pickers ─────────────────── */

const PICKER_ROW_HEIGHT = 44;
const WEIGHT_WINDOW_HALF_STEPS = 40;
const PICKER_SCROLL_DEBOUNCE_MS = 80;

function getPickerHiddenInput(picker) {
    const form = picker.closest("form");
    if (!form) {
        return null;
    }
    const inputId = picker.getAttribute("data-input-id");
    if (inputId) {
        return form.querySelector(`#${inputId}`);
    }
    const kind = picker.getAttribute("data-picker");
    if (kind === "weight") {
        return form.querySelector("#set-modal-weight");
    }
    if (kind === "reps") {
        return form.querySelector("#set-modal-reps");
    }
    return null;
}

function createWeightPickerItem(picker, index) {
    const item = document.createElement("li");
    item.className = "value-picker-item";
    item.dataset.index = String(index);
    item.dataset.value = String(index / 2);
    const unit = picker.getAttribute("data-unit") || "kg";
    item.textContent = `${item.dataset.value} ${unit}`;
    return item;
}

function renderWeightPickerItems(picker, lowIndex, highIndex) {
    const list = picker.querySelector(".value-picker-list");
    list.innerHTML = "";
    for (let index = lowIndex; index <= highIndex; index += 1) {
        list.appendChild(createWeightPickerItem(picker, index));
    }
    picker.dataset.rangeLowIndex = String(lowIndex);
    picker.dataset.rangeHighIndex = String(highIndex);
}

function buildWeightPickerItems(picker, centerIndex) {
    const minIndex = Number(picker.getAttribute("data-min")) * 2;
    const maxIndex = Number(picker.getAttribute("data-max")) * 2;
    if (maxIndex - minIndex <= 80) {
        renderWeightPickerItems(picker, minIndex, maxIndex);
        return;
    }
    const clamped = Math.min(maxIndex, Math.max(minIndex, centerIndex));
    const lowIndex = Math.max(minIndex, clamped - WEIGHT_WINDOW_HALF_STEPS);
    const highIndex = Math.min(maxIndex, clamped + WEIGHT_WINDOW_HALF_STEPS);
    renderWeightPickerItems(picker, lowIndex, highIndex);
}

function createRepsPickerItem(value) {
    const item = document.createElement("li");
    item.className = "value-picker-item";
    item.dataset.value = String(value);
    item.textContent = String(value);
    return item;
}

function buildRepsPickerItems(picker) {
    const min = Number(picker.getAttribute("data-min"));
    const max = Number(picker.getAttribute("data-max"));
    const list = picker.querySelector(".value-picker-list");
    list.innerHTML = "";
    for (let value = min; value <= max; value += 1) {
        list.appendChild(createRepsPickerItem(value));
    }
}

function extendPickerRange(picker, direction) {
    if (picker.getAttribute("data-picker") !== "weight") {
        return;
    }
    const minIndex = Number(picker.getAttribute("data-min")) * 2;
    const maxIndex = Number(picker.getAttribute("data-max")) * 2;
    const list = picker.querySelector(".value-picker-list");
    const windowEl = picker.querySelector(".value-picker-window");
    const lowIndex = Number(picker.dataset.rangeLowIndex);
    const highIndex = Number(picker.dataset.rangeHighIndex);
    if (direction === "up" && lowIndex > minIndex) {
        const newLowIndex = Math.max(minIndex, lowIndex - WEIGHT_WINDOW_HALF_STEPS);
        const addedIndexes = [];
        for (let index = newLowIndex; index < lowIndex; index += 1) {
            addedIndexes.push(index);
        }
        const addedHeight = addedIndexes.length * PICKER_ROW_HEIGHT;
        for (let i = addedIndexes.length - 1; i >= 0; i -= 1) {
            list.insertBefore(createWeightPickerItem(picker, addedIndexes[i]), list.firstChild);
        }
        picker.dataset.rangeLowIndex = String(newLowIndex);
        windowEl.scrollTop += addedHeight;
    }
    if (direction === "down" && highIndex < maxIndex) {
        const newHighIndex = Math.min(maxIndex, highIndex + WEIGHT_WINDOW_HALF_STEPS);
        for (let index = highIndex + 1; index <= newHighIndex; index += 1) {
            list.appendChild(createWeightPickerItem(picker, index));
        }
        picker.dataset.rangeHighIndex = String(newHighIndex);
    }
}

function getCenterPickerItem(picker) {
    const windowEl = picker.querySelector(".value-picker-window");
    const items = picker.querySelector(".value-picker-list").querySelectorAll(".value-picker-item");
    if (!items.length) {
        return null;
    }
    const windowRect = windowEl.getBoundingClientRect();
    const centerY = windowRect.top + windowRect.height / 2;
    let closest = items[0];
    let closestDist = Infinity;
    items.forEach((item) => {
        const itemRect = item.getBoundingClientRect();
        const itemCenter = itemRect.top + itemRect.height / 2;
        const dist = Math.abs(itemCenter - centerY);
        if (dist < closestDist) {
            closestDist = dist;
            closest = item;
        }
    });
    return closest;
}

function updatePickerHighlight(picker) {
    const items = picker.querySelector(".value-picker-list").querySelectorAll(".value-picker-item");
    items.forEach((item) => {
        item.classList.remove("is-center", "is-near");
    });
    const center = getCenterPickerItem(picker);
    if (!center) {
        return;
    }
    center.classList.add("is-center");
    if (center.previousElementSibling) {
        center.previousElementSibling.classList.add("is-near");
    }
    if (center.nextElementSibling) {
        center.nextElementSibling.classList.add("is-near");
    }
}

function scrollItemToCenter(picker, item) {
    const windowEl = picker.querySelector(".value-picker-window");
    const windowRect = windowEl.getBoundingClientRect();
    const itemRect = item.getBoundingClientRect();
    const itemCenter = itemRect.top + itemRect.height / 2;
    const windowCenter = windowRect.top + windowRect.height / 2;
    windowEl.scrollTop += itemCenter - windowCenter;
}

function updateHiddenFromPicker(picker) {
    const item = getCenterPickerItem(picker);
    const hidden = getPickerHiddenInput(picker);
    if (!item || !hidden) {
        return;
    }
    hidden.value = item.dataset.value;
}

function snapPickerToNearest(picker) {
    const item = getCenterPickerItem(picker);
    if (item) {
        scrollItemToCenter(picker, item);
        updateHiddenFromPicker(picker);
        updatePickerHighlight(picker);
    }
}

function onPickerScroll(picker) {
    const windowEl = picker.querySelector(".value-picker-window");
    if (windowEl.scrollTop < PICKER_ROW_HEIGHT * 2) {
        extendPickerRange(picker, "up");
    }
    if (windowEl.scrollTop + windowEl.clientHeight > windowEl.scrollHeight - PICKER_ROW_HEIGHT * 2) {
        extendPickerRange(picker, "down");
    }
    updatePickerHighlight(picker);
    if (picker.scrollTimer) {
        clearTimeout(picker.scrollTimer);
    }
    picker.scrollTimer = setTimeout(() => {
        snapPickerToNearest(picker);
    }, PICKER_SCROLL_DEBOUNCE_MS);
}

function findPickerItem(picker, valueStr) {
    const kind = picker.getAttribute("data-picker");
    if (kind === "weight") {
        return picker.querySelector(".value-picker-list").querySelector(
            `[data-index="${Number(valueStr) * 2}"]`
        );
    }
    return picker.querySelector(".value-picker-list").querySelector(`[data-value="${valueStr}"]`);
}

function setPickerValue(picker, valueStr) {
    let item = findPickerItem(picker, valueStr);
    const kind = picker.getAttribute("data-picker");
    if (!item && kind === "weight") {
        buildWeightPickerItems(picker, Number(valueStr) * 2);
        item = findPickerItem(picker, valueStr);
    }
    if (!item && kind === "reps" && picker.hasAttribute("data-min")) {
        buildRepsPickerItems(picker);
        item = findPickerItem(picker, valueStr);
    }
    if (item) {
        scrollItemToCenter(picker, item);
        updateHiddenFromPicker(picker);
        updatePickerHighlight(picker);
    }
}

function initValuePickers(root) {
    const scope = root || document;
    const pickers = scope.querySelectorAll(".value-picker:not([data-picker-ready])");
    pickers.forEach((picker) => {
        const hidden = getPickerHiddenInput(picker);
        const initialValue = hidden && hidden.value !== "" ? hidden.value : "0";
        if (picker.getAttribute("data-picker") === "weight") {
            buildWeightPickerItems(picker, Number(initialValue) * 2);
        } else if (picker.getAttribute("data-picker") === "reps" && picker.hasAttribute("data-min")) {
            buildRepsPickerItems(picker);
        }
        const windowEl = picker.querySelector(".value-picker-window");
        windowEl.addEventListener("scroll", () => {
            onPickerScroll(picker);
        });
        picker.setAttribute("data-picker-ready", "1");
        setPickerValue(picker, initialValue);
    });
}

function syncPickersFromHidden(form) {
    form.querySelectorAll(".value-picker").forEach((picker) => {
        const hidden = getPickerHiddenInput(picker);
        if (hidden) {
            setPickerValue(picker, hidden.value);
        }
    });
}

/* ── Modals and exercise actions ─────────────── */

function toggleSetModalOption(req_event) {
    const button = req_event.currentTarget;
    const option = button.dataset.setModalOption;
    const hidden = document.getElementById(`set-modal-${option}-input`);
    if (!hidden) {
        return;
    }
    const enabled = hidden.value !== "on";
    hidden.value = enabled ? "on" : "";
    button.textContent = enabled ? button.dataset.labelOn : button.dataset.labelOff;
    button.classList.toggle("btn-primary", enabled);
    button.classList.toggle("btn-outline", !enabled);
    button.setAttribute("aria-pressed", enabled ? "true" : "false");
}

function openSetModal(req_event) {
    const trigger = req_event.currentTarget;
    const modalName = trigger.getAttribute("data-modal-name");
    const endpoint = trigger.getAttribute("data-routing");
    sendWsRequest(endpoint, trigger).then((response) => {
        const contentEl = document.getElementById(`${modalName}-content`);
        contentEl.innerHTML = response.json_content.html;
        const modal = document.getElementById(modalName);
        if (modal) {
            modal.style.display = "flex";
        }
        requestAnimationFrame(() => {
            initValuePickers(contentEl);
        });
    });
}

function openWorkoutEditModal(req_event) {
    const kind = req_event.currentTarget.dataset.sessionType;
    const header = document.getElementById(`${kind}-header`);
    const section = header.querySelector("section");
    const nameInput = document.getElementById(`${kind}-edit-name`);
    const notesInput = document.getElementById(`${kind}-edit-notes`);
    const idInput = document.getElementById(`${kind}-edit-id`);
    const notesText = document.getElementById(`${kind}-notes-text`);
    const nameEl = document.getElementById(`${kind}-name`);
    const idKey = kind === "workout" ? "workoutId" : "routineId";

    idInput.value = section.dataset[idKey];
    nameInput.value = nameEl.textContent;
    notesInput.value = notesText ? notesText.textContent : "";

    if (kind === "workout") {
        document.getElementById("workout-edit-date").value = section.dataset.workoutDate;
    }

    document.getElementById(`${kind}-modal`).style.display = "flex";
}

function setWorkoutExerciseFeedback(req_event) {
    const trigger = req_event.currentTarget;
    const group = trigger.closest("[data-feedback-for]");
    group.querySelectorAll("[data-feedback]").forEach((button) => {
        button.classList.remove("feedback-selected");
        button.classList.add("btn-outline");
    });
    trigger.classList.remove("btn-outline");
    trigger.classList.add("feedback-selected");
    sendWsRequest("workouts/set_performance_feedback", trigger);
}

function toggleSetDone(req_event) {
    const trigger = req_event.currentTarget;
    sendWsRequest("workouts/toggle_set_done", trigger).then((response) => {
        if (response.json_content?.target && response.json_content?.html) {
            document.querySelector(response.json_content.target).innerHTML =
                response.json_content.html;
        }
        if (response.json_content?.active_exercise_index != null) {
            setWorkoutCardIndex(Number(response.json_content.active_exercise_index));
        }
    });
}

function removeExercise(req_event) {
    const trigger = req_event.currentTarget;
    const exerciseUi = document.getElementById("workout-exercise-ui");
    const endpoint = `${exerciseUi.dataset.endpointNs}/delete_exercise`;
    trigger.setAttribute(
        "data-current-exercise-index",
        String(workoutCurrentCardIndex)
    );
    sendWsRequest(endpoint, trigger).then((response) => {
        if (response.json_content?.target && response.json_content?.html) {
            document.querySelector(response.json_content.target).innerHTML =
                response.json_content.html;
        }
        initWorkoutCardsPage();
        if (response.json_content?.active_exercise_index != null) {
            setWorkoutCardIndex(Number(response.json_content.active_exercise_index));
        }
    });
}

function addExercise(req_event) {
    const trigger = req_event.currentTarget;
    const exerciseUi = document.getElementById("workout-exercise-ui");
    const endpoint = `${exerciseUi.dataset.endpointNs}/add_exercise`;
    const currentCard = workoutCards[workoutCurrentCardIndex];
    if (currentCard?.dataset.exerciseId) {
        trigger.setAttribute("data-current-exercise-id", currentCard.dataset.exerciseId);
    } else {
        trigger.removeAttribute("data-current-exercise-id");
    }
    sendWsRequest(endpoint, trigger).then((response) => {
        if (response.json_content?.target && response.json_content?.html) {
            document.querySelector(response.json_content.target).innerHTML =
                response.json_content.html;
        }
        initWorkoutCardsPage();
        if (response.json_content?.new_exercise_index != null) {
            setWorkoutCardIndex(Number(response.json_content.new_exercise_index));
        }
    });
}

function selectExerciseType(req_event) {
    const item = req_event.currentTarget;
    const value = item.getAttribute('data-value');
    const label = item.getAttribute('data-label') || 'Default';
    const dropdown = item.closest('.gainz-dropdown');
    const hidden = dropdown.querySelector('input[name="exercise_type"]');
    const slot = dropdown.querySelector('[data-slot="exercise-type-label"]');
    const menu = dropdown.querySelector('.gainz-dropdown-menu');

    hidden.value = value;
    if (value) {
        slot.innerHTML = item.innerHTML;
    } else {
        slot.textContent = 'Default';
    }
    menu.hidden = true;
}

/* ── Init ────────────────────────────────────── */

document.addEventListener("DOMContentLoaded", () => initWorkoutCardsPage());
