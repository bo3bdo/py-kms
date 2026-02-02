"""Test single version source."""
import pykms_version as m


def test_version_defined():
    """__version__ is a non-empty string."""
    assert hasattr(m, "__version__")
    assert isinstance(m.__version__, str)
    assert len(m.__version__) > 0


def test_version_format():
    """Version looks like YYYY.MM.DD."""
    parts = m.__version__.split(".")
    assert len(parts) >= 2
    assert parts[0].isdigit() and parts[1].isdigit()
