
# Design System

## Table des matières
- [Installation](#installation)
- [Fonctionnement](#fonctionnement)
- [Utilisation](#utilisation)
- [Composants](#composants)

## Installation
L'architecture du Design System (nommé ci-après **DS** prévoit l'installation de celui-c via des packages NPM et des dépendances entre composants.

### Prérequis
Les composants du **DS** sont distribués au travers de l’écosystème NPM, il est de ce fait nécessaire d'installer [NodeJS](https://nodejs.org/en/).

### Installation des composants
Afin d'installer des composants du **DS**, il est nécessaire d'avoir un fichier `package.json` à la racine de votre projet. Il est possible d'en créer un directement via la commande `npm init`.

Afin d'installer par exemple le composant `body` permettant de mettre en place les styles principaux du **DS** comme la typographie, il suffit de lancer la commande suivante :

```
npm install @ds-fr/body
```
Le composant `body` dépend du composant `core`, de ce fait ce composant sera également installé automatiquement. Il est possible d'installer plusieurs packages en les écrivant les uns à la suite des autres après la commande `npm install` :

```
npm install @ds-fr/body @ds-fr/buttons @ds-fr/callout
```

Il est également possible d'installer les composants avec [Yarn](https://yarnpkg.com/) :

```
yarn add @ds-fr/body
```

Veuillez consulter l'[arbre de dépendance](#dependances) afin de savoir quels composants sont dépendants d'autres, et lesquels seront installés automatiquement avec les commandes citées plus haut.

## Fonctionnement

### BEM
Le **DS** utilise la méthodologie [**BEM**]([https://css-tricks.com/bem-101/]([http://getbem.com/naming/](http://getbem.com/naming/))) (Block - Element - Modifier) comme convention de nommage des classes CSS. Elle permet aux développeurs une meilleure compréhension de la relation entre HTML et CSS dans un projet donné.

Selon cette méthodologie, un block représente le plus haut niveau d'abstraction d'un nouveau composant, par exemple `.parent`.
Des éléments (ou enfants), peuvent être placés à l'intérieur de ces blocks, et sont désignés par deux underscore précédés du nom du block : `.parent__element`.
Les modifiers quant à eux, servent à manipuler les blocs, de manière à les styliser de manière indépendante en s'assurant de ne pas induire de changement à des blocks sans aucun rapport avec celui-ci. Ils sont notés à l'aide de deux tirets précédés du nom du block comme suit : `.parent--modifier`.

## Utilisation

### Typographies
Le **DS**, et plus précisément le composant `core`, utilise 2 typographies différentes, à savoir la Marianne et la Spectral, avec des graisses différentes pour chacune. Lors de l'installation de celui-ci, ils vous est demandé le dossier dans lequel copier ces typographies (par défault, un dossiers `fonts`).
Il est possible de spécifier le chemin d'accès à ces typographies via une variable Sass `$static-font-path`

### Icônes
Le **DS** utilise comme système d'icônes un sprite SVG. L'ensemble des icônes sont de ce fait regroupées dans un seul fichier `sprite.svg`.
Il est donc possible d'ajouter une icône à votre fichier HTML en utilisant une balise `svg` et précisant l'identifiant de l'icône à utiliser, par exemple `#account-line`
Lors de l'installation du composant `icons`, ils vous sera demandé dans quel dossier copier ce sprite (par défaut, `icons`)

**Note** : *Pour plus d'informations, consultez la documentation relative au composant `icons`*

### Sass

Si vous souhaitez par exemple utiliser les composants `core`, `icons` et `buttons`, vous pouvez les importer de cette façon dans votre fichier `.scss` principal :

```scss
@import 'node_modules/@ds-fr/core/main';
@import 'node_modules/@ds-fr/icons/main';
@import 'node_modules/@ds-fr/buttons/main';
```

**Note** : *Attention, l'ordre des imports est important, se référer aux dépendances ci-dessous.*

## Composants

### Dépendances

```text
core
└── icons
    ├── links
    ├── buttons
    ├── inputs
    │   ├── forms
└── utilities
```

### Liste
- [core](src/packages/core)
- [body](src/packages/body)
- [content](src/packages/content)
- [links](src/packages/links)
- [medias](src/packages/medias)
- [callout](src/packages/callout)
- [color-schemes](src/packages/color-schemes)
- [icons](src/packages/icons)
- [buttons](src/packages/buttons)
- [forms](src/packages/forms)
- [highlights](src/packages/highlights)
- [grid](src/packages/grid)
- [inputs](src/packages/inputs)
- [pagination](src/packages/pagination)
- [utilities](src/packages/utilities)
