"""
Output structures (context managers) for processed CHAT data.
"""

from contextlib import AbstractContextManager
import os
from chat_config import ChatConfig
from unit_turn import UnitTurn


class ChatSink(AbstractContextManager):
    """
    Abstract base class for outputting processed CHAT data.

    Attributes:
        __enter__: Called before iterating through the lines.
        __exit__: Called after finishing iterating through the lines.
        write_turn: Write a UnitTurn to the output.
    """

    def __init__(self, config: ChatConfig, *, output_file: str):
        """
        Initialize the sink with configuration and output file path.

        During initialization, validate the configuration to ensure
        unsupported features are not enabled.

        Args:
            config: ChatConfig object containing processing settings.
            output_file: Path where the processed content will be written.
        """
        ...

    def write_turn(self, turn: UnitTurn) -> None:
        ...


class ChatSinkText(ChatSink):
    """Output plain text files.
    
    Only supports header, utterance text and action dependent tiers (%act). 
    """

    file_path: str
    buffer: list[str]

    def __init__(self, config: ChatConfig, *, output_file: str):
        """Initialize with the output file path.

        Args:
            output_file: Path where the processed content will be written.
        """
        self.file_path = output_file
        self.buffer = []

        # Validate config

        if config.dependent.get("morphological", {}).get("keep_data", False):
            raise NotImplementedError("Plain text output does not support writing morphological analysis.")
        elif config.dependent.get("grammatical_relations", {}).get("keep_data", False):
            raise NotImplementedError("Plain text output does not support writing grammatical relations.")

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
