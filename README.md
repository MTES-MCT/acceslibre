# Access4all

Référencement de l'accessibilité des ERP (Établissements Recevant du Public) en France.

## Prérequis

- Environnement Linux (ex. Debian/Ubuntu recommandé)
- Python 3.7+
- Les paquets `libpq-dev` et `python3.7-dev` doivent également être installés sur le système
- [Pipenv](https://pipenv.kennethreitz.org/en/latest/)

## Configurer les variables d'environnement

Créez un fichier `.env` à la racine du dépôt, définissant les variables d'environnement suivantes :

- `SECRET_KEY`: une chaine de caractères unique permettant de gérer les [opérations de chiffrement](https://docs.djangoproject.com/en/3.0/ref/settings/#secret-key).
- `DB_HOST`: l'uri de connexion postgres
- `DB_PORT`: le port de connexion à la base postgres
- `DB_NAME`: le nom de la base postgres
- `DB_USER`: le nom d'utilisateur postgres
- `DB_PASSWORD`: le most de passe de l'utilisateur postgres

Note: un fichier d'exemple `.env.sample` est disponible à la racine du dépôt.

## Installation

```
$ pipenv shell
$ pipenv install
```

## Configurer la base de données

:warning: Assurez-vous de disposer des paquets `libpq-dev` et `python3.7-dev`:

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

Dans `access4all/settings.py`, spécifiez la connexion :

```
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'access4all',
        'USER': 'access4all',
        'PASSWORD': 'access4all',
        'HOST': 'localhost',
        'PORT': '',
    }
}
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
