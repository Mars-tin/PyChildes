# PyChildes: A Python-based CHILDES Corpus Preprocessor

## About

### Overview

**PyChildes** is a Python-based preprocessing toolkit designed for working with the [CHILDES](https://childes.talkbank.org/access/) corpus.
This tool is currently under active development to provide streamlined and efficient methods for processing and analyzing CHILDES data.

### CHILDES and CHAT

The **CHILDES** (Child Language Data Exchange System) corpus is a part of the larger [TalkBank](https://talkbank.org/) project, providing an invaluable resource for researchers studying child language acquisition. **PyChildes** aims to simplify the handling of these datasets by offering robust tools for preprocessing, transforming, and analyzing **CHAT-formatted** data files.

To learn more about the **CHAT Transcription Format**, please refer to the [official documentation](https://talkbank.org/manuals/CHAT.html).

When citing the use of [TalkBank](https://talkbank.org/) and [CHILDES](https://childes.talkbank.org/access/) facilities, please use this reference to the last printed version of the CHILDES manual:

```bibtex
@book{macwhinney2000childes,
    author    = {MacWhinney, Brian},
    title     = {The CHILDES Project: Tools for Analyzing Talk},
    edition   = {3rd},
    year      = {2000},
    publisher = {Lawrence Erlbaum Associates},
    address   = {Mahwah, NJ}
}
```

### Credit

If you find this tool useful, please give us credit by citing:

```bibtex
@misc{trabank,
    title={Trabank: A Toolkit for Computational Developmental Studies in Language Models},
    author={Ma, Ziqiao and Shi, Freda and Chai, Joyce},
    howpublished={https://github.com/Mars-tin/PyChildes},
    year={2025}
}
```

## Precommit Setup (For Contributors Only)
We use Google docstring format for our docstrings and the pre-commit library to check our code. To install pre-commit, run the following command:

```bash
conda install pre-commit  # or pip install pre-commit
pre-commit install
```

The pre-commit hooks will run automatically when you try to commit changes to the repository.

## Data Download (For Users)

Start by creating two sub-directories: `raw/` and `prep/` in `data/`.
```bash
mkdir raw
mkdir prep
mkdir raw/childes
mkdir prep/childes
```

### Download CHILDES English Transcripts (English)
- Download the [`Eng-NA`](https://childes.talkbank.org/access/Eng-UK/0-Eng-NA-MOR.zip) and [`Eng-UK`](https://childes.talkbank.org/access/Eng-UK/0-Eng-UK-MOR.zip) collections of the Childes corpora, or run the following scripts.
    ```bash
    cd raw/
    wget https://childes.talkbank.org/access/Eng-NA/0-Eng-NA-MOR.zip
    wget https://childes.talkbank.org/access/Eng-UK/0-Eng-UK-MOR.zip
    ```
- Unzip the file and organize it in the `raw/` directory as follows.

```bash
.
├── childes
│   ├── ENG-NA
│   │   └── ...
│   └── ENG-UK
│       ├── ...
│       └── Wells
│           ├── ...
│           └── Tony
│               ├── 010526.cha
│               ├── 010826.cha
│               ├── 011114.cha
│               ├── 020310.cha
│               ├── 020526.cha
│               ├── 020902.cha
│               ├── 021123.cha
│               ├── 030321.cha
│               └── 030608.cha
```

## Data Preparation

The script `prepare_childes.py` is designed to preprocess `.cha` files from the **CHILDES** corpus based on a specified configuration file.

### Arguments

- `--input_file` (str): Path to the `.cha` file to be processed.  
  **Default:** `raw/childes/Eng-NA/Bates/Free20/amy.cha`

- `--output_file` (str): Path where the processed `.cha` file will be saved.  
  **Default:** `prep/output.cha`

- `--config_path` (str): Path to the configuration file (`.yaml`) defining preprocessing rules and settings.  
  **Default:** `configs/default.yaml`

### Example

To process a file named `amy.cha` located at `raw/childes/Eng-NA/Bates/Free20/` using a custom configuration file `my_config.yaml`:

```bash
python prepare_childes.py --input_file raw/childes/Eng-NA/Bates/Free20/amy.cha --output_file prep/my_output.cha --config_path configs/my_config.yaml
```

The processed file will be saved to `prep/my_output.cha`.
