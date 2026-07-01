const port = window.location.port ? `:${window.location.port}` : '';
const wsProtocol = location.protocol === 'https:' ? 'wss' : 'ws';
const wsUrl = `${wsProtocol}://${window.location.hostname}${port}/ws/`;

let ws;
let wsRetryDelay = 1000;
let wsRetryTimer = null;
const WS_RETRY_MAX = 30000;
const sendQueue = [];

const requestMap = new Map();

function showLoading() {}
function hideLoading() {}

function connectWs() {
  if (ws && ws.readyState !== WebSocket.CLOSED) {
    ws.onclose = null;
    ws.close();
  }

  ws = new WebSocket(wsUrl);

  ws.onopen = () => {
    console.log('WebSocket connected');
    wsRetryDelay = 1000;
    while (sendQueue.length > 0) {
      ws.send(sendQueue.shift());
    }
  };

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.request_id != null && requestMap.has(data.request_id)) {
      const resolve = requestMap.get(data.request_id);
      resolve(data);
      requestMap.delete(data.request_id);
      if (requestMap.size === 0) {
        hideLoading();
      }
      return;
    }
    console.log('WS message (no request_id handler):', data);
  };

  ws.onerror = (error) => {
    console.error('WebSocket error:', error);
  };

  ws.onclose = () => {
    console.log(`WebSocket disconnected, retrying in ${wsRetryDelay}ms`);
    wsRetryTimer = setTimeout(connectWs, wsRetryDelay);
    wsRetryDelay = Math.min(wsRetryDelay * 2, WS_RETRY_MAX);
  };
}

connectWs();

document.addEventListener('visibilitychange', () => {
  if (document.visibilityState === 'visible' && ws.readyState !== WebSocket.OPEN) {
    clearTimeout(wsRetryTimer);
    wsRetryDelay = 1000;
    connectWs();
  }
});

function sendWsRequest(endpoint, element) {
  return new Promise((resolve) => {
    const requestId = Math.random().toString(36).substring(2, 15);
    const attributes = {};
    for (const attribute of element.attributes) {
      attributes[attribute.name] = attribute.value;
    }
    if (element.type === 'checkbox') {
      attributes.checked = element.checked;
    }
    if (element.value) {
      attributes.value = element.value;
    }
    const form = element.closest('form');
    if (form) {
      const formData = new FormData(form);
      for (const [key, value] of formData.entries()) {
        attributes[key] = value;
      }
    }
    const message = JSON.stringify({
      request_id: requestId,
      endpoint,
      attributes,
    });
    showLoading();
    requestMap.set(requestId, resolve);
    if (ws.readyState === WebSocket.OPEN) {
      ws.send(message);
    } else {
      sendQueue.push(message);
    }
  });
}

function ws_request(event, endpoint) {
  const trigger = event.currentTarget;
  const target = trigger.getAttribute('data-target');
  const toRefresh = trigger.hasAttribute('data-refresh');
  const closeModalSelector = trigger.getAttribute('data-close-modal');

  sendWsRequest(endpoint, trigger).then((response) => {
    if (response.status === 302 && response.headers && response.headers.length) {
      window.location.href = response.headers[0][1];
      return;
    }
    if (toRefresh) {
      window.location.reload();
      return;
    }
    if (response.json_content?.target && response.json_content?.html) {
      document.querySelector(response.json_content.target).innerHTML =
        response.json_content.html;
    } else if (target && response.json_content?.html) {
      document.querySelector(target).innerHTML = response.json_content.html;
    } else {
      console.log('WS response:', response);
    }
    if (response.status === 200 && closeModalSelector) {
      const modal = document.querySelector(closeModalSelector);
      if (modal) {
        hideGainzModal(modal);
      }
    }
    if (response.status === 200 && response.json_content?.toast_html) {
      appendToast(
        response.json_content.toast_html,
        response.json_content.toast_delay_ms
      );
    }
  });
}

