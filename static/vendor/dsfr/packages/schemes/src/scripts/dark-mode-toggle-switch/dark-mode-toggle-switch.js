import { addClass, removeClass } from '@ds-fr/utilities/src/scripts/';

const DM = '${prefix}-dark-mode';

class DarkModeToggleSwitch {
  constructor () {
    this.init();
  }

  init () {
    this.scheme = localStorage.getItem('scheme')
      ? localStorage.getItem('scheme')
      : null;

    if (this.scheme === null) {
      if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
        this.scheme = 'dark';
        localStorage.setItem('scheme', 'dark');
      } else this.scheme = 'light';
    }

    this.body = document.body;

    if (this.scheme === 'dark') {
      const className = this.body.className + ' ' + DM;

      if (className.indexOf(DM + '--sudden') > -1) this.body.className = className;
      else {
        this.body.className = className + ' ' + DM + '--sudden';

        setTimeout(() => {
          this.body.className = className;
        }, 300);
      }
    }

    this.checkbox = document.getElementById(DM + '-toggle-switch');

    if (this.scheme === 'dark') this.checkbox.checked = true;

    this.checkbox.addEventListener('change', this.change.bind(this));
  }

  change () {
    if (this.checkbox.checked) {
      this.scheme = 'dark';
      localStorage.setItem('scheme', 'dark');
      addClass(this.body, DM);
    } else {
      this.scheme = 'light';
      localStorage.setItem('scheme', 'light');
      removeClass(this.body, DM);
    }
  }
}

export { DarkModeToggleSwitch };
