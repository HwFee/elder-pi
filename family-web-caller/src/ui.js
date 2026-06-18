export function $(selector, root = document) {
  return root.querySelector(selector);
}

export function clearChildren(el) {
  while (el.firstChild) el.removeChild(el.firstChild);
}

export function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

export function show(el) { el.hidden = false; }
export function hide(el) { el.hidden = true; }
