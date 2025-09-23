from typing import Optional

import yaml

class ChatConfig:
    """Load and provide access to CHAT data processing configuration.

    This class loads configuration from a YAML file specifying how different
    CHAT data elements should be processed and transformed.

    Attributes:
        header: Configuration for header section processing.
        utterance: Configuration for utterance processing including
            special markers and transformations.
        dependent: Configuration for dependent tier processing.
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