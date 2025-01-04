"""collect dataset from local .txt folder."""

import os
import re

import torch
from transformers import GPT2Tokenizer


def collect_and_tokenize_text(input_dir: str, output_file: str, block_size: str = 128):
    """Collects text files, tokenizes them, and saves the tokenized dataset.

    Args:
        input_dir (str): Directory containing text files.
        output_file (str): Path to save the tokenized dataset.
        block_size (int): Size of each block of tokens.
    """
    tokenizer = GPT2Tokenizer.from_pretrained('gpt2')

    all_text = ''
    # Read and combine text files
    for filename in os.listdir(input_dir):
        if filename.endswith('.txt'):
            with open(os.path.join(input_dir, filename), 'r', encoding='utf-8') as file:
                text = re.sub(r'\n+', '\n', file.read())
                all_text += text + '\n'

    # Tokenize the entire dataset
    tokens = tokenizer(all_text, return_tensors='pt', truncation=False)

    # Split into blocks of block_size
    input_ids = tokens['input_ids'].squeeze(0)
    num_blocks = len(input_ids) // block_size
    input_ids = input_ids[: num_blocks * block_size].reshape(-1, block_size)

    # Save the tokenized data
    torch.save(input_ids, output_file)
    print(f'Tokenized dataset saved to {output_file}.')


if __name__ == '__main__':
    input_dir = './text_files'  # Directory containing .txt files
    output_file = './tokenized_data.pt'  # Path to save tokenized dataset
    block_size = 128

    collect_and_tokenize_text(input_dir, output_file, block_size)
