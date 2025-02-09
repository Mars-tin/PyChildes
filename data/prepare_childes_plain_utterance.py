"""Functions for processing CHAT (.cha) files based on line prefixes.

This module provides functionality to process CHAT format files, specifically
filtering lines that begin with asterisk (*) which typically denote speaker turns.

This processing pipeline only keeps the utterances.
"""

import os
import re
from typing import List, Optional, Tuple

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
            config_path = './configs/example.yaml'

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


def process_basic(utterance: str, config: ChatConfig) -> str:
    """Processes basic phonetic and prosodic markers in CHAT-format transcripts.

    This function modifies the given utterance based on the configuration settings in `config.utterance['basic']`,
    selectively removing or replacing various phonetic and prosodic markers.

    Args:
        utterance (str): The input utterance containing CHAT-format phonetic markers.
        config (ChatConfig): Configuration object specifying which markers to process.

    Returns:
        str: The processed utterance with specified markers removed or replaced.
    """
    unid_basic = config.utterance['basic']

    # Remove file errors, i.e., U+0015 (Negative Acknowledge)
    utterance = re.sub(r'\s\u0015.*?\u0015', '', utterance)

    # [TODO] Audio and Video Time Marks (10.1)
    # For now just remove
    utterance = re.sub(r'\s\·.*?\·', '', utterance)

    # Satellite (9.3)
    if not unid_basic.get('satellite', False):
        utterance = re.sub(r'\‡', ',', utterance)
        utterance = re.sub(r'\„', ',', utterance)

    # Tone Direction (9.8)
    if not unid_basic.get('tone', False):
        utterance = re.sub(r'\↑', '', utterance)
        utterance = re.sub(r'\↓', '', utterance)

    # Lengthening (9.7 / 9.9)
    if not unid_basic.get('lengthening', False):
        utterance = re.sub(r'\:', '', utterance)

    # Primary Stress (9.9)
    if not unid_basic.get('prim_stress', False):
        utterance = re.sub(r'\ˈ', '', utterance)

    # Secondary Stress (9.9)
    if not unid_basic.get('prim_stress', False):
        utterance = re.sub(r'\ˌ', '', utterance)

    # Blocking (9.9)
    if not unid_basic.get('blocking', False):
        utterance = re.sub(r'\≠', '', utterance)

    # Pauses (9.9 / 9.10.4)
    if not unid_basic.get('pause', False):

        # Pauses can take the following forms:
        # 1. (...) - Arbitrary number of dots inside parentheses.
        # 2. (xx.xx) - A decimal number inside parentheses.
        # 3. (xx:xx) - A minute:second format inside parentheses.
        # 4. (xx:xx.xx) - A minute:second.fraction format inside parentheses.
        pause_pattern = r'\(\.{1,}\)\s?|\(\d+\.\d*\)\s?|\(\d+:\d+\.\d*\)\s?|\(\d+:\d+\)\s?'
        utterance = re.sub(pause_pattern + r'\)', '', utterance)

        # 5. (ww^ww) - Pause between syllables
        utterance = re.sub(r'\^', '', utterance)

    return utterance


