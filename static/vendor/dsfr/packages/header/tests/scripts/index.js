/* eslint-disable no-new */

import '../style.scss';
import { DarkModeToggleSwitch } from '@ds-fr/schemes/src/scripts/';
import { addClass } from '@ds-fr/utilities/src/scripts/';
import { Navigation } from '@ds-fr/navigation/src/scripts/';

function start () {
  new DarkModeToggleSwitch();
  new Navigation();
}

if (document.readyState !== 'loading') start();
else document.addEventListener('DOMContentLoaded', start);

addClass(document.body, '${prefix}-scheme');
addClass(document.body, '${prefix}-scheme--grey-100');
