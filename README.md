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

- `SECRET_KEY`: Une chaine de caractères unique permettant de garantir la sécurité des [opérations de chiffrement](https://docs.djangoproject.com/en/3.0/ref/settings/#secret-key)
- `SENTRY_DSN`: La chaine de connexion à [Sentry](https://sentry.io/), l'outil de rapport d'erreur que nous utilisons en production.
- `EMAIL_HOST`: Host du serveur SMTP
- `EMAIL_PORT`: Port du serveur SMTP
- `EMAIL_HOST_USER`: Nom d'utilisateur SMTP
- `EMAIL_HOST_PASSWORD`: Mot de passe SMTP

**Notes :**

- Un fichier d'exemple `.env.sample` est disponible à la racine du dépôt.
- En production, nous utilisons les services de [Mailjet](https://app.mailjet.com/) pour gérer l'envoi d'emails.
- Pour travailler localement, l'utilisation du [backend d'email "console"](https://docs.djangoproject.com/en/3.0/topics/email/#console-backend) est recommandé.

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
\c access4all;
CREATE EXTENSION postgis;
CREATE EXTENSION pg_trgm;
CREATE EXTENSION unaccent;
CREATE TEXT SEARCH CONFIGURATION french_unaccent( COPY = french );
ALTER TEXT SEARCH CONFIGURATION french_unaccent
ALTER MAPPING FOR hword, hword_part, word
WITH unaccent, french_stem;
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

Créez un superutilisateur :

```
$ python manage.py createsuperuser
```

Charger les jeux de données initiaux :

```
$ python manage.py loaddata erp/fixtures/communes.json
```

## Lancer le serveur

```
$ python manage.py runserver
```

L'application est alors accessible à l'adresse [http://127.0.0.1:8000/](http://127.0.0.1:8000/).

## Configuration locale (développement)

La configuration de production des paramètres applicatifs se fait dans le fichier `access4all/settings.py`. Il est cependant possible de surcharger les paramètres en créant un fichier `local_settings.py` dans le même répertoire, qui sera alors interprété localement pour servir l'application.

Par exemple :

```python
DEBUG = True

ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
]

INTERNAL_IPS = [
    "127.0.0.1",
]

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

INSTALLED_APPS = [
    "django_extensions",
    "nested_admin",
    "import_export",
    "reset_migrations",
    "django_admin_listfilter_dropdown",
    "erp.apps.ErpConfig",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.gis",
    "django.contrib.postgres",
    "corsheaders",
    "logentry_admin",
    "django_better_admin_arrayfield.apps.DjangoBetterAdminArrayfieldConfig",
    "rest_framework",
    "rest_framework_gis",
    "debug_toolbar",
]

CORS_ORIGIN_ALLOW_ALL = True

MIDDLEWARE = [
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

CACHES = {
    "default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache",}
}

CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False
```

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

## Importer les données initiales

### Importer les communes

```
$ python manage.py import_communes
```

### Importer les données c-conforme

```
$ python manage.py import_cconforme
```

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
$ scalingo -a access4all env-set SECRET_KEY="<insérez la valeur ici>"
$ scalingo -a access4all env-set SENTRY_DSN="<insérer la valeur ici>"
$ scalingo -a access4all env-set EMAIL_HOST="<insérez la valeur ici>"
$ scalingo -a access4all env-set EMAIL_PORT=<insérez la valeur ici>
$ scalingo -a access4all env-set EMAIL_HOST_USER="<insérez la valeur ici>"
$ scalingo -a access4all env-set EMAIL_HOST_PASSWORD="<insérez la valeur ici>"
```

Au besoin, redémarrez le conteneur applicatif pour prendre en compte une éventuelle modification :

```
$ scalingo --app access4all restart
```

## Activer l'extension postgis

Les instructions de mise en place et d'activation postgis sont disponibles [à cette adresse](https://doc.scalingo.com/languages/python/django/geodjango).

## Déployer l'application

Le déploiement s'effectue au moyen de la simple commande git :

```
$ git push scalingo master
```

## Dump manuel de la base de données de production

La [procédure](https://doc.scalingo.com/databases/postgresql/dump-restore) est décrite dans la documentation de Scalingo.

## Restaurer la base depuis backup Scalingo

Téléchargez un backup [ici](https://db-osc-fr1.scalingo.com/dashboard/5e3400ce987e0b6ac394c116/backups), puis :

```
$ tar xvzf 20200326230000_access4all_8677.tar.gz
$ pg_restore --clean --if-exists --no-owner --no-privileges --dbname $DATABASE_URL 20200326230000_access4all_8677.pgsql
```

### Réinitialisation complète de la base et réimport d'un dump de données

Il peut parfois arriver de rencontrer des erreurs si vous tentez de restaurer un dump dont le schéma diffère de vos encours de développement. Par exemple :

```
...
pg_restore: while PROCESSING TOC:
pg_restore: from TOC entry 5; 3079 32768 EXTENSION postgis (no owner)
pg_restore: error: could not execute query: ERROR:  cannot drop extension postgis because other objects depend on it
DETAIL:  column geom of table public.erp_commune depends on type public.geometry
...
pg_restore: warning: errors ignored on restore: 1
```

En pareil cas, une solution rapide et efficace est de supprimer complètement votre base de développement locale, de la recréer et d'y réimporter un dump de données comme montré précédemment :

```
$ sudo -u postgres dropdb access4all
$ sudo -u postgres createdb access4all
$ pg_restore --clean --if-exists --no-owner --no-privileges --dbname $DATABASE_URL docs/backups/20200505092251_access4all_8677.pgsql
```

Enfin, n'oubliez pas de rejouer d'éventuelles migrations non appliquées vis à vis de vos encours de développement :

```
$ python manage.py migrate
```

## Générer les graphes du modèle de données

Il est possible de générer les diagrammes de la structure du modèle de données métier Access4all en installant [GraphViz](https://www.graphviz.org/) sur votre machine et en exécutant la commande dédiée :

```
$ sudo apt install graphviz
$ ./makegraphs.sh
```

Les diagrammes au format PNG sont générés dans le répertoire `graphs` à la racine du dépôt.

## Astuces de développement

### Shell interactif

```
$ ./manage.py shell_plus
```

Pour activer le rechargement automatique :

```
%load_ext autoreload
%autoreload 2
```

### Astuce Postgres

Lancer psql en local:

```
$ sudo -u postgres psql
```