def process_linker(utterance: str, config: ChatConfig) -> str:
    """Processes special utterance terminators and linkers in the given text.

    This function replaces specific transcription markers that denote special
    linguistic events, such as trailing off, interruptions, self-interruptions,
    and transcription breaks. It modifies the input `utterance` based on the
    settings in `config.utterance['linkers']`.

    Args:
        utterance (str): The input text containing special transcription markers.
        config (ChatConfig): Configuration object that specifies which markers
                             should be processed.

    Returns:
        str: The processed utterance with special markers replaced based on settings.
    """
    unid_linkers = config.utterance['linkers']

    # Trailing Off (9.11)
    if not unid_linkers.get('trail_off', False):
        utterance = re.sub(r'\+\.\.\.', '...', utterance)

    # Trailing Off of a Question (9.11)
    if not unid_linkers.get('trail_off_q', False):
        utterance = re.sub(r'\+\.\.\?', r'...?', utterance)

    # Question With Exclamation (9.11)
    if not unid_linkers.get('exclamation', False):
        utterance = re.sub(r'\+\!\?', '!?', utterance)

    # Interruption (9.11)
    if not unid_linkers.get('interruption', False):
        utterance = re.sub(r'\+\/\.', '...', utterance)

    # Self Completion (9.12)
    if not unid_linkers.get('completion', False):
        utterance = re.sub(r'\+\,\s', '', utterance)

    # Interruption of a Question (9.11)
    if not unid_linkers.get('interruption_q', False):
        utterance = re.sub(r'\+\/\?', '...?', utterance)

    # Self-Interruption (9.11)
    if not unid_linkers.get('interruption_self', False):
        utterance = re.sub(r'\+\/\/\.', '...', utterance)

    # Self-Interrupted Question (9.11)
    if not unid_linkers.get('interruption_self_q', False):
        utterance = re.sub(r'\+\/\/\?', '...?', utterance)

    # Transcription Break (9.11)
    if not unid_linkers.get('trans_break', False):
        utterance = re.sub(r'\+\.', '.', utterance)

    # [TODO] Quotation (9.11, 9.12)
    # Currently just remove all quotation marks.
    # In the future can add a pair of quotation marks to the sequence.
    if not unid_linkers.get('quote_precede', False):
        utterance = re.sub(r'\+\"\.', '.', utterance)
    if not unid_linkers.get('quote_follow', False):
        utterance = re.sub(r'\+\"\/\.', ':', utterance)
    if not unid_linkers.get('quote_utterance', False):
        utterance = re.sub(r'\+\"\s', '', utterance)

    # Quick Uptake (9.12)
    if not unid_linkers.get('uptake', False):
        utterance = re.sub(r'\+\^\s', '', utterance)

    # Other Completion, i.e., Latching (9.12)
    if not unid_linkers.get('latching', False):
        utterance = re.sub(r'\+\+\s', '', utterance)

    return utterance


def process_local_event(utterance: str, config: ChatConfig) -> str:
    """Processes local events in the given utterance and replaces them with formatted tags.

    This function identifies and processes two types of events in the input `utterance`:
    It applies replacements in reverse order to maintain correct character positions.

    Args:
        utterance (str): The input text containing event markers.
        config (ChatConfig): Configuration object containing utterance-related settings.

    Returns:
        str: The processed utterance with events replaced by formatted tags or tokens.
    """
    env_tag = config.utterance['scoped'].get('paralinguistic', 'ENV')
    nonverbal_token = config.utterance.get('nonverbal', '<0>')
    replacements = []

    # Simple Events &= (9.10.l)
    pattern = r'&=(\w+)(?::(\w+))?'

    # Find all matches in the utterance
    regions = re.finditer(pattern, utterance)

    # Process each match and construct replacements
    for match in regions:

        start, end = match.span()
        verb = match.group(1)
        noun = match.group(2) if match.group(2) else None
        event = f'{verb} {noun}' if noun else verb

        if env_tag != 'null':
            replacements.append((
                start, end,
                f'<{env_tag}> {event} <sep> {nonverbal_token} </{env_tag}>'
            ))
        else:
            replacements.append((
                start, end,
                f'{nonverbal_token}'
            ))

    # Complex Local Events (9.10.3)
    pattern = r'&\{(l|n)=(\w+)(?::(\w+))?\s*(.*?)\s*&}\1=\2(?::\3)?'

    # Find all matches in the utterance
    regions = re.finditer(pattern, utterance)

    # Process each match and construct replacements
    for match in regions:

        start, end = match.span()
        verb = match.group(2)
        noun = match.group(3) if match.group(3) else None
        details = match.group(4).strip()
        event = f'{verb} {noun} {details}'.strip() if noun else f'{verb} {details}'.strip()

        if env_tag != 'null':
            replacements.append((
                start, end,
                f'<{env_tag}> {event} <sep> {nonverbal_token} </{env_tag}>'
            ))
        else:
            replacements.append((
                start, end,
                f'{nonverbal_token}'
            ))

    # Apply replacements from end to start
    for start, end, replacement in sorted(replacements, reverse=True):
        utterance = utterance[:start] + replacement + utterance[end:]

    return utterance


