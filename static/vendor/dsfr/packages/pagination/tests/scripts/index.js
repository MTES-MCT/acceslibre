/* eslint-disable no-new */

import '../style.scss';
import { DarkModeToggleSwitch } from '@ds-fr/schemes/src/scripts/';

function start () {
  new DarkModeToggleSwitch();
}

if (document.readyState !== 'loading') start();
else document.addEventListener('DOMContentLoaded', start);
