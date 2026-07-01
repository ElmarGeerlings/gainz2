const TIMER_DB_NAME = 'gainz-timer';
const TIMER_STORE_NAME = 'pending';
const TIMER_NOTIFICATION_TAG = 'gainz-rest-timer';

let pendingTimeoutId = null;

self.addEventListener('install', (event) => {
    self.skipWaiting();
});

self.addEventListener('activate', (event) => {
    event.waitUntil(
        self.clients.claim().then(() => openTimerDb().then((db) => new Promise((resolve, reject) => {
            const tx = db.transaction(TIMER_STORE_NAME, 'readonly');
            const store = tx.objectStore(TIMER_STORE_NAME);
            const request = store.get('active');
            request.onsuccess = () => resolve(request.result || null);
            request.onerror = () => reject(request.error);
        })).then((record) => schedulePendingTimer(record)))
    );
});

function openTimerDb() {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open(TIMER_DB_NAME, 1);
        request.onupgradeneeded = () => {
            const db = request.result;
            if (!db.objectStoreNames.contains(TIMER_STORE_NAME)) {
                db.createObjectStore(TIMER_STORE_NAME, { keyPath: 'id' });
            }
        };
        request.onsuccess = () => resolve(request.result);
        request.onerror = () => reject(request.error);
    });
}

function clearPendingTimer() {
    return openTimerDb().then((db) => new Promise((resolve, reject) => {
        const tx = db.transaction(TIMER_STORE_NAME, 'readwrite');
        const store = tx.objectStore(TIMER_STORE_NAME);
        const request = store.delete('active');
        request.onsuccess = () => resolve();
        request.onerror = () => reject(request.error);
    }));
}

function showTimerNotification(payload) {
    const title = payload.title || 'Rest over';
    const options = {
        body: payload.body || 'Time to start your next set.',
        tag: payload.tag || TIMER_NOTIFICATION_TAG,
        renotify: true,
        data: {
            url: payload.url || '/',
        },
    };
    return self.registration.showNotification(title, options);
}

function schedulePendingTimer(record) {
    if (pendingTimeoutId != null) {
        clearTimeout(pendingTimeoutId);
        pendingTimeoutId = null;
    }
    if (!record || !record.endTimestamp) {
        return Promise.resolve();
    }
    const remainingMs = record.endTimestamp - Date.now();
    if (remainingMs <= 0) {
        return showTimerNotification(record).then(() => clearPendingTimer());
    }
    pendingTimeoutId = setTimeout(() => {
        pendingTimeoutId = null;
        showTimerNotification(record).then(() => clearPendingTimer());
    }, remainingMs);
    return Promise.resolve();
}

self.addEventListener('message', (event) => {
    const data = event.data;
    if (!data || !data.type) {
        return;
    }
    if (data.type === 'timer-schedule') {
        const record = {
            id: 'active',
            endTimestamp: data.endTimestamp,
            title: data.title,
            body: data.body,
            url: data.url,
            tag: data.tag || TIMER_NOTIFICATION_TAG,
        };
        event.waitUntil(
            openTimerDb().then((db) => new Promise((resolve, reject) => {
                const tx = db.transaction(TIMER_STORE_NAME, 'readwrite');
                const store = tx.objectStore(TIMER_STORE_NAME);
                const request = store.put(record);
                request.onsuccess = () => resolve();
                request.onerror = () => reject(request.error);
            })).then(() => schedulePendingTimer(record))
        );
        return;
    }
    if (data.type === 'timer-cancel') {
        if (pendingTimeoutId != null) {
            clearTimeout(pendingTimeoutId);
            pendingTimeoutId = null;
        }
        event.waitUntil(clearPendingTimer());
    }
});

self.addEventListener('notificationclick', (event) => {
    event.notification.close();
    const targetUrl = event.notification.data && event.notification.data.url
        ? event.notification.data.url
        : '/';
    event.waitUntil(
        self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clientList) => {
            for (const client of clientList) {
                if ('focus' in client) {
                    return client.focus();
                }
            }
            if (self.clients.openWindow) {
                return self.clients.openWindow(targetUrl);
            }
            return undefined;
        })
    );
});