def process_special_form(utterance: str, config: ChatConfig) -> str:
    """Process special form markers in CHAT format transcripts.

    Args:
        utterance: Raw utterance text containing special form markers
        config: Configuration object with special form speech settings

    Returns:
        Utterance with special form markers replaced according to config settings
    """
    spec_form_cfg = config.utterance['specform']
    env_tag = config.utterance['scoped'].get('paralinguistic', 'ENV')
    pho_tag = config.utterance['unidentifiable'].get('phonological', '<pho>')

    # singing (@si)
    if spec_form_cfg.get('singing', True):
        utterance = re.sub(
            r'([^<>\s]+)@si\b',
            f'<{env_tag}> sings <sep> ' + r'\1' + f' </{env_tag}>',
            utterance
        )
    else:
        utterance = re.sub(r'([^<>\s]+)@si\b', r'\1', utterance)

    # sign language (@sl)
    if spec_form_cfg.get('sign', True):
        utterance = re.sub(
            r'([^<>\s]+)@sl\b',
            f'<{env_tag}> sign language<sep> ' + r'\1' + f' </{env_tag}>',
            utterance
        )
    else:
        utterance = re.sub(r'([^<>\s]+)@sl\b', r'\1', utterance)

    # sign and speech (@sas)
    if spec_form_cfg.get('sas', True):
        utterance = re.sub(
            r'([^<>\s]+)@sl\b',
            f'<{env_tag}> sign language <sep> ' + r'\1' + f' </{env_tag}>',
            utterance
        )
    else:
        utterance = re.sub(r'([^<>\s]+)@sl\b', r'\1', utterance)

    # Babbling (@b)
    marker = spec_form_cfg.get('babbling', '<unk>')
    utterance = re.sub(r'[^<>\s]+@b\b', marker, utterance)

    # Child-invented forms (@c)
    marker = spec_form_cfg.get('child_invented', '<unk>')
    utterance = re.sub(r'[^<>\s]+@c\b', marker, utterance)

    # Dialect form (@d)
    if spec_form_cfg.get('dialect', True):
        utterance = re.sub(r'([^<>\s]+)@d\b', r'\1', utterance)
    else:
        utterance = re.sub(r'[^<>\s]+@d\b', '<unk>', utterance)

    # Filled pause (@fp)
    if spec_form_cfg.get('filled_pause', False):
        utterance = re.sub(r'[^<>\s]+@fp\b', '<unk>', utterance)
    else:
        utterance = re.sub(r'\s*[^<>\s]+@fp\b\s*', ' ', utterance)

    # Family-specific forms (@f)
    marker = spec_form_cfg.get('family_spec', '<unk>')
    utterance = re.sub(r'[^<>\s]+@f\b', marker, utterance)

    # General special form (@g)
    if spec_form_cfg.get('general', False):
        utterance = re.sub(r'[^<>\s]+@g\b', '<unk>', utterance)
    else:
        utterance = re.sub(r'\s*[^<>\s]+@g\b\s*', ' ', utterance)

    # Interjections (@i)
    if spec_form_cfg.get('interjections', True):
        utterance = re.sub(r'([^<>\s]+)@i\b', r'\1', utterance)
    else:
        utterance = re.sub(r'[^<>\s]+@i\b', '<unk>', utterance)

    # Multi_letters (@k)
    if spec_form_cfg.get('multi_letters', True):
        utterance = re.sub(r'([^<>\s]+)@k\b', lambda m: ' '.join(m.group(1)).upper(), utterance)
    else:
        utterance = re.sub(r'[^<>\s]+@k\b', '<unk>', utterance)

    # Letter (@l)
    if spec_form_cfg.get('letter', True):
        utterance = re.sub(r'([^<>\s]+)@l\b', lambda m: m.group(1).upper(), utterance)
    else:
        utterance = re.sub(r'[^<>\s]+@l\b', '<unk>', utterance)

    # Neologism (@n)
    if spec_form_cfg.get('neologism', False):
        utterance = re.sub(r'([^<>\s]+)@n\b', r'\1' + ' <neo>', utterance)
    else:
        utterance = re.sub(r'([^<>\s]+)@n\b', r'\1', utterance)

    # Phonological consistent forms (PCFs, @p)
    if spec_form_cfg.get('pcf', False):
        utterance = re.sub(r'([^<>\s]+)@p\b', r'\1', utterance)
    else:
        utterance = re.sub(r'[^<>\s]+@p\b', '<unk>', utterance)

    # Metalinguistics (@q)
    if spec_form_cfg.get('metaling', False):
        utterance = re.sub(r'([^<>\s]+)@q\b', r'"\1"', utterance)
    else:
        utterance = re.sub(r'([^<>\s]+)@q\b', r'\1', utterance)

    # Second language (@s)
    if spec_form_cfg.get('l2', True):
        utterance = re.sub(r'([^<>\s]+)@s[:$][^<>\s]+\b', r'\1', utterance)
    else:
        utterance = re.sub(r'[^<>\s]+@s[:$][^<>\s]+\b', '<unk>', utterance)

    # Onomatopoeias (@o)
    if spec_form_cfg.get('onomatopoeia', True):
        utterance = re.sub(r'([^<>\s]+)@o\b', lambda m: m.group(1).replace('_', ' '), utterance)
    else:
        utterance = re.sub(r'[^<>\s]+@o\b', '<unk>', utterance)

    # Test word (@t)
    if spec_form_cfg.get('testword', True):
        utterance = re.sub(r'([^<>\s]+)@t\b', r'\1', utterance)
    else:
        utterance = re.sub(r'[^<>\s]+@t\b', '<unk>', utterance)

    # Unibet (@u)
    if spec_form_cfg.get('unibet', False):
        utterance = re.sub(r'([^<>\s]+)@u\b', r'\1', utterance)
    else:
        utterance = re.sub(r'([^<>\s]+)@u\b', pho_tag, utterance)

    # Word Play (@wp)
    marker = spec_form_cfg.get('wordplay', '<unk>')
    utterance = re.sub(r'[^<>\s]+@wp\b', marker, utterance)

    # Excluded words (@x)
    if spec_form_cfg.get('excluded', False):
        utterance = re.sub(r'([^<>\s]+)@x\b', r'\1', utterance)
    else:
        utterance = re.sub(r'([^<>\s]+)@x\b', '<unk>', utterance)

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


