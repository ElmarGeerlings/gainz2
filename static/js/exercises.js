function debounce(func, delay) {
    let timeoutId;
    return function (...args) {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => {
            func.apply(this, args);
        }, delay);
    };
}

async function fetchAndUpdateExerciseList() {
    const form = document.getElementById("exercise-filter-form");
    const listContainer = document.getElementById("exercise-list-container");
    if (!form || !listContainer) {
        return;
    }

    const params = new URLSearchParams();
    const searchInput = document.getElementById("exercise-search");
    const typeFilter = document.getElementById("exercise-type-filter");
    const bodypartFilter = document.getElementById("bodypart-filter");
    const customFilter = document.getElementById("custom-filter");

    if (searchInput && searchInput.value) {
        params.append("search_query", searchInput.value);
    }
    if (typeFilter && typeFilter.value) {
        params.append("exercise_type", typeFilter.value);
    }
    if (bodypartFilter && bodypartFilter.value) {
        params.append("primary_bodypart", bodypartFilter.value);
    }
    if (customFilter && customFilter.value) {
        params.append("custom_filter", customFilter.value);
    }

    const url = "/exercises/?" + params.toString();
    const response = await fetch(url, {
        method: "GET",
        headers: {
            "X-Requested-With": "XMLHttpRequest",
        },
        credentials: "same-origin",
    });

    listContainer.innerHTML = await response.text();
}

const debouncedFetchExercises = debounce(fetchAndUpdateExerciseList, 300);
window.debouncedFetchExercises = debouncedFetchExercises;

function preventExerciseFilterSubmit(req_event) {
    req_event.preventDefault();
    fetchAndUpdateExerciseList();
}

function exerciseDangerToast(message) {
    appendToast(
        '<div class="gainz-toast gainz-toast-danger" role="alert">' +
        '<button type="button" class="gainz-toast-close" data-function="click->dismissToast" aria-label="Close">×</button>' +
        '<p class="gainz-toast-message">' + message + '</p>' +
        '</div>',
        3000
    );
}

async function saveExercise(req_event) {
    const btn = req_event.currentTarget;
    const form = btn.closest("form");
    if (!form) {
        return;
    }

    const name = (form.querySelector("#exercise-modal-name")?.value || "").trim();
    const primaryBodypart = form.querySelector("#exercise-modal-primary-bodypart")?.value || "";

    if (!name) {
        exerciseDangerToast("Exercise name is required.");
        return;
    }
    if (!primaryBodypart) {
        exerciseDangerToast("Primary bodypart is required.");
        return;
    }

    const exerciseId = form.querySelector("#exercise-modal-id")?.value || "";
    const endpoint = exerciseId
        ? "exercises/update_exercise"
        : "exercises/create_exercise";

    const response = await sendWsRequest(endpoint, btn);

    if (response.status === 200) {
        const modal = document.getElementById("exercise-modal");
        if (modal) {
            hideGainzModal(modal);
        }
        if (response.json_content?.toast_html) {
            appendToast(
                response.json_content.toast_html,
                response.json_content.toast_delay_ms
            );
        }
        fetchAndUpdateExerciseList();
        return;
    }
    if (response.json_content?.toast_html) {
        appendToast(
            response.json_content.toast_html,
            response.json_content.toast_delay_ms
        );
    }
}
window.saveExercise = saveExercise;
