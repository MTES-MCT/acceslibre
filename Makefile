.PHONY: messages
messages:
	python manage.py makemessages --ignore=node_modules --ignore=venv --ignore=docs --all --no-location
	python manage.py makemessages -d djangojs --all --pythonpath=../acceslibre --ignore=venv --ignore=node_modules --ignore=static/dist --ignore=docs --no-location 

.PHONY: translate
translate:
	python manage.py translate_messages --untranslated --source-language="french" --locale "en"