def process_disfluencies(utterance: str, config: ChatConfig) -> str:
    """Process disfluency markers in CHAT format transcripts.

    Handles three types of disfluency markers:
    1. &+ : Phonological fragments (e.g., "&+sn dog")
    2. &- : Phonological fillers (e.g., "&-uh cat")
    3. &~ : Nonwords (e.g., "&~meowmeow pet")

    Args:
        utterance: Raw utterance text containing disfluency markers
        config: Configuration object with disfluency settings:
            - disfluency.fragment: How to handle &+ markers
            - disfluency.filler: How to handle &- markers
            - disfluency.nonwords: How to handle &~ markers

    Returns:
        Utterance with disfluency markers processed according to config settings

    Raises:
        DataIntegrityError: If config contains invalid handling option
    """
    disfluencies_cfg = config.utterance['disfluency']

    # Phonological Fragments (&+)
    handle = disfluencies_cfg.get('fragment', 'null')
    if handle == 'null':
        utterance = re.sub(r'&\+[^<>\s]+\s+', '', utterance)
    elif handle == 'keep':
        utterance = re.sub(r'&\+([^<>\s]+\s+)', r'\1', utterance)
    elif handle == 'unk':
        utterance = re.sub(r'&\+[^<>\s]+', '<unk>', utterance)
    else:
        raise DataIntegrityError(
            f'Invalid config format for "fragment": {disfluencies_cfg}',
            disfluencies_cfg
        )

    # Phonological Fillers (&-)
    handle = disfluencies_cfg.get('filler', 'null')
    if handle == 'null':
        utterance = re.sub(r'&\-[^<>\s]+\s+', '', utterance)
    elif handle == 'keep':
        utterance = re.sub(r'&\-([^<>\s]+\s+)', r'\1', utterance)
    elif handle == 'unk':
        utterance = re.sub(r'&\-[^<>\s]+', '<unk>', utterance)
    else:
        raise DataIntegrityError(
            f'Invalid config format for "filler": {disfluencies_cfg}',
            disfluencies_cfg
        )

    # Nonwords (&~)
    handle = disfluencies_cfg.get('nonwords', 'null')
    if handle == 'null':
        utterance = re.sub(r'&\~[^<>\s]+\s+', '', utterance)
    elif handle == 'keep':
        utterance = re.sub(r'&\~([^<>\s]+\s+)', r'\1', utterance)
    elif handle == 'unk':
        utterance = re.sub(r'&\~[^<>\s]+', '<unk>', utterance)
    else:
        raise DataIntegrityError(
            f'Invalid config format for "nonwords": {disfluencies_cfg}',
            disfluencies_cfg
        )

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
    """Process multiple scoped markers in CHAT format utterances.

    This includes paralinguistics, duration, explanations, alternatives, ...

    Args:
        utterance: The utterance containing paralinguistic markers.
        config: Configuration object with paralinguistic utterance settings

    Returns:
        The processed utterance with standardized event/explanation markup.
    """
    scope_cfg = config.utterance['scoped']

    # Special handles for overlap (10.4)
    # TODO: For now we just remove overlap marks
    if scope_cfg.get('alternative', False):
        raise NotImplementedError
    else:
        utterance = re.sub(r'\+\<\s*', '', utterance)
        utterance = re.sub(
            r'(?:<([^>]+)>|(\S+))\s*\[[<>{}]\d*\]',
            lambda m: m.group(1) or m.group(2),
            utterance
        )

    # Find all minimal regions with markers
    # Capture the identifier in group 4
    all_identifiers = [
        '=!', '=?', '=', '!!', '!', '#', ':', '::', '%', '?',
        '/', 'x', '//', '///', '/-', '/?', '*',
        'e', '+', '-', '^', '^c'
    ]
    all_identifiers = sorted(all_identifiers, key=len, reverse=True)

    # First, match the base text which can be either in <> or a single word
    base_pattern = r"""(?:<([^>]+)>|(\S+))"""

    # Then match one or more identifier-event pairs
    identifier_pattern = (
        # Start with [
        r"""\s*\[""" +

        # Identifier must come IMMEDIATELY after [
        fr"""({"|".join(re.escape(i) for i in all_identifiers)})""" +

        # Optional event text until ]
        r"""(?:\s*([^\]]*))?""" +

        # End with ]
        r"""\]"""
    )

    # Must have base text followed by ONE OR MORE identifier blocks
    full_pattern = base_pattern + f'(?:{identifier_pattern})+'

    # Use in code:
    regions = re.finditer(full_pattern, utterance)

    # Process each match from end to start
    replacements = []
    for match in regions:

        # Get base text
        phrase_in_brackets, word = match.groups()[:2]
        text = phrase_in_brackets if phrase_in_brackets else word
        start, end = match.span()

        # Only search for identifier-events in the part after the base text
        base_text = phrase_in_brackets if phrase_in_brackets else word
        full_text = match.group()
        remaining_text = full_text[len(base_text):]

        # Get all identifier-event pairs
        identifier_events = re.findall(
            fr"""\["""
            fr"""({"|".join(re.escape(i) for i in all_identifiers)})"""
            r"""(?:\s*([^\]]*))?"""
            r"""\]""",
            remaining_text
        )

        for identifier, event in identifier_events:

            # Excluded Material (10.4) & Postcodes (10.5)
            if identifier == '+':

                # Excluded Material (10.4)
                if event == 'exc':
                    if scope_cfg.get('excluded', True):
                        return ''
                    else:
                        replacements.append((
                            start, end, f'{text}'
                        ))

                # Back Channel (10.6)
                elif event == 'bch':
                    if scope_cfg.get('back_channel', True):
                        return ''
                    else:
                        replacements.append((
                            start, end, f'{text}'
                        ))

                # Included Turn (10.6)
                elif event == 'trn':
                    if scope_cfg.get('include_turn', True):
                        replacements.append((
                            start, end, f'{text}'
                        ))
                    else:
                        return ''

                # Postcode (10.6)
                else:
                    if scope_cfg.get('postcode', True):
                        return ''
                    else:
                        replacements.append((
                            start, end, f'{text}'
                        ))

            # Excluded Material (10.4)
            elif identifier == 'e':
                if scope_cfg.get('excluded', True):
                    replacements.append((
                        start, end+1, ''
                    ))
                else:
                    replacements.append((
                        start, end, f'{text}'
                    ))

            # Error Marking (10.5)
            elif identifier == '*':
                if scope_cfg.get('error', False):
                    return ''
                else:
                    replacements.append((
                        start, end+1, ''
                    ))

            # Precodes (10.6)
            elif identifier == '-':
                if scope_cfg.get('precode', False):
                    return ''
                else:
                    replacements.append((
                        start, end+1, ''
                    ))

            # Complex Local Events (9.10.3) and Paralinguistic Material (10.2)
            elif identifier == '^' or identifier == '=!':
                tag = scope_cfg.get('paralinguistic', 'ENV')
                if tag != 'null':
                    replacements.append((
                        start, end,
                        f'<{tag}> {event} <sep> {text} </{tag}>'
                    ))
                else:
                    replacements.append((
                        start, end, f'{text}'
                    ))

            # Alternative Transcription (10.3)
            elif identifier == '=?':
                if scope_cfg.get('alternative', False):
                    replacements.append((
                        start, end, f'{event}'
                    ))
                else:
                    replacements.append((
                        start, end, f'{text}'
                    ))

            # Explanation and Comment (10.3)
            elif identifier == '=' or identifier == '%':
                tag = scope_cfg.get('explanation', 'null')
                if tag != 'null':
                    replacements.append((
                        start, end,
                        f'<{tag}> {event} <sep> {text} </{tag}>'
                    ))
                else:
                    replacements.append((
                        start, end, f'{text}'
                    ))

            # Contrastive Stressing (10.2)
            elif identifier == '!!':
                assert (event is None) or (event == '')
                tag = scope_cfg.get('contra_stressing', 'stress')
                if tag != 'null':
                    replacements.append((
                        start, end,
                        f'<{tag}> {text} </{tag}>'
                    ))
                else:
                    replacements.append((
                        start, end, f'{text}'
                    ))

            # Stressing (10.2)
            elif identifier == '!':
                assert (event is None) or (event == '')
                tag = scope_cfg.get('stressing', 'stress')
                if tag != 'null':
                    replacements.append((
                        start, end,
                        f'<{tag}> {text} </{tag}>'
                    ))
                else:
                    replacements.append((
                        start, end, f'{text}'
                    ))

            # Duration (10.2)
            # TODO: For now we just remove duration marks
            elif identifier == '#':
                replacements.append((
                    start, end, f'{text}'
                ))

            # Best Guess (10.3)
            # TODO: For now we just remove guess marks
            elif identifier == '?':
                replacements.append((
                    start, end, f'{text}'
                ))

            # Replacement (of Real Word) (10.3)
            elif identifier == ':' or identifier == '::':
                if scope_cfg.get('replacement', True):
                    replacements.append((
                        start, end, f'{event}'
                    ))
                else:
                    replacements.append((
                        start, end, f'{text}'
                    ))

            # Repetition (10.4)
            elif identifier == '/' or identifier == 'x':
                if scope_cfg.get('repetition', False):
                    replacements.append((
                        start, end, f'{text}'
                    ))
                else:
                    replacements.append((
                        start, end+1, ''
                    ))

            # Retracing (10.4)
            elif identifier == '//':
                if scope_cfg.get('retracing', True):
                    replacements.append((
                        start, end, f'{text} ...'
                    ))
                else:
                    replacements.append((
                        start, end+1, ''
                    ))

            # Reformulation (10.4)
            elif identifier == '///':
                if scope_cfg.get('reformulation', True):
                    replacements.append((
                        start, end, f'{text} ...'
                    ))
                else:
                    replacements.append((
                        start, end+1, ''
                    ))

            # False Start Without Retracing (10.4)
            elif identifier == '/-':
                if scope_cfg.get('false_start', True):
                    replacements.append((
                        start, end, f'{text} ...'
                    ))
                else:
                    replacements.append((
                        start, end+1, ''
                    ))

            # Clause Delimiter (10.4)
            elif identifier == '^c':
                if scope_cfg.get('clause', True):
                    replacements.append((
                        start, end, f'{text}'
                    ))
                else:
                    replacements.append((
                        start, end+1, ''
                    ))

            else:
                continue

    # Apply replacements from end to start
    for start, end, replacement in sorted(replacements, reverse=True):
        utterance = utterance[:start] + replacement + utterance[end:]

    return utterance


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

    # Process basic separators and markers
    utterance = process_basic(utterance, config)

    # Process special utterance terminators and linkers
    utterance = process_linker(utterance, config)

    # Process incomplete words, must go after basic
    utterance = process_incomplete(utterance, config)

    # Process paralinguistic scope markers
    utterance = process_paralinguistic(utterance, config)

    # Process special forms, must go after paralinguistic
    utterance = process_special_form(utterance, config)

    # Process nonverbal token, before local event but after paralinguistic
    marker = config.utterance.get('nonverbal', '<0>')
    utterance = re.sub(r'0', marker, utterance)

    # Process local events, must go after paralinguistic
    utterance = process_local_event(utterance, config)

    # Process disfluencies
    utterance = process_disfluencies(utterance, config)

    # Process unidentifiable markers
    utterance = process_unidentifiable(utterance, config)

    # utterance = re.sub(r'\[.*?\]\s*', '', utterance)
    # utterance = re.sub(r'\<(.+?)\>', r'\1', utterance)

    words = re.findall(r"<\w+>|\b\w+'\w+|\b\w+", utterance)
    annotated_words = [f'{word}:{speaker}' for word in words]
    utterance = ' '.join(annotated_words) + ' '

    return True, utterance


