"""Command-line entry point."""

from platydiff.cli.parser import build_parser


def main(argv: list[str] | None = None) -> int:
    """Parse command-line arguments for the package bootstrap."""
    parser = build_parser()
    parser.parse_args(argv)
    return 0
