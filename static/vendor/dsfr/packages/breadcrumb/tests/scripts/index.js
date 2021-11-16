/* eslint-disable no-new */

import '../style.scss';
import { DarkModeToggleSwitch } from '@ds-fr/schemes/src/scripts/';
import { BreadcrumbButton } from '../../src/scripts';

function start () {
  new DarkModeToggleSwitch();
  new BreadcrumbButton();
}

if (document.readyState !== 'loading') start();
else document.addEventListener('DOMContentLoaded', start);
