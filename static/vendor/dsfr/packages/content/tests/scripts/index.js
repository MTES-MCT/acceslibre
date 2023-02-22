/* eslint-disable no-new */

import '../style.scss';

import { ContentMediaFixLegacy } from '../../src/scripts';
import { DarkModeToggleSwitch } from '@ds-fr/schemes/src/scripts/';

function start () {
  new ContentMediaFixLegacy();
  new DarkModeToggleSwitch();
}

if (document.readyState !== 'loading') start();
else document.addEventListener('DOMContentLoaded', start);
