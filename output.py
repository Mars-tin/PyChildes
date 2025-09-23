from collections.abc import Container
from contextlib import AbstractContextManager
import os
from typing import Literal

from unit_turn import UnitTurn

OutputFields = Literal["utterance"]


class ChildesSink(AbstractContextManager):
    def __init__(self, output_fields: Container[OutputFields] | None = None, **kwargs):
        ...

    def write_turn(self, turn: UnitTurn) -> None:
        ...


class ChildesSinkText(ChildesSink):
    """Text file implementation of ChildesSink that writes turns to a text file."""

    file_path: str
    buffer: list[str]

    def __init__(self, output_fields: set[OutputFields] | None = None, *, output_file: str):
        """Initialize with the output file path.

        Args:
            output_file: Path where the processed content will be written.
        """
        self.file_path = output_file
        self.buffer = []

    def __enter__(self):
        """Open the file for writing and return self."""

        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        return self

    def write_turn(self, turn: UnitTurn) -> None:
        """Write a UnitTurn to the file."""
        self.buffer.extend(turn.to_list())

    def __exit__(self, exc_type, exc_value, traceback):
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                f.writelines(self.buffer)
        except Exception:
            raise
        else:
            self.buffer.clear()