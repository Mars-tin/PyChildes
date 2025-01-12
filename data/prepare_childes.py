"""Functions for processing CHAT (.cha) files based on line prefixes.

This module provides functionality to process CHAT format files, specifically
filtering lines that begin with asterisk (*) which typically denote speaker turns.
"""

import re
from typing import Optional, Tuple

import yaml
from utils import DataIntegrityError


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


def process_special_form(utterance: str, config: ChatConfig) -> str:
    """Process special form markers in CHAT format transcripts.

    Args:
        utterance: Raw utterance text containing special form markers
        config: Configuration object with special form speech settings

    Returns:
        Utterance with special form markers replaced according to config settings
    """
    spec_form_cfg = config.utterance['specform']

    # Babbling (@b)
    marker = spec_form_cfg.get('babbling', '<unk>')
    utterance = re.sub(r'\S+@b\b', marker, utterance)

    # Child-invented forms (@c)
    marker = spec_form_cfg.get('child_invented', '<unk>')
    utterance = re.sub(r'\S+@c\b', marker, utterance)

    # Dialect form (@d)
    if spec_form_cfg.get('dialect', True):
        utterance = re.sub(r'(\S+)@d\b', r'\1', utterance)
    else:
        utterance = re.sub(r'\S+@d\b', '<unk>', utterance)

    # Filled pause (@fp)
    if spec_form_cfg.get('filled_pause', False):
        utterance = re.sub(r'\S+@fp\b', '<unk>', utterance)
    else:
        utterance = re.sub(r'\S+@fp\b', '', utterance)

    # Family-specific forms (@f)
    marker = spec_form_cfg.get('family_spec', '<unk>')
    utterance = re.sub(r'\S+@f\b', marker, utterance)

    # General special form (@g)
    if spec_form_cfg.get('general', False):
        utterance = re.sub(r'\S+@g\b', '<unk>', utterance)
    else:
        utterance = re.sub(r'\S+@g\b', '', utterance)

    # interjections (@i)
    if spec_form_cfg.get('interjections', True):
        utterance = re.sub(r'(\S+)@i\b', r'\1', utterance)
    else:
        utterance = re.sub(r'\S+@i\b', '<unk>', utterance)

    # multi_letters (@k)
    if spec_form_cfg.get('multi_letters', True):
        utterance = re.sub(r'(\S+)@k\b', lambda m: ' '.join(m.group(1)).upper(), utterance)
    else:
        utterance = re.sub(r'\S+@k\b', '<unk>', utterance)

    # letter (@l)
    if spec_form_cfg.get('letter', True):
        utterance = re.sub(r'(\S+)@l\b', lambda m: m.group(1).upper(), utterance)
    else:
        utterance = re.sub(r'\S+@l\b', '<unk>', utterance)

    # neologism (@n)
    if spec_form_cfg.get('neologism', False):
        utterance = re.sub(r'(\S+)@n\b', r'\1' + ' <neo>', utterance)
    else:
        utterance = re.sub(r'(\S+)@n\b', r'\1', utterance)

    # pcf (@p)
    if spec_form_cfg.get('pcf', False):
        utterance = re.sub(r'(\S+)@p\b', r'\1', utterance)
    else:
        utterance = re.sub(r'\S+@p\b', '<unk>', utterance)

    # metaling (@q)
    if spec_form_cfg.get('metaling', False):
        utterance = re.sub(r'(\S+)@q\b', r'"\1"', utterance)
    else:
        utterance = re.sub(r'(\S+)@q\b', r'\1', utterance)

    # second-language (@s)
    if spec_form_cfg.get('l2', True):
        utterance = re.sub(r'(\S+)@s[:$]\S+\b', r'\1', utterance)
    else:
        utterance = re.sub(r'\S+@s[:$]\S+\b', '<unk>', utterance)

    # Onomatopoeias (@o)
    if spec_form_cfg.get('onomatopoeia', True):
        utterance = re.sub(r'(\S+)@o\b', lambda m: m.group(1).replace('_', ' '), utterance)
    else:
        utterance = re.sub(r'\S+@o\b', '<unk>', utterance)

    return utterance


def process_unidentifiable(utterance: str, config: ChatConfig) -> str:
    """Process unidentifiable markers in CHAT format transcripts.

    Handles three types of unidentifiable content markers:
    1. xxx: Unintelligible speech
    2. yyy: Phonologically unclear speech
    3. www: Untranscribed speech

    Args:
        utterance: Raw utterance text containing unidentifiable markers
        config: Configuration object with unidentifiable speech settings

    Returns:
        Utterance with unidentifiable markers replaced according to config settings
    """
    unid_cfg = config.utterance['unidentifiable']

    marker = unid_cfg.get('unintelligible', '<unk>')
    utterance = re.sub(r'xxx', marker, utterance)

    marker = unid_cfg.get('phonological', '<unk>')
    utterance = re.sub(r'yyy', marker, utterance)

    marker = unid_cfg.get('untranscribed', '<unk>')
    utterance = re.sub(r'www', marker, utterance)

    return utterance


