.PHONY: messages
messages:
	uv run python manage.py makemessages --ignore=node_modules --ignore=venv --ignore=docs --all --no-location
	uv run python manage.py makemessages -d djangojs --all --pythonpath=../acceslibre --ignore=venv --ignore=node_modules --ignore=static/dist --ignore=docs --no-location

.PHONY: translate
translate:
	uv run python manage.py translate_messages --untranslated --source-language="french" --locale "en"


.PHONY: runserver
runserver:
	uv run manage.py runserver  --settings=core.settings_dev