def split_interposed(input_line: str, config: ChatConfig) -> List[str]:
    """Split an interposed utterance into separate speaker-labeled lines.

    Args:
        input_line (str): The input line containing interposed speech.

    Returns:
        str: The reformatted utterance with separate speaker designations.
    """
    speaker_id, utterance = input_line.split(':\t', 1)

    # Locate the split point
    split_marker = '&*'
    if split_marker in utterance:
        first_part, remaining = utterance.split(split_marker, 1)

        # Identify the next speaker token (e.g., "MOT")
        interpose_speaker, second_part = remaining.split(':', 1)
        second_part = second_part.strip()

        # Generate reformatted output
        if config.utterance.get('interposed', True):

            input_line_split = [
                '{speaker_id}:\t{first_part.strip()} +.',
                f"*{interpose_speaker}:\t{second_part.split(' ', 1)[0]} .",
                f"{speaker_id}:\t{' '.join(second_part.split(' ')[1:])}\n"
            ]

        else:
            input_line_split = [
                f"{speaker_id}:\t{first_part.strip()} {' '.join(second_part.split(' ')[1:])}\n",
            ]

    return input_line_split


def process_dependent_tier(input_line: str, config: ChatConfig) -> Tuple[bool, str]:
    """Process a dependent tier from the input.

    Args:
        input_line: The line to be processed as a dependent tier.

    Returns:
        A tuple containing:
            - bool: True if the line will be added to the processed file.
            - str: The processed line.
    """
    return False, input_line


