function Menu(root) {
  const menuModalEl = document.querySelector("#modal-menu-mobile");

  function showMenu(event) {
    event.preventDefault();
    menuModalEl.style.opacity = "1";
    menuModalEl.style.visibility = "visible";
  }

  root.addEventListener("click", showMenu);
}

export default Menu;
