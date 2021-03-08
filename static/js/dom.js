function ready(fn) {
  window.addEventListener("DOMContentLoaded", fn);
}

function findOne(sel, parent) {
  return (parent || document).querySelector(sel);
}

function findAll(sel) {
  return [].slice.call(document.querySelectorAll(sel), 0);
}

export default {
  findOne,
  findAll,
  ready,
};
