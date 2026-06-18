export function $(selector) {
  const el = document.querySelector(selector);
  if (!el) throw new Error(`Element not found: ${selector}`);
  return el;
}

export function show(el) {
  el.hidden = false;
}

export function hide(el) {
  el.hidden = true;
}

export function clearChildren(el) {
  while (el.firstChild) {
    el.removeChild(el.firstChild);
  }
}

export function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

export function setStatus(online) {
  const bar = $('.status-bar');
  const text = $('#status-text');
  bar.classList.remove('online', 'offline');
  if (online) {
    bar.classList.add('online');
    text.textContent = '在线';
  } else {
    bar.classList.add('offline');
    text.textContent = '离线';
  }
}
