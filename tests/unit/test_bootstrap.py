"""Bootstrap contract tests."""

from platydiff import __version__
from platydiff.cli.main import main


def test_version() -> None:
    assert __version__ == "0.1.0.dev0"


def test_help_loads() -> None:
    try:
        main(["--help"])
    except SystemExit as error:
        assert error.code == 0
    else:
        raise AssertionError("argparse help must exit successfully")