function appendToast(htmlString, delayMs) {
  const toastContainer = document.querySelector('.toast-container');
  if (!toastContainer) {
    console.error('Toast container not found');
    return;
  }
  const parser = new DOMParser();
  const toast = parser.parseFromString(htmlString, 'text/html').body.firstChild;
  toastContainer.appendChild(toast);
  const delay = Number(delayMs) || 2000;
  setTimeout(() => {
    toast.remove();
  }, delay);
}

function dismissToast(event) {
  const toast = event.currentTarget.closest('.gainz-toast');
  if (toast) {
    toast.remove();
  }
}

function notifyUser(message, options) {
  const opts = options || {};
  const variant = opts.variant || 'success';
  const delayMs = opts.delayMs != null ? Number(opts.delayMs) : 2500;
  const toastHtml =
    '<div class="gainz-toast gainz-toast-' + variant + '" role="alert">' +
    '<button type="button" class="gainz-toast-close" data-function="click->dismissToast" aria-label="Close">×</button>' +
    '<p class="gainz-toast-message"></p>' +
    '</div>';
  const toastContainer = document.querySelector('.toast-container');
  if (toastContainer) {
    const parser = new DOMParser();
    const toast = parser.parseFromString(toastHtml, 'text/html').body.firstChild;
    toast.querySelector('.gainz-toast-message').textContent = message;
    toastContainer.appendChild(toast);
    const closeBtn = toast.querySelector('.gainz-toast-close');
    if (closeBtn) {
      closeBtn.addEventListener('click', dismissToast);
    }
    setTimeout(() => {
      toast.remove();
    }, delayMs);
  }
  if (opts.sound) {
    const audioContext = new AudioContext();
    const oscillator = audioContext.createOscillator();
    const gainNode = audioContext.createGain();
    oscillator.connect(gainNode);
    gainNode.connect(audioContext.destination);
    oscillator.frequency.value = 880;
    gainNode.gain.value = 0.15;
    oscillator.start();
    oscillator.stop(audioContext.currentTime + 0.2);
  }
  if (opts.vibrate && navigator.vibrate) {
    navigator.vibrate(200);
  }
}

function navigateTo(req_event) {
  const el = req_event.currentTarget;
  let url = el.getAttribute('data-nav');
  if (!url && el.tagName === 'SELECT') {
    url = el.options[el.selectedIndex].getAttribute('data-nav');
  }
  window.location.href = url;
}

function show_confirm_toast(req_event) {
  const trigger = req_event.currentTarget;
  const text = trigger.getAttribute('data-text');
  const endpoint = trigger.getAttribute('data-endpoint');
  const confirmLabel = trigger.getAttribute('data-confirm-label') || 'Confirm';
  const toastContainer = document.querySelector('.toast-container');
  if (!text || !endpoint || !toastContainer) {
    return;
  }

  const toast = document.createElement('div');
  toast.className = 'gainz-toast gainz-toast-warning';
  toast.setAttribute('role', 'alert');
  toast.innerHTML =
    '<button type="button" class="gainz-toast-close" data-function="click->dismissToast" aria-label="Close">×</button>' +
    '<p class="gainz-toast-message"></p>' +
    '<div class="gainz-toast-actions mt-2">' +
    `<button type="button" class="btn btn-danger btn-sm">${confirmLabel}</button>` +
    '</div>';
  toast.querySelector('.gainz-toast-message').textContent = text;

  const confirmBtn = toast.querySelector('.btn');
  confirmBtn.setAttribute('data-endpoint', `click->${endpoint}`);
  for (const attribute of trigger.attributes) {
    if (
      attribute.name.startsWith('data-') &&
      attribute.name !== 'data-function' &&
      attribute.name !== 'data-text' &&
      attribute.name !== 'data-endpoint' &&
      attribute.name !== 'data-confirm-label'
    ) {
      confirmBtn.setAttribute(attribute.name, attribute.value);
    }
  }

  toastContainer.appendChild(toast);
  setTimeout(() => {
    toast.remove();
  }, 7000);
}

