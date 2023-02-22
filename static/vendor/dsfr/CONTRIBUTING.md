# Contributing

## Git

Nous utilisons des [conventional commits](https://www.conventionalcommits.org/en/v1.0.0/) afin d'automatiser la génération automatique de Changelog au sein des différents packages du design system via [Lerna.js](https://lerna.js.org/), ainsi que des numéros de version des différents packages via le schéma [SemVer](https://semver.org/#summary) (Semantic Versionning).
Les commits doivent donc s'écrire sous la forme suivante :

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

La Changelog de chaque package sera donc mis à jour automatiquement en fonction du `type` de commit :
* **fix**: Un commit de type `fix` permet de patcher un bug ([\[PATCH\]](https://semver.org/#summary))
* **feat**: Un commit de type `feat` permet d'introduire une nouvelle fonctionnalité ([\[MINOR\]](https://semver.org/#summary))
* **BREAKING CHANGE**: Un commit avec un footer `BREAKING CHANGE:` introduit un changement important dans le code ([\[MAJOR\]](https://semver.org/#summary))
* D'autres types que `feat` et `fix` peuvent être utilisés, nous utilisons [@commitlint/config-conventional](https://github.com/conventional-changelog/commitlint/tree/master/%40commitlint/config-conventional), qui recommande l'utilisation des principaux types suivants : `build`, `chore`, `ci`, `docs`, `style`, `refactor`, `perf`, `test`

Lors d'une release, Lerna va automatiquement créer un commit de type `chore(packages): release` avec comme description l'ensemble des packages qui ont été créés mis à jour, avec leurs bons numéros de version

### Exemples
Commit simple :

```
docs: add sassdoc info
```

Commit avec `scope`, description et `BREAKING CHANGE` footer
```
fix(core): change mixin name my-mixin to my-new-mixin

BREAKING CHANGE: new name for the mixin my-mixin
```

### Test automatiques

Un hook de pre-commit est utilisé pour lancer les tests automatisés avant de valider un commit. Il permet de s'assurer que le code ajouté respecte bien l'ensemble des tests. Pour passer la vérification de ces tests (Lors par exemple de modifications uniquement sur le process de build), il est possible de passer un paramètre --no-verify lors du commit. Exemple :

```
git commit -m "build: add webpack" --no-verify
```

## Local
Le Design System est construit sous NodeJS, et utilise principalement Yarn et Webpack. Afin de l'installer de manière locale, il suffit de cloner ce repository et d'installer les dépendances NPM avec la commande `yarn`.  Pour lancer le serveur local et travailler sur le Design System, il est ensuite nécessaire de sélectionner le package sur lequel travailler, et lancer la commande `yarn run start` :

```
cd packages/buttons
yarn run start
```

## Packages

Le Design System est un monorepo proposant différents composants, listés dans le dossier `packages`. Certains de ces packages sont dépendants les uns des autres. Afin d'ajouter une dépendance à un package, il est nécessaire d'utiliser la commande `lerna add`. Ainsi, pour ajouter par exemple le package `core` en tant que dépendance du package `buttons`, il faut utiliser la commande suivante :

```
lerna add @ds-fr/core --scope=@ds-fr/buttons
```

## Sassdoc
Des commentaires spéciaux sont utilisés sur l'ensemble des fichier `scss`, afin de permettre la génération d'une [Sassdoc](http://sassdoc.com/) automatiquement, documentant l'ensemble des `mixins` et `functions` utilisés sur le Design System :

```
yarn run styleguide
```
Cette commande permet la génération de la doc dans le dossier `sassdoc`, à la racine du projet.

## Tests
Afin de s'assurer de la qualité du code, nous utilisons des tests automatisés qu'il est nécessaire d'exécuter régulièrement pour vérifier que le code du Design System reste valide et cohérent.

### Sass
Afin de tester les différentes `functions` et `mixins`, nous utilisons jest et sass-true, afin d'effectuer une batterie de tests, présents dans un fichier `tests/_sass-tests.scss` au sein de certains packages.

Pour vérifier l'ensemble de ces tests, il faut utiliser la commande suivante :

```
yarn run test:sass
```

### Accessibilité
Pour tester de manière automatisée l'accessibilité des composants du Design System, nous utilisons [Pa11y](https://pa11y.org/) sur les pages de tests des différents packages :

```
yarn run test:pa11y
```

Afin d'exclure un élément de ces tests, il est possible de lui attribuer une class spécifique `.is-pa11y-hidden`
