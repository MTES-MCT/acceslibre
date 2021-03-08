function ready(fn) {
  window.addEventListener("DOMContentLoaded", fn);
}

function findAll(sel) {
  return [].slice.call(document.querySelectorAll(sel), 0);
}

export default {
  findAll,
  ready,
};
