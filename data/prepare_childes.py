"""Functions for processing CHAT (.cha) files based on line prefixes.

This module provides functionality to process CHAT format files, specifically
filtering lines that begin with asterisk (*) which typically denote speaker turns.
"""

import os
import re
from typing import Any, Optional, Tuple

import yaml


class DataIntegrityError(Exception):
    """Exception raised for errors in the data integrity.

    Args:
        message: Explanation of the error.
        data: The data that caused the integrity violation.

    Attributes:
        message: A string explaining the error.
        data: The data that caused the integrity violation.
    """

    def __init__(
        self,
        message: str = 'Data integrity violation encountered.',
        data: Optional[Any] = None,
    ) -> None:
        """Initialize the DataIntegrityError.

        Args:
            message: Explanation of the error. Defaults to generic message.
            data: The data that caused the error. Defaults to None.
        """
        self.message = message
        self.data = data
        super().__init__(self.message)

    def __str__(self) -> str:
        """Create string representation of the error.

        Returns:
            String containing error message and optionally the problematic data.
        """
        if self.data:
            return f'{self.message} Data: {self.data}'
        return self.message


class ChatConfig:
    """Load and provide access to CHAT data processing configuration.

    This class loads configuration from a YAML file specifying how different
    CHAT data elements should be processed and transformed.

    Attributes:
        header: Configuration for header section processing.
        utterance: Configuration for utterance processing including
            special markers and transformations.
        dependent_tier: Configuration for dependent tier processing.
    """

    def __init__(self, config_path: Optional[str] = None) -> None:
        """Initialize ChatConfig with configuration from YAML file.

        Args:
            config_path: Path to the YAML configuration file. If None,
                defaults to 'chat.yaml' in the current directory.

        Raises:
            FileNotFoundError: If the configuration file is not found.
            yaml.YAMLError: If the YAML file is malformed.
        """
        if config_path is None:
            config_path = 'configs/chat.yaml'

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            self.header = config.get('header', {})
            self.utterance = config.get('utterance', {})
            self.dependent = config.get('dependent', {})

        except FileNotFoundError:
            raise FileNotFoundError(f'Configuration file not found: {config_path}')

        except yaml.YAMLError as e:
            raise yaml.YAMLError(f'Error parsing YAML configuration: {str(e)}')


def process_header(input_line: str, config: ChatConfig) -> Tuple[bool, str]:
    """Process a header line from the input.

    Args:
        input_line: The line to be processed as a header.

    Returns:
        A tuple containing:
            - bool: True if the line will be added to the processed file.
            - str: The processed line.
    """
    return config.header.get('keep_data', False), input_line


def process_utterance(input_line: str, config: ChatConfig) -> Tuple[bool, str]:
    """Process an utterance from the input using provided configuration.

    Args:
        input_line: The line to be processed as an utterance.
        config: Configuration object containing processing rules.

    Returns:
        A tuple containing:
            - bool: True if the line will be added to the processed file.
            - str: The processed line.

    Raises:
        ValueError: If input line is not in expected format (speaker:tab:utterance).
    """
    try:
        speaker_id, utterance = input_line.split(':\t')

    except ValueError:
        raise DataIntegrityError(
            f'Invalid utterance format: {input_line}',
            input_line
        )

    # Get configuration
    if not config.utterance.get('keep_data', True):
        return False, ''

    # Process the speaker token
    speaker = ''
    if config.utterance.get('keep_speaker', True):
        speaker = '<' + speaker_id[1:] + '>'

    # Process incomplete words
    incomplete = config.utterance['incomplete']

    if incomplete.get('noncompletion', True):
        utterance = re.sub(r'\((.+?)\)', r'\1', utterance)
    else:
        utterance = re.sub(r'\(.*?\)\s*', '', utterance)

    if incomplete.get('omitted', True):
        utterance = re.sub(r'&=0', '', utterance)
    else:
        utterance = re.sub(r'&=0\w+', '', utterance)

    # Process nonverbal token
    marker = config.utterance.get('nonverbal', '<0>')
    utterance = re.sub(r'0', marker, utterance)

    # Process unidentifiable markers
    unidentifiable = config.utterance['unidentifiable']

    marker = unidentifiable.get('unintelligible', '<unk>')
    utterance = re.sub(r'xxx', marker, utterance)

    marker = unidentifiable.get('phonological', '<unk>')
    utterance = re.sub(r'yyy', marker, utterance)

    # Process scoped markers
    scoped_markers = config.utterance['scoped']
    for key, marker in scoped_markers.items():
        if key == 'stressed':
            utterance = re.sub(r'\[!\]\s+(\S+)', r'<stress> \\1 </stress>', utterance)

    utterance = re.sub(r'\[.*?\]\s*', '', utterance)

    return True, speaker + ' ' + utterance


def process_dependent_tier(input_line: str, config: ChatConfig) -> Tuple[bool, str]:
    """Process a dependent tier from the input.

    Args:
        input_line: The line to be processed as a dependent tier.

    Returns:
        A tuple containing:
            - bool: True if the line will be added to the processed file.
            - str: The processed line.
    """
    try:
        tier, content = input_line.split(':\t')

    except ValueError:
        raise DataIntegrityError(
            f'Invalid dependent tier format: {input_line}',
            input_line
        )

    # Get configuration
    if not config.dependent.get('keep_data', True):
        return False, ''

    # TODO: complete parsing dependent tiers

    return True, content


def process_cha_file(input_file: str, output_file: str, config_path: str) -> None:
    """Read a .cha file and write cleaned conversations to output file.

    Args:
        input_file: Path to the input .cha file to be processed.
        output_file: Path where the processed content will be written.
        config_path: Path to the configuration .yaml file to be followed.

    Raises:
        FileNotFoundError: If the input file does not exist.
        IOError: If there are issues reading the input or writing to output.
        DataIntegrityError: If the input file contains data integrity violations.
    """
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

    except FileNotFoundError:
        print(f'Input file not found: {input_file}')

    try:
        config = ChatConfig(config_path)

        processed_lines = []

        for line in lines:

            keep_data = True

            if line.startswith('@'):
                keep_data, line = process_header(line, config)

            elif line.startswith('*'):
                keep_data, line = process_utterance(line, config)

            elif line.startswith('%'):
                keep_data, line = process_dependent_tier(line, config)

            else:
                raise DataIntegrityError(data=line)

            if keep_data:
                processed_lines.append(line)

        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(processed_lines)

        print(f'Successfully processed {input_file}')
        print(f'processed content written to {output_file}')

    except IOError as e:
        print(f'Error: IO error occurred: {str(e)}')
        raise e

    except DataIntegrityError as e:
        print(f'Error: {str(e)}')
        raise e


if __name__ == '__main__':

    # Example usage
    input_file = 'raw/childes/Eng-NA/Bates/Free20/amy.cha'
    output_file = 'prep/childes/output.cha'
    config_path = 'configs/chat.yaml'
    process_cha_file(input_file, output_file, config_path)