document.addEventListener('keydown', (event) => {
  if (event.key !== 'Escape') {
    return;
  }
  document.querySelectorAll('.gainz-modal').forEach((modal) => {
    if (modal.style.display === 'flex') {
      hideGainzModal(modal);
    }
  });
});

function handle_attribute(element, attr) {
  const tokens = attr.value.trim().split(/\s+/);
  for (const value of tokens) {
    if (attr.name === 'data-endpoint') {
      const [eventName, routeName] = value.split('->');
      element.addEventListener(eventName, (ev) => ws_request(ev, routeName));
    } else if (attr.name === 'data-function') {
      const [eventName, funcName] = value.split('->');
      element.addEventListener(eventName, (ev) => window[funcName](ev));
    }
  }
}

function process_mutations(mutations) {
  for (const mutation of mutations) {
    if (mutation.type === 'attributes') {
      const attr = mutation.target.getAttributeNode(mutation.attributeName);
      if (attr && ['data-endpoint', 'data-function'].includes(attr.name)) {
        handle_attribute(mutation.target, attr);
      }
    } else if (mutation.type === 'childList') {
      for (const node of mutation.addedNodes) {
        if (node.nodeType !== Node.ELEMENT_NODE) continue;
        if (node.hasAttribute('data-endpoint')) {
          handle_attribute(node, node.getAttributeNode('data-endpoint'));
        }
        if (node.hasAttribute('data-function')) {
          handle_attribute(node, node.getAttributeNode('data-function'));
        }
        for (const el of node.querySelectorAll('[data-endpoint], [data-function]')) {
          const ep = el.getAttributeNode('data-endpoint');
          const fn = el.getAttributeNode('data-function');
          if (ep) handle_attribute(el, ep);
          if (fn) handle_attribute(el, fn);
        }
      }
    }
  }
}

const observer = new MutationObserver(process_mutations);
observer.observe(document.documentElement, {
  childList: true,
  subtree: true,
  attributes: true,
  attributeFilter: ['data-endpoint', 'data-function'],
});

document.querySelectorAll('[data-endpoint], [data-function]').forEach((element) => {
  const ep = element.getAttributeNode('data-endpoint');
  const fn = element.getAttributeNode('data-function');
  if (ep) handle_attribute(element, ep);
  if (fn) handle_attribute(element, fn);
});

////////////////////////////////////////////////////////////////////////
// New functions under here
////////////////////////////////////////////////////////////////////////

function resetModalContent(modal) {
  if (modal.hasAttribute('data-modal-persist')) {
    return;
  }
  const resetFn = modal.getAttribute('data-reset-function');
  if (resetFn && typeof window[resetFn] === 'function') {
    window[resetFn](modal);
    return;
  }
  modal.querySelectorAll('form').forEach((form) => form.reset());
}

function hideGainzModal(modal) {
  resetModalContent(modal);
  modal.style.display = 'none';
}

function ShowModal(event) {
  const trigger = event.currentTarget;
  const modalName = trigger.getAttribute('data-modal-name');
  const modal = document.getElementById(modalName);
  if (modal) {
    modal.style.display = 'flex';
  }
  const focusId = trigger.getAttribute('data-focus');
  if (focusId) {
    setTimeout(() => {
      const el = document.getElementById(focusId);
      if (el) {
        el.focus();
      }
    }, 100);
  }
}

function MorphingModal(event) {
  const trigger = event.currentTarget;
  const modalName = trigger.getAttribute('data-modal-name');
  const endpoint = trigger.getAttribute('data-routing');
  const modal = document.getElementById(modalName);
  const contentEl = document.getElementById(`${modalName}-content`);
  const focusId = trigger.getAttribute('data-focus');
  sendWsRequest(endpoint, trigger).then((response) => {
    contentEl.innerHTML = response.json_content.html;
    if (modal) {
      modal.style.display = 'flex';
    }
    if (focusId) {
      setTimeout(() => {
        const el = document.getElementById(focusId);
        if (el) {
          el.focus();
        }
      }, 100);
    }
  });
}

