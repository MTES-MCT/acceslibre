/**
 * Polyfill pour IE11 qui ne supporte pas object-fit. On met l'image en background sur l'élément img et un svg vide en source
 */

class ContentMediaFixLegacy {
  constructor () {
    if ('objectFit' in document.documentElement.style === false) this.fix();
  }

  fix () {
    Array.prototype.forEach.call(document.querySelectorAll('.rf-content-media__img img'), image => {
      (image.runtimeStyle || image.style).background = 'url("' + image.src + '") no-repeat 50%/cover';
      image.src = 'data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' width=\'' + image.width + '\' height=\'' + image.height + '\' %3E%3C/svg%3E';
    });
  }
}

export { ContentMediaFixLegacy };
