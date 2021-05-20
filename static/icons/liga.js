/* A polyfill for browsers that don't support ligatures. */
/* The script tag referring to this file must be placed before the ending body tag. */

/* To provide support for elements dynamically added, this script adds
   method 'icomoonLiga' to the window object. You can pass element references to this method.
*/
(function () {
    'use strict';
    function supportsProperty(p) {
        var prefixes = ['Webkit', 'Moz', 'O', 'ms'],
            i,
            div = document.createElement('div'),
            ret = p in div.style;
        if (!ret) {
            p = p.charAt(0).toUpperCase() + p.substr(1);
            for (i = 0; i < prefixes.length; i += 1) {
                ret = prefixes[i] + p in div.style;
                if (ret) {
                    break;
                }
            }
        }
        return ret;
    }
    var icons;
    if (!supportsProperty('fontFeatureSettings')) {
        icons = {
            'home': '&#xe900;',
            'house': '&#xe900;',
            'office': '&#xe905;',
            'buildings': '&#xe905;',
            'files-empty': '&#xe925;',
            'files': '&#xe925;',
            'phone': '&#xe942;',
            'telephone': '&#xe942;',
            'map': '&#xe94b;',
            'guide': '&#xe94b;',
            'clock': '&#xe94e;',
            'time2': '&#xe94e;',
            'download': '&#xe960;',
            'save': '&#xe960;',
            'upload': '&#xe961;',
            'load': '&#xe961;',
            'bubble2': '&#xe96e;',
            'comment2': '&#xe96e;',
            'bubbles3': '&#xe96f;',
            'comments3': '&#xe96f;',
            'user': '&#xe971;',
            'profile2': '&#xe971;',
            'users': '&#xe972;',
            'group': '&#xe972;',
            'user-tie': '&#xe976;',
            'user5': '&#xe976;',
            'search': '&#xe986;',
            'magnifier': '&#xe986;',
            'zoom-in': '&#xe987;',
            'magnifier2': '&#xe987;',
            'shrink': '&#xe98a;',
            'collapse': '&#xe98a;',
            'key': '&#xe98d;',
            'password': '&#xe98d;',
            'lock': '&#xe98f;',
            'secure': '&#xe98f;',
            'unlocked': '&#xe990;',
            'lock-open': '&#xe990;',
            'trophy': '&#xe99e;',
            'cup': '&#xe99e;',
            'road': '&#xe9b1;',
            'asphalt': '&#xe9b1;',
            'earth': '&#xe9ca;',
            'globe2': '&#xe9ca;',
            'link': '&#xe9cb;',
            'chain': '&#xe9cb;',
            'flag': '&#xe9cc;',
            'report': '&#xe9cc;',
            'attachment': '&#xe9cd;',
            'paperclip': '&#xe9cd;',
            'eye': '&#xe9ce;',
            'views': '&#xe9ce;',
            'star-empty': '&#xe9d7;',
            'rate': '&#xe9d7;',
            'star-full': '&#xe9d9;',
            'rate3': '&#xe9d9;',
            'male-female': '&#xe9de;',
            'man-woman': '&#xe9de;',
            'toilet': '&#xe9de;',
            'toilets': '&#xe9de;',
            'plus': '&#xea0a;',
            'add': '&#xea0a;',
            'enter': '&#xea13;',
            'signin': '&#xea13;',
            'radio-unchecked': '&#xea56;',
            'radio-button3': '&#xea56;',
            'whatsapp': '&#xea93;',
            'brand13': '&#xea93;',
          '0': 0
        };
        delete icons['0'];
        window.icomoonLiga = function (els) {
            var classes,
                el,
                i,
                innerHTML,
                key;
            els = els || document.getElementsByTagName('*');
            if (!els.length) {
                els = [els];
            }
            for (i = 0; ; i += 1) {
                el = els[i];
                if (!el) {
                    break;
                }
                classes = el.className;
                if (/icon-/.test(classes)) {
                    innerHTML = el.innerHTML;
                    if (innerHTML && innerHTML.length > 1) {
                        for (key in icons) {
                            if (icons.hasOwnProperty(key)) {
                                innerHTML = innerHTML.replace(new RegExp(key, 'g'), icons[key]);
                            }
                        }
                        el.innerHTML = innerHTML;
                    }
                }
            }
        };
        window.icomoonLiga();
    }
}());
