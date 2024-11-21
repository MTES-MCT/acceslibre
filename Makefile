.PHONY: messages
messages:
	python manage.py makemessages --ignore=node_modules --ignore=venv --all --no-location
	python manage.py makemessages -d djangojs --all --pythonpath=../acceslibre --ignore=node_modules --ignore=static/dist --no-location

.PHONY: translate
translate:
	python manage.py translate_messages --untranslated --source-language="french" --locale "en"
