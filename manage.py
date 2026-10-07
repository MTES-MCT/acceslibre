#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""

import importlib
import os
import sys


def _dotenv_settings_module():
    """Return the settings module named in the local .env, but only if its DEBUG is True.

    The value is used only when DJANGO_SETTINGS_MODULE is not already set (CI, the
    container ENV and --settings keep priority) and only when importing it yields
    DEBUG=True, so a stray .env can never select a production settings module.
    """
    if "DJANGO_SETTINGS_MODULE" in os.environ:
        return None

    env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    name = None
    try:
        with open(env_file, encoding="utf-8") as env:
            for line in env:
                line = line.strip()
                if line.startswith("export "):
                    line = line[7:].lstrip()
                if line.startswith("DJANGO_SETTINGS_MODULE="):
                    name = line.partition("=")[2].strip().strip("\"'")
                    break
    except OSError:
        return None
    if not name:
        return None

    try:
        module = importlib.import_module(name)
    except Exception:
        name = None
    else:
        if getattr(module, "DEBUG", False) is not True:
            name = None

    # core/__init__ imports the celery worker, which forces its own default while
    # DJANGO_SETTINGS_MODULE is still unset: drop whatever the import introduced.
    os.environ.pop("DJANGO_SETTINGS_MODULE", None)
    return name


def main():
    settings_module = _dotenv_settings_module()
    if settings_module:
        os.environ["DJANGO_SETTINGS_MODULE"] = settings_module
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings_prod")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
