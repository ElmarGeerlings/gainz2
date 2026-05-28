let workoutCurrentCardIndex = 0;
let workoutCards = [];
let workoutIndicators = [];
let workoutTouchStartX = 0;
let workoutTouchEndX = 0;

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
    const response = workoutTouchStartX - workoutTouchEndX;
    if (Math.abs(response) < 45) {
        return;
    }
    if (response > 0) {
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
    }, { passive: true });

    container.addEventListener("touchend", (req_event) => {
        if (!req_event.changedTouches.length) {
            return;
        }
        workoutTouchEndX = req_event.changedTouches[0].clientX;
        handleWorkoutSwipe();
    }, { passive: true });
}

function initWorkoutCardsPage() {
    const container = document.getElementById("exercise-card-container");
    if (!container) {
        return;
    }

    workoutCards = Array.from(container.querySelectorAll(".exercise-card"));
    workoutIndicators = Array.from(document.querySelectorAll(".carousel-indicator"));
    workoutCurrentCardIndex = 0;
    refreshWorkoutNavState();
    bindWorkoutTouch(container);
}

const PICKER_ROW_HEIGHT = 44;
const WEIGHT_WINDOW_HALF_STEPS = 40;
const PICKER_SCROLL_DEBOUNCE_MS = 80;

function getPickerHiddenInput(picker) {
    const form = picker.closest("form");
    if (!form) {
        return null;
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
    const clamped = Math.min(maxIndex, Math.max(minIndex, centerIndex));
    const lowIndex = Math.max(minIndex, clamped - WEIGHT_WINDOW_HALF_STEPS);
    const highIndex = Math.min(maxIndex, clamped + WEIGHT_WINDOW_HALF_STEPS);
    renderWeightPickerItems(picker, lowIndex, highIndex);
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
    if (!item && picker.getAttribute("data-picker") === "weight") {
        buildWeightPickerItems(picker, Number(valueStr) * 2);
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
    const weightPicker = form.querySelector('[data-picker="weight"]');
    const repsPicker = form.querySelector('[data-picker="reps"]');
    const weightInput = form.querySelector("#set-modal-weight");
    const repsInput = form.querySelector("#set-modal-reps");
    if (weightPicker && weightInput) {
        setPickerValue(weightPicker, weightInput.value);
    }
    if (repsPicker && repsInput) {
        setPickerValue(repsPicker, repsInput.value);
    }
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
    const header = document.getElementById("workout-header");
    const section = header.querySelector("section");
    const nameInput = document.getElementById("workout-edit-name");
    const dateInput = document.getElementById("workout-edit-date");
    const notesInput = document.getElementById("workout-edit-notes");
    const idInput = document.getElementById("workout-edit-id");
    const notesText = document.getElementById("workout-notes-text");
    const nameEl = document.getElementById("workout-name");

    idInput.value = section.dataset.workoutId;
    nameInput.value = nameEl.textContent;
    dateInput.value = section.dataset.workoutDate;
    notesInput.value = notesText ? notesText.textContent : "";

    const modal = document.getElementById("workout-modal");
    modal.style.display = "flex";
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

function removeExerciseFromWorkout(req_event) {
    const trigger = req_event.currentTarget;
    trigger.setAttribute(
        "data-current-exercise-index",
        String(workoutCurrentCardIndex)
    );
    sendWsRequest("workouts/delete_exercise", trigger).then((response) => {
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
function addExerciseToWorkout(req_event) {
    const trigger = req_event.currentTarget;
    const currentCard = workoutCards[workoutCurrentCardIndex];
    if (currentCard?.dataset.exerciseId) {
        trigger.setAttribute("data-current-exercise-id", currentCard.dataset.exerciseId);
    } else {
        trigger.removeAttribute("data-current-exercise-id");
    }
    sendWsRequest("workouts/add_exercise", trigger).then((response) => {
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

document.addEventListener("DOMContentLoaded", initWorkoutCardsPage);