def process_incomplete(utterance: str, config: ChatConfig) -> str:
    """Process incomplete utterance markers in CHAT format transcripts.

    Handles two types of incomplete markers:
    1. Noncompletion markers: Text within parentheses ()
    2. Omitted word markers: &=0 followed by optional POS tag

    Args:
        utterance: Raw utterance text containing incomplete markers
        config: Configuration object with incomplete utterance settings

    Returns:
        Utterance with incomplete markers processed according to config settings
    """
    incomplete_cfg = config.utterance['incomplete']

    if incomplete_cfg.get('noncompletion', True):
        utterance = re.sub(r'\((.+?)\)', r'\1', utterance)
    else:
        utterance = re.sub(r'\(.*?\)\s*', '', utterance)

    # [TODO]: Create special handles for `&=0` + POS, e.g., `&=0det`.
    if incomplete_cfg.get('omitted', True):
        utterance = re.sub(r'&=0', '', utterance)
    else:
        utterance = re.sub(r'&=0\w+', '', utterance)

    return utterance


def process_paralinguistic(utterance: str, config: ChatConfig) -> str:
    """Process multiple paralinguistic markers in CHAT format utterances.

    Args:
        utterance: The utterance containing paralinguistic markers.
        config: Configuration object with paralinguistic utterance settings

    Returns:
        The processed utterance with standardized event/explanation markup.
    """
    scope_cfg = config.utterance['scoped']

    # Find all minimal regions with markers
    # Capture the identifier in group 4
    all_identifiers = ['=!', '=', '!', '!!']
    all_identifiers = sorted(all_identifiers, key=len, reverse=True)
    regions = re.finditer(
        fr'(?:<([^>]+)>|(\S+))\s*\[\s*({"|".join(all_identifiers)})\s*(\w+)?\]',
        utterance
    )

    # Process each match from end to start
    replacements = []
    for match in regions:
        phrase_in_brackets, word, identifier, event = match.groups()
        text = phrase_in_brackets if phrase_in_brackets else word
        start, end = match.span()

        if identifier == '=!':
            tag = scope_cfg.get('paralinguistic', 'evt')
            if tag != 'null':
                replacements.append((
                    start, end,
                    f'<{tag}>{event}<sep>{text}</{tag}>'
                ))
            else:
                replacements.append((
                    start, end, f'{text}'
                ))

        elif identifier == '=':
            tag = scope_cfg.get('explanation', 'null')
            if tag != 'null':
                replacements.append((
                    start, end,
                    f'<{tag}>{event}<sep>{text}</{tag}>'
                ))
            else:
                replacements.append((
                    start, end, f'{text}'
                ))

        elif identifier == '!':
            assert event is None
            tag = scope_cfg.get('stressing', 'stress')
            if tag != 'null':
                replacements.append((
                    start, end,
                    f'<{tag}>{text}</{tag}>'
                ))
            else:
                replacements.append((
                    start, end, f'{text}'
                ))

        else:
            replacements.append((
                start, end, f'{text}'
            ))

    # Apply replacements from end to start
    for start, end, replacement in sorted(replacements, reverse=True):
        utterance = utterance[:start] + replacement + utterance[end:]

    return utterance


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

    # Process special forms
    utterance = process_special_form(utterance, config)

    # Process incomplete words
    utterance = process_incomplete(utterance, config)

    # Process unidentifiable markers
    utterance = process_unidentifiable(utterance, config)

    # Process paralinguistic scope markers
    utterance = process_paralinguistic(utterance, config)

    # utterance = re.sub(r'\[.*?\]\s*', '', utterance)
    # utterance = re.sub(r'\<(.+?)\>', r'\1', utterance)

    # Process nonverbal token
    marker = config.utterance.get('nonverbal', '<0>')
    utterance = re.sub(r'0', marker, utterance)

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

        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(processed_lines)

        print(f'Successfully processed {input_file}')
        print(f'processed content written to {output_file}')

    except FileNotFoundError as e:
        print(f'Error: File error occurred: {str(e)}')

    except IOError as e:
        print(f'Error: IO error occurred: {str(e)}')

    except DataIntegrityError as e:
        print(f'Error: {str(e)}')


if __name__ == '__main__':

    # Example usage
    input_file = 'raw/childes/Eng-NA/Bates/Free20/amy.cha'
    output_file = 'prep/childes/output.cha'
    config_path = 'configs/example.yaml'
    process_cha_file(input_file, output_file, config_path)
