// The Panoramax viewer bundles its own Font Awesome and ships its styles in its shadow DOM:
// the <style> auto-injected in <head> is useless and blocked by our CSP (no nonce).
// Must run before the viewer is imported, as Font Awesome reads this global at load time.
window.FontAwesomeConfig = { autoAddCss: false }
