from pathlib import Path

import pytest
from munch import Munch

from simple import version


def test_nothing(capfd):
    print('yup, that just happened')
    out, err = capfd.readouterr()
    assert 'yup' in out
