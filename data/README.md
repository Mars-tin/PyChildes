# TraBank Data Preprocessing

## Corpora for Cognitive Inquiry

### Childes Transcripts (English)
- Download the [`Eng-NA`](https://childes.talkbank.org/access/Eng-UK/0-Eng-NA-MOR.zip) and [`Eng-UK`](https://childes.talkbank.org/access/Eng-UK/0-Eng-UK-MOR.zip) collections of the Childes corpora, or run the following scripts.
    ```bash
    wget https://childes.talkbank.org/access/Eng-NA/0-Eng-NA-MOR.zip
    wget https://childes.talkbank.org/access/Eng-UK/0-Eng-UK-MOR.zip
    ```
- Unzip the file and organize the directory as follows.

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

### BabyLM Challenge Round 1 Corpora (100M)
- Download `train_100M.zip` at [osf.io](https://osf.io/download/rduj2/).
- Unzip the file and organize the directory as follows.

```bash
.
├── babylm_100m
│   ├── bnc_spoken.train
│   ├── childes.train
│   ├── gutenberg.train
│   ├── open_subtitles.train
│   ├── simple_wiki.train
│   └── switchboard.train
```