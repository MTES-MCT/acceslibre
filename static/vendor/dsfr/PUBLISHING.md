# Publishing

## Publication
La publication du Design System sur NPM se fait via l'outil [Lerna.js](https://lerna.js.org/), qui va s'occuper automatiquement du versionning des packages en fonction des différents commits effectués depuis la dernière publication (cf [Git](#git))

La commande utilisée pour publier une nouvelle version des packages impactés est la suivante :

```
yarn run publish
```

Cette commande permet de lancer des tests automatisés (Sur les fichiers scss et l'accessibilité), et de publier les nouvelles versions des packages si les précédents tests sont passés.

### Test NPM local : Verdaccio
Afin de tester la publication des packages, il est possible de mettre en place un NPM local avec l'outil [Verdaccio](https://verdaccio.org/). Il est également nécessaire de cloner à nouveau le repo à un autre emplacement, pour éviter de provoquer la montée en version des packages sur le repo principal.

Afin d'installer Verdaccio de manière globale :
```
npm install --global verdaccio
```

Il suffit ensuite de lancer simplement la commande `verdaccio`, afin de faire tourner une instance locale, sur une url du type `http://localhost:4873/`.
Il est ensuite nécessaire d'éditer le fichier `lerna.json`, afin de préciser le registry à utiliser pour la publication (Dans notre exemple : `"registry": "http://localhost:4873/"`)

Afin de tester les packages publiés sur ce NPM local, il est nécessaire de préciser le `registry` où récupérer ces derniers, par exemple :

```
yarn add @ds-fr/buttons --registry http://localhost:4873
```