def process_header(input_line: str, config: ChatConfig) -> Tuple[bool, str]:
    """Process a header line from the input.

    Args:
        input_line: The line to be processed as a header.

    Returns:
        A tuple containing:
            - bool: True if the line will be added to the processed file.
            - str: The processed line.
    """
    return False, input_line


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

            # Header
            if line.startswith('@'):
                keep_data, line = process_header(line, config)
                lines_proc = [line] if keep_data else []

            # Utterance
            elif line.startswith('*'):

                # Default
                if '&*' not in line:
                    keep_data, line = process_utterance(line, config)
                    lines_proc = [line] if keep_data else []

                # Interposed Words
                else:
                    lines_proc = []
                    lines_split = split_interposed(line, config)
                    for line_split in lines_split:
                        keep_data, line = process_utterance(line_split, config)
                        if keep_data:
                            lines_proc.append(line)

            # Dependent_Tier
            elif line.startswith('%'):
                keep_data, line = process_dependent_tier(line, config)
                lines_proc = [line] if keep_data else []

            else:
                raise DataIntegrityError(data=line)

            processed_lines.extend(lines_proc)

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
    output_file = 'prep/childes/plain_utterance.cha'
    config_path = 'configs/plain_utterance.yaml'
    process_cha_file(input_file, output_file, config_path)
