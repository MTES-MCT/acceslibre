function addClass(el, class_) {
  el.classList.add(class_);
}

function findAll(sel) {
  return [].slice.call(document.querySelectorAll(sel), 0);
}

function hide(el) {
  el.dataset.previousDisplay = window.getComputedStyle(el).display;
  el.style.display = "none";
}

function ready(fn) {
  window.addEventListener("DOMContentLoaded", fn);
}

function removeClass(el, class_) {
  el.classList.remove(class_);
}

function show(el) {
  const { previousDisplay } = el.dataset;
  if (previousDisplay) {
    delete el.dataset.previousDisplay;
    el.style.display = previousDisplay;
  } else {
    el.style.display = "block";
  }
}

export default {
  addClass,
  findAll,
  hide,
  ready,
  removeClass,
  show,
};
