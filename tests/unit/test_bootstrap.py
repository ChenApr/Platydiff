"""Bootstrap contract tests."""

import platydiff
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


def test_package_root_does_not_export_prohibited_internals() -> None:
    prohibited = {
        "InternalRegistry",
        "MyersResult",
        "PipelineStage",
        "StageRunner",
        "compare_text",
        "render_json",
        "render_terminal",
    }
    assert prohibited.isdisjoint(platydiff.__all__)
    assert all(not hasattr(platydiff, name) for name in prohibited)


def test_package_root_exports_corrected_schema_v3_contracts() -> None:
    expected = {
        "ArrayChange",
        "ArrayCompareSpec",
        "ArrayResourceLimits",
        "ColumnOrderFact",
        "ColumnSchemaFact",
        "ColumnSpec",
        "NumericPolicy",
        "TableChange",
        "TableCompareSpec",
        "TableResourceLimits",
        "TableRowFact",
        "YamlCompareSpec",
        "YamlResourceLimits",
    }
    assert expected <= set(platydiff.__all__)
    assert all(hasattr(platydiff, name) for name in expected)
