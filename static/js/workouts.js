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
        return;
    }

    workoutCards.forEach((card, index) => {
        card.classList.toggle("is-hidden", index !== workoutCurrentCardIndex);
    });

    workoutIndicators.forEach((indicator, index) => {
        indicator.classList.toggle("is-active", index === workoutCurrentCardIndex);
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

function toggleSetDone(req_event) {
    const button = req_event.currentTarget;
    if (button.classList.contains("btn-success")) {
        button.classList.remove("btn-success", "text-white");
        button.classList.add("btn-outline");
    } else {
        button.classList.add("btn-success", "text-white");
        button.classList.remove("btn-outline");
    }
}

function placeholderEditWorkout() {}
function placeholderDeleteWorkout() {}
function placeholderRemoveExercise() {}
function placeholderAddSet() {}
function placeholderAddExercise() {}

window.showNextWorkoutCard = showNextWorkoutCard;
window.showPreviousWorkoutCard = showPreviousWorkoutCard;
window.goToWorkoutCard = goToWorkoutCard;
window.toggleSetDone = toggleSetDone;
window.placeholderEditWorkout = placeholderEditWorkout;
window.placeholderDeleteWorkout = placeholderDeleteWorkout;
window.placeholderRemoveExercise = placeholderRemoveExercise;
window.placeholderAddSet = placeholderAddSet;
window.placeholderAddExercise = placeholderAddExercise;

document.addEventListener("DOMContentLoaded", initWorkoutCardsPage);
