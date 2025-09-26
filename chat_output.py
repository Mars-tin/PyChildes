"""Output structures (context managers) for processed CHAT data."""

import os
from contextlib import AbstractContextManager
from typing import Any

from chat_config import ChatConfig
from unit_turn import UnitTurn


class ChatSink(AbstractContextManager):
    """Abstract base class for outputting processed CHAT data.

    Attributes:
        __enter__: Called before iterating through the lines.
        __exit__: Called after finishing iterating through the lines.
        write_turn: Write a UnitTurn to the output.
    """

    def __init__(self, config: ChatConfig, *, output_file: str):
        """Initialize the sink with configuration and output file path.

        During initialization, validate the configuration to ensure
        unsupported features are not enabled.

        Args:
            config: ChatConfig object containing processing settings.
            output_file: Path where the processed content will be written.
        """
        ...

    def write_turn(self, turn: UnitTurn) -> None:
        """Write a UnitTurn to the output.

        Args:
            turn: UnitTurn object representing a single turn in the CHAT data.
        """
        ...


class ChatSinkText(ChatSink):
    """Output plain text files.

    Only supports header, utterance text and action dependent tiers (%act).
    """

    file_path: str
    buffer: list[str]

    def __init__(self, config: ChatConfig, *, output_file: str):
        """Initialize with the output file path and configuration.

        Args:
            config: ChatConfig object containing processing settings.
            output_file: Path where the processed content will be written.

        Raises:
            NotImplementedError: If the configuration includes unsupported features.
        """
        self.file_path = output_file
        self.buffer = []

        # Validate config

        if config.dependent.get('morphological', {}).get('keep_data', False):
            raise NotImplementedError(
                'Plain text output does not support writing morphological analysis.'
            )
        elif config.dependent.get('grammatical_relations', {}).get('keep_data', False):
            raise NotImplementedError(
                'Plain text output does not support writing grammatical relations.'
            )

    def __enter__(self):
        """Create output directory if it doesn't exist."""
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        return self

    def write_turn(self, turn: UnitTurn) -> None:
        """Write a UnitTurn to the file."""
        self.buffer.extend(turn.to_list())

    def __exit__(self, exc_type, exc_value, traceback):
        """Write the buffered content to the plain text file and close it."""
        if exc_type is not None:
            self.buffer.clear()
            return

        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                f.writelines(self.buffer)
        except Exception:
            raise
        else:
            self.buffer.clear()


class ChatSinkJSON(ChatSink):
    """Output JSON or Multiline JSON files, by default in Multiline JSONL format.

    Each line is a JSON object with "kind" and "content" fields.
    The schema for each kind is as follows:
    ```
    header: string[]
    utterance: string[]
    ```

    If JSON is chosen, the entire output is wrapped in a single JSON object with a "data" field containing an array of these objects.
    """

    file_path: str
    is_multiline: bool
    buffer: list[dict[str, Any]]

    def __init__(
        self, config: ChatConfig, *, output_file: str, is_multiline: bool = True
    ):
        """Initialize with the output file path, configuration, and format choice.

        Args:
            config: ChatConfig object containing processing settings.
            output_file: Path where the processed content will be written.
            is_multiline: If True, output in Multiline JSONL format; otherwise, output in standard JSON format.
        """
        self.file_path = output_file
        self.buffer = []
        self.is_multiline = is_multiline

    def __enter__(self):
        """Create output directory if it doesn't exist."""
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        return self

    def write_turn(self, turn: UnitTurn) -> None:
        """Write a UnitTurn to the buffer as a JSON object."""
        if turn.head:
            kind = 'header'
            content = {
                'content': list(map(str.strip, turn.head)),
            }
        elif turn.utt:
            kind = 'utterance'
            content = {
                'content': list(map(str.strip, turn.to_list())),
            }
        else:
            # Skip unknown/empty turns
            return

        self.buffer.append(
            {
                'kind': kind,
                **content,
            }
        )

    def __exit__(self, exc_type, exc_value, traceback):
        """Write the buffered content to the JSON or Multiline JSON file and close it."""
        if exc_type is not None:
            self.buffer.clear()
            return

        import json

        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                if self.is_multiline:
                    for entry in self.buffer:
                        f.write(json.dumps(entry, ensure_ascii=False) + '\n')
                else:
                    data = {'data': self.buffer}
                    f.write(json.dumps(data, ensure_ascii=False))
        except Exception:
            raise
        else:
            self.buffer.clear()
