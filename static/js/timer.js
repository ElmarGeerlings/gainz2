const REST_TIMER_STORAGE_KEY = 'gainz-active-rest-timer';
const REST_TIMER_NOTIFICATION_ID = 1;

let restTimerTickIntervalId = null;

function formatMinutes(seconds) {
    const total = Math.max(0, Math.floor(Number(seconds)));
    const minutes = Math.floor(total / 60);
    const secs = total % 60;
    return `${minutes}:${String(secs).padStart(2, '0')}`;
}

function isCapacitorNative() {
    return window.Capacitor
        && Capacitor.isNativePlatform
        && Capacitor.isNativePlatform();
}

function getLocalNotifications() {
    if (!isCapacitorNative()) {
        return null;
    }
    if (Capacitor.Plugins && Capacitor.Plugins.LocalNotifications) {
        return Capacitor.Plugins.LocalNotifications;
    }
    if (window.capacitorLocalNotifications && window.capacitorLocalNotifications.LocalNotifications) {
        return window.capacitorLocalNotifications.LocalNotifications;
    }
    return null;
}

function ensureNativeNotificationPermission() {
    const LocalNotifications = getLocalNotifications();
    if (!LocalNotifications) {
        return Promise.resolve();
    }
    return LocalNotifications.checkPermissions().then((status) => {
        if (status.display === 'granted') {
            return;
        }
        return LocalNotifications.requestPermissions();
    });
}

function scheduleNativeRestNotification(state) {
    const LocalNotifications = getLocalNotifications();
    if (!LocalNotifications || !state || state.isPaused || !state.endTimestamp) {
        return Promise.resolve();
    }
    const body = state.exerciseName
        ? `${state.exerciseName} — start your next set.`
        : 'Time to start your next set.';
    return ensureNativeNotificationPermission().then(() => LocalNotifications.cancel({
        notifications: [{ id: REST_TIMER_NOTIFICATION_ID }],
    })).then(() => LocalNotifications.schedule({
        notifications: [{
            id: REST_TIMER_NOTIFICATION_ID,
            title: 'Rest over',
            body,
            schedule: {
                at: new Date(state.endTimestamp),
                allowWhileIdle: true,
            },
        }],
    }));
}

function cancelNativeRestNotification() {
    const LocalNotifications = getLocalNotifications();
    if (!LocalNotifications) {
        return Promise.resolve();
    }
    return LocalNotifications.cancel({
        notifications: [{ id: REST_TIMER_NOTIFICATION_ID }],
    });
}

function getWorkoutTimerState() {
    const raw = localStorage.getItem(REST_TIMER_STORAGE_KEY);
    const state = raw ? JSON.parse(raw) : null;
    const workoutUi = document.getElementById('workout-exercise-ui');
    const workoutId = workoutUi && workoutUi.dataset.workoutId
        ? workoutUi.dataset.workoutId
        : null;
    if (!state || !workoutId || String(state.workoutId) !== String(workoutId)) {
        return null;
    }
    return state;
}

function getRemainingSeconds(state) {
    if (!state) {
        return 0;
    }
    if (state.isPaused) {
        return Math.max(0, Math.ceil(Number(state.pausedRemaining) || 0));
    }
    if (!state.endTimestamp) {
        return 0;
    }
    return Math.max(0, Math.ceil((state.endTimestamp - Date.now()) / 1000));
}

function setCardTimerDisplay(card, seconds) {
    const display = card.querySelector('[data-timer-display]');
    if (display) {
        display.textContent = formatMinutes(seconds);
    }
}

function resetCardToIdle(card) {
    if (!card) {
        return;
    }
    setCardTimerDisplay(card, Number(card.dataset.restSeconds) || 0);
    card.classList.remove('timer-display-running');
}

function stopRestTimerTick() {
    if (restTimerTickIntervalId != null) {
        clearInterval(restTimerTickIntervalId);
        restTimerTickIntervalId = null;
    }
}

function finalizeExpiredTimer(state, showForegroundAlert) {
    if (!state || state.completeHandled) {
        return;
    }
    state.completeHandled = true;
    localStorage.setItem(REST_TIMER_STORAGE_KEY, JSON.stringify(state));
    stopRestTimerTick();

    if (showForegroundAlert && !document.hidden && typeof notifyUser === 'function') {
        cancelNativeRestNotification();
        const workoutUi = document.getElementById('workout-exercise-ui');
        const sound = !workoutUi || workoutUi.dataset.notificationSoundEnabled === 'true';
        const vibrate = !workoutUi || workoutUi.dataset.notificationVibrationEnabled === 'true';
        notifyUser('Rest over', {
            variant: 'success',
            sound,
            vibrate,
            delayMs: 2500,
        });
    }

    resetCardToIdle(
        document.querySelector(`.exercise-card[data-exercise-id="${state.exerciseId}"]`)
    );
    localStorage.removeItem(REST_TIMER_STORAGE_KEY);
}

