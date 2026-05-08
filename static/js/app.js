const port = window.location.port ? `:${window.location.port}` : '';
const wsProtocol = location.protocol === 'https:' ? 'wss' : 'ws';
const wsUrl = `${wsProtocol}://${window.location.hostname}${port}/ws/`;

const ws = new WebSocket(wsUrl);

const requestMap = new Map();

function showLoading() {}
function hideLoading() {}

ws.onopen = () => {
  console.log('WebSocket connected');
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
  console.log('WebSocket disconnected');
};

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
    ws.send(message);
  });
}

function ws_request(event, endpoint) {
  const target = event.currentTarget.getAttribute('data-selector');
  const toRefresh = event.currentTarget.hasAttribute('data-refresh');

  sendWsRequest(endpoint, event.currentTarget).then((response) => {
    if (response.status === 302 && response.headers && response.headers.length) {
      window.location.href = response.headers[0][1];
      return;
    }
    if (toRefresh) {
      window.location.reload();
      return;
    }
    if (target && response.html_content) {
      document.querySelector(target).innerHTML = response.html_content;
      return;
    }
    if (response.json_content?.target && response.json_content?.html) {
      document.querySelector(response.json_content.target).innerHTML =
        response.json_content.html;
      return;
    }
    if (target && response.json_content?.html) {
      document.querySelector(target).innerHTML = response.json_content.html;
      return;
    }
    console.log('WS response:', response);
  });
}

document.addEventListener('keydown', (event) => {
  if (event.key !== 'Escape') {
    return;
  }
  document.querySelectorAll('.gainz-modal').forEach((modal) => {
    if (modal.style.display === 'flex') {
      modal.style.display = 'none';
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

function show_modal(event) {
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

function morphing_modal(event) {
  const trigger = event.currentTarget;
  const modalName = trigger.getAttribute('data-modal-name');
  const endpoint = trigger.getAttribute('data-routing');
  const modal = document.getElementById(modalName);
  if (modal) {
    modal.style.display = 'flex';
  }
  sendWsRequest(endpoint, trigger).then((response) => {
    const contentEl = document.getElementById(`${modalName}-content`);
    contentEl.innerHTML = response.json_content.html;
  });
}

function close_modal(event) {
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
      modal.style.display = 'none';
    }
  }
}
