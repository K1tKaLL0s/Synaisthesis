import re

from synaisthesis import __version__
from synaisthesis.version import get_version

SEMVER_PATTERN = re.compile(r"^\d+\.\d+\.\d+(?:[a-z0-9.\-+]*)$")


def test_get_version_returns_semver_string():
    assert isinstance(get_version(), str)
    assert SEMVER_PATTERN.match(get_version())


def test_get_version_matches_package_version():
    assert get_version() == __version__
