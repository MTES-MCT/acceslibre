# Acceslibre

Référencement de l'accessibilité des ERP (Établissements Recevant du Public) en France.

**Note:** Ce projet a historiquement été créé et conçu sous le nom _access4all_, avant d'être rebaptisé _acceslibre_. Le nom technique _access4all_ reste utilisé dans la base de code et doit être perçu comme équivalent, même s'il n'apparâit plus sur l'interface publique du site.

## Prérequis

L'environnement de développement recommandé est Ubuntu 20.04 LTS, disposant des outils et paquets suivants :

- Python 3.8+
- [Pipenv](https://pipenv.kennethreitz.org/en/latest/)
- PostgreSQL 12.2+
- `postgresql-12-postgis-3`
- `postgresql-12-postgis-3-scripts`
- `libpq-dev`
- `python3.8-dev`
- `Django` en version 3 ou supérieure
- [Node](https://nodejs.org/fr/) v14+ + Npm
- Optionnel: [Docker](https://docs.docker.com/get-docker/) et [docker-compose](https://docs.docker.com/compose/install/)

## Configurer les variables d'environnement

Créez un fichier `.env` à la racine du dépôt, définissant les variables d'environnement suivantes :

- `DJANGO_SETTINGS_MODULE`: Le nom du module Python définissant la configuration Django. Sa valeur peut être `core.settings_prod` pour l'environnement de production, ou `core.settings_dev` pour l'environnement de développement local.
- `EMAIL_HOST`: Host du serveur SMTP
- `EMAIL_PORT`: Port du serveur SMTP
- `EMAIL_HOST_USER`: Nom d'utilisateur SMTP
- `EMAIL_HOST_PASSWORD`: Mot de passe SMTP
- `MATTERMOST_HOOK`: Url du [webhook entrant Mattermost](https://docs.mattermost.com/developer/webhooks-incoming.html) utilisé pour envoyer des notifications techniques
- `SCALINGO_APP`: Le nom de l'application Scalingo, toujours `access4all`
- `SECRET_KEY`: Une chaine de caractères unique permettant de garantir la sécurité des [opérations de chiffrement](https://docs.djangoproject.com/en/3.0/ref/settings/#secret-key)
- `SENTRY_DSN`: La chaine de connexion à [Sentry](https://sentry.io/), l'outil de rapport d'erreur que nous utilisons en production.

**Notes :**

- Un fichier d'exemple `.env.sample` est disponible à la racine du dépôt.
- Les jetons d'authentification pour l'API Sirene de l'INSEE [s'obtiennent ici](https://api.insee.fr/catalogue/site/themes/wso2/subthemes/insee/pages/item-info.jag?name=Sirene&version=V3&provider=insee).
- En production, nous utilisons les services de [Mailjet](https://app.mailjet.com/) pour gérer l'envoi d'emails.
- Pour travailler localement, l'utilisation du [backend d'email "console"](https://docs.djangoproject.com/en/3.0/topics/email/#console-backend) est recommandée.
- La prise en compte de l'assignation des variables d'environnement définies dans ce fichier `.env` ne sont effectives qu'après avoir activé l'environnement virtuel de développement Python, au moyen de la commande `pipenv shell`. L'exécution de cette commande est également nécessaire pour prendre en compte chaque modification de leur valeur.
- Vous pouvez lancer un serveur de développement en positionnant la variable d'environnement `DJANGO_SETTINGS_MODULE` manuellement à l'appel de la ligne de commande :

      $ DJANGO_SETTINGS_MODULE=core.settings_prod npm run start:both

## Installation

```
$ pipenv shell
$ pipenv install -d
```

## Base de données avec Docker Compose

Pour lancer les services :
```
docker-compose up
# ou pour lancer en background
docker-compose up -d
```

L'interface web [Adminer](https://www.adminer.org/) est accessible sur http://localhost:8080/?pgsql=database&username=access4all&db=access4all&ns=public.

:bulb: Pour les commandes dans le container PG, préfixer les commandes avec :
```
docker-compose exec database <...>
# Ex: docker-compose exec database psql -U access4all
```


## Configurer la base de données

:warning: Assurez-vous de disposer des paquets `libpq-dev` et `python3.8-dev`:

:bulb: Cette étape est inutile dans l'environnement de production Scalingo.

```
sudo apt install libpq-dev python3.8-dev
```

Créez la base de données :

```shell
psql -U postgres < bin/create_db.sql
# ou avec docker-compose
cat bin/create_db.sql | docker-compose exec -T database psql -U access4all
```

> Note: pour jouer les tests, vous devez également exécuter cette commande :
>
>     ALTER ROLE access4all SUPERUSER;
>
> Cette commande ne doit **jamais** être exécutée sur la base de production.

Puis, initialisez la base de données :

```
$ python manage.py migrate
```

Chargez les [révisions](https://django-reversion.readthedocs.io/) initiales de modèles :

```
$ python manage.py createinitialrevisions
```

Créez un superutilisateur :

```
$ python manage.py createsuperuser
```

Charger les jeux de données initiaux :

```
$ python manage.py loaddata erp/fixtures/communes.json
```

## Lancer le serveur de développement

```
# Front
npm start
# Back
python manage.py runserver

# Ou simultanément
npm run start:both
```

L'application est alors accessible à l'adresse [http://localhost:8000/](http://localhost:8000/).

## Configuration locale de dévelopement

La configuration de développement des paramètres applicatifs se fait dans le fichier `core/settings_dev.py`. Vous pouvez également définir votre propre module sur le même modèle et l'importer par le biais de la variable d'environnement `DJANGO_SETTINGS_MODULE`.

N'oubliez pas de relancer `python manage.py runserver` ou `npm run start:both`pour prendre en compte tout changement effectué à ce niveau.

## Importer les données initiales

### Importer les communes

```
$ python manage.py import_communes
```

### Importer les données c-conforme

```
$ python manage.py import_cconforme
```

## Accéder au shell Django

```
$ python manage.py shell
```

# Déploiement

See [Déploiement et Production](https://github.com/MTES-MCT/acceslibre/wiki/D%C3%A9ploiement-et-Production)

## Licence

Le code source du logiciel est publié sous licence [MIT](https://fr.wikipedia.org/wiki/Licence_MIT).
