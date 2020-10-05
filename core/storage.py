from django.contrib.staticfiles.storage import ManifestStaticFilesStorage


class AppStaticFilesStorage(ManifestStaticFilesStorage):
    manifest_strict = True
