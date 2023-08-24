.PHONY: messages
messages:
	python manage.py makemessages --ignore=node_modules --all --no-location --no-wrap
	django-admin makemessages -d djangojs --all --pythonpath=../acceslibre --ignore=node_modules --no-location