function toggleSiteNav(req_event) {
    const btn = req_event.currentTarget;
    const menu = document.getElementById('site-nav-menu');
    const isOpen = !menu.hidden;
    menu.hidden = isOpen;
    btn.setAttribute('aria-expanded', isOpen ? 'false' : 'true');
    if (!isOpen) {
        const close = (e) => {
            if (!btn.closest('.site-nav').contains(e.target)) {
                menu.hidden = true;
                btn.setAttribute('aria-expanded', 'false');
                document.removeEventListener('click', close);
            }
        };
        setTimeout(() => document.addEventListener('click', close), 0);
    }
}

function toggleGainzDropdown(req_event) {
    const btn = req_event.currentTarget;
    const menu = btn.nextElementSibling;
    const isOpen = !menu.hidden;
    document.querySelectorAll(".gainz-dropdown-menu").forEach((m) => { m.hidden = true; });
    if (!isOpen) {
        menu.hidden = false;
        const close = (e) => {
            if (!btn.closest(".gainz-dropdown").contains(e.target)) {
                menu.hidden = true;
                document.removeEventListener("click", close);
            }
        };
        setTimeout(() => document.addEventListener("click", close), 0);
    }
}

function submitParentForm(event) {
    const form = event.currentTarget.closest("form");
    if (form) {
        form.requestSubmit();
    }
}

function toggleReveal(req_event) {
    const trigger = req_event.currentTarget;
    const target = document.querySelector(trigger.getAttribute("data-reveal-target"));
    if (!target) {
        return;
    }
    const isOpen = !target.hidden;
    target.hidden = isOpen;
    trigger.setAttribute("aria-expanded", isOpen ? "false" : "true");
}

function startInlineEdit(req_event) {
    const display = req_event.currentTarget;
    const root = display.closest("[data-inline-edit]");
    const input = root.querySelector(".inline-edit-input");
    const placeholder = display.dataset.placeholder || "";
    const text = display.textContent.trim();
    input.value = (!text || text === placeholder) ? "" : text;
    display.classList.add("hidden");
    input.classList.remove("hidden");
    input.focus();
    input.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            input.blur();
        }
    }, { once: true });
}

function saveInlineEdit(req_event) {
    const input = req_event.currentTarget;
    const root = input.closest("[data-inline-edit]");
    const display = root.querySelector(".inline-edit-display");
    const endpoint = input.getAttribute("data-routing");
    const placeholder = display.dataset.placeholder || input.dataset.placeholder || "";
    const displayText = display.textContent.trim();
    const savedValue = (!displayText || displayText === placeholder) ? "" : displayText;
    const newValue = input.value.trim();

    const finishEdit = () => {
        display.classList.remove("hidden");
        input.classList.add("hidden");
    };

    if (newValue === savedValue) {
        finishEdit();
        return;
    }

    input.setAttribute("data-notes", newValue);
    sendWsRequest(endpoint, input).then((response) => {
        if (response.status === 200) {
            if (newValue) {
                display.textContent = newValue;
                display.classList.remove("font-italic");
            } else {
                display.textContent = placeholder;
                display.classList.add("font-italic");
            }
            finishEdit();
        }
    });
}

function CloseModal(event) {
  if (
    event.target.classList.contains('gainz-modal') ||
    event.target.closest('.gainz-modal-close')
  ) {
    const modal = event.target.closest('.gainz-modal');
    if (
      modal &&
      (!event.target.closest('.gainz-modal-content') ||
        event.target.closest('.gainz-modal-close'))
    ) {
      hideGainzModal(modal);
    }
  }
}
