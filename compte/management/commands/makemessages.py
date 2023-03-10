from django.core.management.commands import makemessages


class Command(makemessages.Command):
    """
    Be able to use other alias to import gettext*
    Source: https://stackoverflow.com/questions/16509160/ugettext-and-ugettext-lazy-functions-not-recognized-by-makemessages-in-python-dj
    """

    xgettext_options = makemessages.Command.xgettext_options + [
        "--keyword=trans",
        "--keyword=translate",
        "--keyword=trans_lazy",
        "--keyword=translate_lazy",
    ]
