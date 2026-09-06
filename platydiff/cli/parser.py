"""Argument parser construction."""

import argparse


def build_parser() -> argparse.ArgumentParser:
    """Build the top-level parser without publishing comparison behavior."""
    return argparse.ArgumentParser(
        prog="platydiff",
        description="Compare scientific and multimodal data.",
    )
