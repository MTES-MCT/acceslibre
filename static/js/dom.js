function addClass(el, ...args) {
  for (const class_ of args) {
    el.classList.add(class_)
  }
}

function findAll(sel) {
  return [].slice.call(document.querySelectorAll(sel), 0)
}

function mountOne(selector, fn) {
  const node = document.querySelector(selector)
  if (node) {
    fn(node)
  }
}

function mountAll(selector, fn) {
  findAll(selector).forEach(fn)
}

function preventDefault(event) {
  event.preventDefault()
}

function ready(fn) {
  window.addEventListener('DOMContentLoaded', fn)
}

function removeClass(el, ...args) {
  for (const class_ of args) {
    el.classList.remove(class_)
  }
}

export default {
  addClass,
  mountAll,
  mountOne,
  preventDefault,
  ready,
  removeClass,
}
