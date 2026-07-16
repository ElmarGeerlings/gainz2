const REST_TIMER_STORAGE_KEY = 'gainz-active-rest-timer';
const REST_TIMER_CHANNEL_STORAGE_KEY = 'gainz-rest-timer-channel-id';
const REST_TIMER_DEEPLINK_WORKOUT_KEY = 'gainz-rest-deeplink-workout';
const REST_TIMER_DEEPLINK_EXERCISE_KEY = 'gainz-rest-deeplink-exercise';
const REST_TIMER_NOTIFICATION_ID = 1;
const REST_TIMER_ACTION_TYPE = 'REST_TIMER';

let restTimerTickIntervalId = null;
let restTimerActiveChannelId = null;
let restTimerNativeListenersInitialized = false;
let restTimerScheduledEndTimestamp = null;

function formatMinutes(seconds) {
    const total = Math.max(0, Math.floor(Number(seconds)));
    const minutes = Math.floor(total / 60);
    const secs = total % 60;
    return `${minutes}:${String(secs).padStart(2, '0')}`;
}

function getLocalNotifications() {
    if (!window.Capacitor || !Capacitor.isNativePlatform || !Capacitor.isNativePlatform()) {
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

function ensureRestTimerNotificationChannel() {
    const LocalNotifications = getLocalNotifications();
    if (!LocalNotifications) {
        return Promise.resolve(null);
    }
    const workoutUi = document.getElementById('workout-exercise-ui');
    const sound = !workoutUi || workoutUi.dataset.notificationSoundEnabled === 'true';
    const vibrate = !workoutUi || workoutUi.dataset.notificationVibrationEnabled === 'true';
    const channelId = `gainz-rest-s${sound ? 1 : 0}-v${vibrate ? 1 : 0}`;
    const storedId = restTimerActiveChannelId
        || localStorage.getItem(REST_TIMER_CHANNEL_STORAGE_KEY);
    let deletePromise = Promise.resolve();
    if (storedId && storedId !== channelId) {
        deletePromise = LocalNotifications.deleteChannel({ id: storedId });
    }
    const channelConfig = {
        id: channelId,
        name: 'Rest timer',
        description: 'Alerts when your rest timer finishes',
        importance: 4,
        visibility: 1,
        vibration: vibrate,
    };
    return deletePromise.then(() => LocalNotifications.createChannel(channelConfig)).then(() => {
        restTimerActiveChannelId = channelId;
        localStorage.setItem(REST_TIMER_CHANNEL_STORAGE_KEY, channelId);
        return channelId;
    });
}

function scheduleNativeRestNotification(state) {
    const LocalNotifications = getLocalNotifications();
    if (!LocalNotifications || !state || state.isPaused || !state.endTimestamp) {
        return Promise.resolve();
    }
    if (restTimerScheduledEndTimestamp === state.endTimestamp) {
        return Promise.resolve();
    }
    restTimerScheduledEndTimestamp = state.endTimestamp;
    const restCount = Number(state.restCount) || 1;
    const title = restCount >= 2 ? `Rest ${restCount} over` : 'Rest over';
    const body = state.exerciseName
        ? `${state.exerciseName} — start your next set.`
        : 'Time to start your next set.';
    return ensureNativeNotificationPermission()
        .then(() => ensureRestTimerNotificationChannel())
        .then((channelId) => LocalNotifications.cancel({
            notifications: [{ id: REST_TIMER_NOTIFICATION_ID }],
        }).then(() => channelId))
        .then((channelId) => LocalNotifications.schedule({
            notifications: [{
                id: REST_TIMER_NOTIFICATION_ID,
                title,
                body,
                channelId,
                autoCancel: true,
                actionTypeId: REST_TIMER_ACTION_TYPE,
                extra: {
                    workoutId: state.workoutId,
                    exerciseId: state.exerciseId,
                    exerciseName: state.exerciseName,
                    durationSeconds: state.durationSeconds,
                    restCount,
                },
                schedule: {
                    at: new Date(state.endTimestamp),
                    allowWhileIdle: true,
                },
            }],
        }));
}

function syncNativeRestNotification(state) {
    if (!state || state.isPaused || !state.endTimestamp) {
        return cancelNativeRestNotification();
    }
    return scheduleNativeRestNotification(state);
}

function cancelNativeRestNotification() {
    restTimerScheduledEndTimestamp = null;
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
    const playBtn = card.querySelector('[data-rest-timer-play]');
    const pauseBtn = card.querySelector('[data-rest-timer-pause]');
    const stopBtn = card.querySelector('[data-rest-timer-stop]');
    if (playBtn && pauseBtn && stopBtn) {
        playBtn.classList.remove('hidden');
        pauseBtn.classList.add('hidden');
        stopBtn.classList.add('hidden');
    }
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
    } else {
        restTimerScheduledEndTimestamp = null;
    }

    resetCardToIdle(
        document.querySelector(`.exercise-card[data-exercise-id="${state.exerciseId}"]`)
    );
    const workoutUi = document.getElementById('workout-exercise-ui');
    if (workoutUi && String(workoutUi.dataset.workoutId) === String(state.workoutId)) {
        sessionStorage.setItem(REST_TIMER_DEEPLINK_WORKOUT_KEY, String(state.workoutId));
        sessionStorage.setItem(REST_TIMER_DEEPLINK_EXERCISE_KEY, String(state.exerciseId));
    }
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

    if (typeof setWorkoutCardIndex === 'function') {
        const cards = document.querySelectorAll('.exercise-card[data-exercise-id]');
        const cardIndex = Array.from(cards).findIndex(
            (card) => card.dataset.exerciseId === String(state.exerciseId)
        );
        if (cardIndex >= 0) {
            setWorkoutCardIndex(cardIndex);
        }
    }

    document.querySelectorAll('.exercise-card[data-exercise-id]').forEach((card) => {
        const playBtn = card.querySelector('[data-rest-timer-play]');
        const pauseBtn = card.querySelector('[data-rest-timer-pause]');
        const stopBtn = card.querySelector('[data-rest-timer-stop]');
        if (card.dataset.exerciseId === String(state.exerciseId)) {
            const remaining = getRemainingSeconds(state);
            if (!state.isPaused && remaining <= 0) {
                finalizeExpiredTimer(state, false);
                return;
            }
            setCardTimerDisplay(card, remaining);
            card.classList.add('timer-display-running');
            if (playBtn && pauseBtn && stopBtn) {
                if (state.isPaused) {
                    playBtn.classList.remove('hidden');
                    pauseBtn.classList.add('hidden');
                    stopBtn.classList.remove('hidden');
                } else {
                    playBtn.classList.add('hidden');
                    pauseBtn.classList.remove('hidden');
                    stopBtn.classList.remove('hidden');
                }
            }
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

    syncNativeRestNotification(state);
    stopRestTimerTick();
    restTimerTick();
    restTimerTickIntervalId = setInterval(restTimerTick, 1000);
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
        restCount: 1,
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
    syncRestTimerDisplay();
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

function initNativeRestNotificationListeners() {
    const LocalNotifications = getLocalNotifications();
    if (!LocalNotifications || restTimerNativeListenersInitialized) {
        return;
    }
    restTimerNativeListenersInitialized = true;
    LocalNotifications.registerActionTypes({
        types: [{
            id: REST_TIMER_ACTION_TYPE,
            actions: [{ id: 'rest-again', title: 'Rest again' }],
        }],
    });
    LocalNotifications.addListener('localNotificationActionPerformed', (action) => {
        const notification = action.notification;
        if (!notification || notification.id !== REST_TIMER_NOTIFICATION_ID) {
            return;
        }
        const extra = notification.extra;
        if (action.actionId === 'rest-again') {
            if (!extra || !extra.workoutId || !extra.exerciseId || !extra.durationSeconds) {
                return;
            }
            const durationSeconds = Number(extra.durationSeconds) || 0;
            if (durationSeconds <= 0) {
                return;
            }
            const restCount = (Number(extra.restCount) || 1) + 1;
            const state = {
                workoutId: String(extra.workoutId),
                exerciseId: String(extra.exerciseId),
                exerciseName: extra.exerciseName || '',
                durationSeconds,
                endTimestamp: Date.now() + durationSeconds * 1000,
                isPaused: false,
                pausedRemaining: 0,
                completeHandled: false,
                restCount,
            };
            localStorage.setItem(REST_TIMER_STORAGE_KEY, JSON.stringify(state));
            scheduleNativeRestNotification(state);
            const App = (Capacitor.Plugins && Capacitor.Plugins.App)
                || (window.capacitorApp && window.capacitorApp.App);
            if (App && App.minimizeApp) {
                App.minimizeApp();
            }
            return;
        }
        if (action.actionId === 'tap' && extra && extra.workoutId && extra.exerciseId) {
            const workoutId = String(extra.workoutId);
            const exerciseId = String(extra.exerciseId);
            sessionStorage.setItem(REST_TIMER_DEEPLINK_WORKOUT_KEY, workoutId);
            sessionStorage.setItem(REST_TIMER_DEEPLINK_EXERCISE_KEY, exerciseId);
            const targetUrl = `/workouts/${workoutId}/?exercise=${exerciseId}`;
            const workoutUi = document.getElementById('workout-exercise-ui');
            if (workoutUi && String(workoutUi.dataset.workoutId) === workoutId) {
                history.replaceState(null, '', targetUrl);
                if (typeof setWorkoutCardIndex === 'function') {
                    const cards = document.querySelectorAll('.exercise-card[data-exercise-id]');
                    const index = Array.from(cards).findIndex(
                        (card) => card.dataset.exerciseId === exerciseId
                    );
                    if (index >= 0) {
                        setWorkoutCardIndex(index);
                    }
                }
                return;
            }
            window.location.href = targetUrl;
        }
    });
}

function initRestTimer() {
    const workoutUi = document.getElementById('workout-exercise-ui');
    if (!workoutUi || !workoutUi.dataset.workoutId) {
        return;
    }

    ensureRestTimerNotificationChannel();

    document.addEventListener('visibilitychange', () => {
        syncRestTimerDisplay();
    });

    window.addEventListener('pageshow', () => {
        syncRestTimerDisplay();
    });

    window.addEventListener('pagehide', () => {
        const raw = localStorage.getItem(REST_TIMER_STORAGE_KEY);
        const storedState = raw ? JSON.parse(raw) : null;
        if (!storedState || storedState.isPaused || !storedState.endTimestamp) {
            return;
        }
        if (String(storedState.workoutId) !== String(workoutUi.dataset.workoutId)) {
            return;
        }
        scheduleNativeRestNotification(storedState);
    });
}

document.addEventListener('DOMContentLoaded', () => {
    const workoutUi = document.getElementById('workout-exercise-ui');
    const exerciseParam = new URLSearchParams(window.location.search).get('exercise');
    if (exerciseParam && workoutUi && workoutUi.dataset.workoutId) {
        sessionStorage.setItem(REST_TIMER_DEEPLINK_WORKOUT_KEY, workoutUi.dataset.workoutId);
        sessionStorage.setItem(REST_TIMER_DEEPLINK_EXERCISE_KEY, exerciseParam);
    }
    initNativeRestNotificationListeners();
    initRestTimer();
    const raw = localStorage.getItem(REST_TIMER_STORAGE_KEY);
    const storedState = raw ? JSON.parse(raw) : null;
    if (storedState && !storedState.isPaused && storedState.endTimestamp) {
        const workoutUi = document.getElementById('workout-exercise-ui');
        if (!workoutUi || !workoutUi.dataset.workoutId) {
            syncNativeRestNotification(storedState);
        }
    }
});
