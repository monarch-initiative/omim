from omim2obo.config import ROOT, DATA_DIR
from omim2obo.utils import check_version


def test_check_version():

    temp_file = ROOT / 'tests/tmp.txt'
    temp_file.touch()
    version = check_version(temp_file)
    print(version.st_ctime)
