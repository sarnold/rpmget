from pathlib import Path

import pytest

from rpmget import version


def test_nothing(capfd):
    print('yup, that just happened')
    out, err = capfd.readouterr()
    assert 'yup' in out