function restTimerTick() {
    const state = getWorkoutTimerState();
    if (!state || state.isPaused) {
        return;
    }
    const remaining = getRemainingSeconds(state);
    const ownerCard = document.querySelector(
        `.exercise-card[data-exercise-id="${state.exerciseId}"]`
    );
    if (ownerCard) {
        setCardTimerDisplay(ownerCard, remaining);
    }
    if (remaining <= 0) {
        finalizeExpiredTimer(state, true);
    }
}

function startRestTimerTick() {
    stopRestTimerTick();
    restTimerTick();
    restTimerTickIntervalId = setInterval(restTimerTick, 1000);
}

function syncRestTimerDisplay() {
    const workoutUi = document.getElementById('workout-exercise-ui');
    if (!workoutUi || !workoutUi.dataset.workoutId) {
        stopRestTimerTick();
        return;
    }

    const state = getWorkoutTimerState();
    if (!state) {
        stopRestTimerTick();
        document.querySelectorAll('.exercise-card[data-exercise-id]').forEach((card) => {
            resetCardToIdle(card);
        });
        return;
    }

    document.querySelectorAll('.exercise-card[data-exercise-id]').forEach((card) => {
        if (card.dataset.exerciseId === String(state.exerciseId)) {
            const remaining = getRemainingSeconds(state);
            if (!state.isPaused && remaining <= 0) {
                finalizeExpiredTimer(state, false);
                return;
            }
            setCardTimerDisplay(card, remaining);
            card.classList.add('timer-display-running');
        } else {
            resetCardToIdle(card);
        }
    });

    if (state.isPaused) {
        stopRestTimerTick();
        return;
    }

    const remaining = getRemainingSeconds(state);
    if (remaining <= 0) {
        finalizeExpiredTimer(state, false);
        return;
    }

    scheduleNativeRestNotification(state);
    startRestTimerTick();
}

function startRestTimer(req_event) {
    const workoutUi = document.getElementById('workout-exercise-ui');
    if (!workoutUi || !workoutUi.dataset.workoutId) {
        return;
    }

    const card = req_event.currentTarget.closest('.exercise-card');
    if (!card) {
        return;
    }

    const workoutId = workoutUi.dataset.workoutId;
    const exerciseId = card.dataset.exerciseId;
    const durationSeconds = Number(card.dataset.restSeconds) || 0;
    const exerciseName = card.dataset.exerciseName || '';

    if (durationSeconds <= 0) {
        return;
    }

    const existing = getWorkoutTimerState();
    if (
        existing
        && String(existing.exerciseId) === String(exerciseId)
        && existing.isPaused
    ) {
        const pausedRemaining = Math.max(0, Number(existing.pausedRemaining) || 0);
        if (pausedRemaining <= 0) {
            return;
        }
        existing.isPaused = false;
        existing.pausedRemaining = 0;
        existing.endTimestamp = Date.now() + pausedRemaining * 1000;
        existing.completeHandled = false;
        localStorage.setItem(REST_TIMER_STORAGE_KEY, JSON.stringify(existing));
        syncRestTimerDisplay();
        return;
    }

    if (existing) {
        cancelNativeRestNotification();
        resetCardToIdle(
            document.querySelector(`.exercise-card[data-exercise-id="${existing.exerciseId}"]`)
        );
    }

    const state = {
        workoutId,
        exerciseId,
        exerciseName,
        durationSeconds,
        endTimestamp: Date.now() + durationSeconds * 1000,
        isPaused: false,
        pausedRemaining: 0,
        completeHandled: false,
    };
    localStorage.setItem(REST_TIMER_STORAGE_KEY, JSON.stringify(state));
    syncRestTimerDisplay();
}

function pauseRestTimer(req_event) {
    const state = getWorkoutTimerState();
    if (!state || state.isPaused) {
        return;
    }

    const remaining = getRemainingSeconds(state);
    if (remaining <= 0) {
        return;
    }

    stopRestTimerTick();
    cancelNativeRestNotification();

    state.isPaused = true;
    state.pausedRemaining = remaining;
    state.endTimestamp = null;
    state.completeHandled = false;
    localStorage.setItem(REST_TIMER_STORAGE_KEY, JSON.stringify(state));

    const ownerCard = document.querySelector(
        `.exercise-card[data-exercise-id="${state.exerciseId}"]`
    );
    if (ownerCard) {
        setCardTimerDisplay(ownerCard, remaining);
    }
}

function stopRestTimer(req_event) {
    const state = getWorkoutTimerState();
    if (!state) {
        return;
    }

    stopRestTimerTick();
    cancelNativeRestNotification();

    resetCardToIdle(
        document.querySelector(`.exercise-card[data-exercise-id="${state.exerciseId}"]`)
    );
    localStorage.removeItem(REST_TIMER_STORAGE_KEY);
}

function initRestTimer() {
    const workoutUi = document.getElementById('workout-exercise-ui');
    if (!workoutUi || !workoutUi.dataset.workoutId) {
        return;
    }

    syncRestTimerDisplay();

    document.addEventListener('visibilitychange', () => {
        if (document.visibilityState === 'visible') {
            syncRestTimerDisplay();
        }
    });

    window.addEventListener('pageshow', () => {
        syncRestTimerDisplay();
    });
}

document.addEventListener('DOMContentLoaded', () => {
    initRestTimer();
});
