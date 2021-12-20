import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from enthic.scraping.cquest import fetch_bundle_xmls, list_bundles


@patch("enthic.scraping.cquest.wget.download")
def test_fetch_bundle_xmls(mock_download):
    bundle_fn = Path(__file__).parent / "fixtures" / "bundles.7z"

    with tempfile.TemporaryDirectory() as savedir:

        savedir = Path(savedir)
        mock_download.side_effect = lambda _, outdir: shutil.copyfile(
            bundle_fn, Path(outdir) / "bilans_saisis_20210101.7z"
        )

        fetch_bundle_xmls("bilans_saisis_20210101.7z", savedir)
        comptes = (
            savedir
            / "bilans_saisis_20210101"
            / "comptes"
            / "PUB_CA_483935326_1303_2013D00195_2015_1048.donnees.xml"
        )
        assert comptes.exists()


@pytest.mark.skip(reason="No need to stress the platform")
def test_list_bundles():
    bundles = list_bundles()
    assert len(bundles) > 1660
