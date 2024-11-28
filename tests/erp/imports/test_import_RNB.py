from unittest import mock

import pytest
from django.core.management import call_command

from erp.models import ExternalSource
from tests.factories import ErpFactory, ExternalSourceFactory

csv_file_contents = """ext_id,rnb_ids,match_reason
e6db2f76-d4d3-4732-b409-a3ad014482c9,"['XVZC5ZVWA778']","precise_address_match"
c5afca82-aff0-4680-a270-914a2ea4c727,"['PB1TGMTZPFDZ']","precise_address_match"
c7d781c0-12cf-4d66-aeef-571d8d4efd4f,"['MTGXZS6TJM6G', '4SW8FJEER86W']","precise_address_match"
"""


@pytest.mark.django_db
def test_erp_not_found():
    with mock.patch("builtins.open", mock.mock_open(read_data=csv_file_contents)):
        call_command("import_RNB", file="mocked_file", write=False)

    assert ExternalSource.objects.count() == 0


@pytest.mark.django_db
def test_add_new_external_source():
    erp = ErpFactory.create(uuid="e6db2f76-d4d3-4732-b409-a3ad014482c9")

    with mock.patch("builtins.open", mock.mock_open(read_data=csv_file_contents)):
        call_command("import_RNB", file="mocked_file", write=True)

    assert ExternalSource.objects.count() == 1
    source = erp.sources.first()
    assert source.erp == erp
    assert source.source_id == "XVZC5ZVWA778"


@pytest.mark.django_db
def test_dry_run_mode():
    ErpFactory.create(uuid="e6db2f76-d4d3-4732-b409-a3ad014482c9")

    with mock.patch("builtins.open", mock.mock_open(read_data=csv_file_contents)):
        call_command("import_RNB", file="mocked_file", write=False)

    assert ExternalSource.objects.count() == 0


@pytest.mark.django_db
def test_update_sources():
    erp = ErpFactory.create(uuid="c7d781c0-12cf-4d66-aeef-571d8d4efd4f")
    ExternalSourceFactory(erp=erp, source_id="OLD_SOURCE_ID", source=ExternalSource.SOURCE_RNB)

    with mock.patch("builtins.open", mock.mock_open(read_data=csv_file_contents)):
        call_command("import_RNB", file="mocked_file", write=True)

    assert ExternalSource.objects.count() == 1
    assert erp.sources.first().source_id == "MTGXZS6TJM6G"


@pytest.mark.django_db
def test_ignore_existing_sources():
    erp = ErpFactory.create(uuid="e6db2f76-d4d3-4732-b409-a3ad014482c9")
    ExternalSourceFactory(erp=erp, source_id="XVZC5ZVWA778", source=ExternalSource.SOURCE_RNB)

    with mock.patch("builtins.open", mock.mock_open(read_data=csv_file_contents)):
        call_command("import_RNB", file="mocked_file", write=True)

    assert ExternalSource.objects.count() == 1
    assert erp.sources.first().source_id == "XVZC5ZVWA778"
