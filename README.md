# Access4all

Référencement de l'accessibilité des ERP (Établissements Recevant du Public) en France.

## Prérequis

L'environnement de développement recommandé est Ubuntu 18.04 LTS, disposant des outils et paquets suivants :

- Python 3.7+
- [Pipenv](https://pipenv.kennethreitz.org/en/latest/)
- PostgreSQL 10.11+
- `postgresql-10-postgis-3`
- `postgresql-10-postgis-3-scripts`
- `libpq-dev`
- `python3.7-dev`

## Configurer les variables d'environnement

Créez un fichier `.env` à la racine du dépôt, définissant les variables d'environnement suivantes :

- `SECRET_KEY`: une chaine de caractères unique permettant de gérer les [opérations de chiffrement](https://docs.djangoproject.com/en/3.0/ref/settings/#secret-key).

Note: un fichier d'exemple `.env.sample` est disponible à la racine du dépôt.

## Installation

```
$ pipenv shell
$ pipenv install
```

## Configurer la base de données

:warning: Assurez-vous de disposer des paquets `libpq-dev` et `python3.7-dev`:

:bulb: Cette étape est inutile dans l'environnement de production Scalingo.

```
sudo apt install libpq-dev python3.7-dev
```

Connectez-vous à postgres en ligne de commande :

```
$ sudo su - postgres
```

Puis lancez `psql`:

```
$ psql
```

Dans `psql`, lancez ces commandes :

```
CREATE DATABASE access4all;
CREATE USER access4all WITH PASSWORD 'access4all';
ALTER ROLE access4all SET client_encoding TO 'utf8';
ALTER ROLE access4all SET default_transaction_isolation TO 'read committed';
ALTER ROLE access4all SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE access4all TO access4all;
```

Activez le support postgis pour la base `access4all` :

```
$ psql access4all
> CREATE EXTENSION postgis;
```

Puis, initialisez la base de données :

```
$ python manage.py migrate
```

Créez un superutilisateur :

```
$ python manage.py createsuperuser
```

## Lancer le serveur

```
$ python manage.py runserver
```

L'application est alors accessible à l'adresse [http://127.0.0.1:8000/](http://127.0.0.1:8000/).

## Générer et appliquer les migrations du modèle de données

Générer les migrations :

```
$ python manage.py makemigrations
```

Appliquer les migrations :

```
$ python manage.py migrate
```

Vous devez relancer le serveur pour que les changements soient pris en compte.

## Réinitialiser les migrations

Une commande spécifique est disponible :

```
$ python manage.py reset_migrations
```

## Réinitialiser la base de données

:warning: Attention, cela supprimera toutes les données dans la base.

```
$ python manage.py flush
```

## Accéder au shell Django

```
$ python manage.py shell
```

# Déploiement

L'application est hébergée sur la plateforme [Scalingo](https://scalingo.com/).

## Configuration préliminaire

Il faut installer l'outil en ligne de commande `scalingo`. Vous trouverez les instructions [ici](https://doc.scalingo.com/cli).

Une fois l'installation effectuée, vous pouvez ajouter votre clé publique SSH :

```
$ scalingo keys-add <user> ~/.ssh/id_rsa.pub
```

Note: replacez `<user>` par le nom que vous voulez donner à votre clé sur Scalingo.

Vous pouvez maintenant vous authentifier en ligne de commande :

```
$ scalingo login
```

Ensuite, il faut ajouter le remote git suivant :

```
git remote add scalingo git@ssh.osc-fr1.scalingo.com:access4all.git
```

Enfin, il faut positionner les variables d'environnement applicatives :

```
$ scalingo -a access4all env-set SECRET_KEY="<insérez une chaîne de caractère arbitraire ici>"
```

Au besoin, redémarrez le conteneur applicatif pour prendre en compte une éventuelle modification :

```
$ scalingo --app access4all restart
```

## Déployer l'application

Le déploiement s'effectue au moyen de la simple commande git :

```
$ git push scalingo master
```
