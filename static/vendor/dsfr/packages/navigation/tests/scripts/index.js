/* eslint-disable no-new */

import '../style.scss';
import { DarkModeToggleSwitch } from '@ds-fr/schemes/src/scripts/';
import { Navigation } from '../../src/scripts';

function start () {
  new DarkModeToggleSwitch();
  new Navigation();
}

if (document.readyState !== 'loading') start();
else document.addEventListener('DOMContentLoaded', start);
