# @ds-fr/selects

## Dépendance
```shell
selects
└─ core
└─ forms
```

## Installation
Installation via NPM:
```
npm install @ds-fr/selects
```
Via Yarn :
```
yarn add install @ds-fr/selects
```

## Utilisation
Afin d'utilise le composant `selects`, il est nécessaire d'importer le composant ainsi que ses dépendances :
```scss
@import 'node_modules/@ds-fr/core/main';
@import 'node_modules/@ds-fr/forms/main';
@import 'node_modules/@ds-fr/selects/main';
```

Liste déroulante
pour le placeholder, ajoutez une première option avec les attributs selected disabled et hidden.

Exemple :

```html
<label class="rf-label" for="unique-id">Label for select</label>
<select class="rf-select" id="unique-id">
    <option value="" selected disabled hidden>- placeholder -</option>
    <option value="1">option 1</option>
    <option value="2">option 2</option>
    <option value="3">option 3</option>
</select>
```

## Documentation

Consulter [la documentation](#) sur les selects
