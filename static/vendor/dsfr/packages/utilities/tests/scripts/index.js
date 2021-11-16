/* eslint-disable no-new */

import '../style.scss';
import { DarkModeToggleSwitch } from '@ds-fr/schemes/src/scripts/';
import { Collapse } from '@ds-fr/utilities/src/scripts/';

function start () {
  new DarkModeToggleSwitch();
  new Collapse();
}

if (document.readyState !== 'loading') start();
else document.addEventListener('DOMContentLoaded', start);
