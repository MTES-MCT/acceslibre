.PHONY: messages
messages:
	uv run python manage.py makemessages --ignore=node_modules --ignore=venv --ignore=.venv --ignore=docs --all --no-location --settings=core.settings_dev
	uv run python manage.py makemessages -d djangojs --all --pythonpath=../acceslibre --ignore=venv --ignore=node_modules --ignore=static/dist --ignore=docs --no-location --settings=core.settings_dev

.PHONY: compilemessages
compilemessages:
	uv run python manage.py compilemessages --settings=core.settings_dev --ignore=venv --ignore=node_modules --ignore=static/dist --ignore=docs --ignore=.venv

.PHONY: translate
translate:
	uv run python manage.py translate_messages --untranslated --source-language="french" --locale "en" --settings=core.settings_dev


.PHONY: runserver
runserver:
	uv run manage.py runserver  --settings=core.settings_dev
