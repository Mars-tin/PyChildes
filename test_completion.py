"""test the completion ability of a model."""

import torch
from transformers import GPT2LMHeadModel, GPT2Tokenizer


def generate_text(model_path, input_text, num_return_sequences=5, max_length=50):
    """Generates text completions using a trained GPT-2 model.

    Args:
        model_path (str): Path to the trained GPT-2 model.
        input_text (str): Input text to generate completions for.
        num_return_sequences (int): Number of completions to generate.
        max_length (int): Maximum length of the generated sequence (including input).

    Returns:
        List[str]: Generated text completions.
    """
    # Load the trained model and tokenizer
    tokenizer = GPT2Tokenizer.from_pretrained('gpt2')
    model = GPT2LMHeadModel.from_pretrained(model_path)
    model.eval()  # Set model to evaluation mode

    # Encode the input text
    input_ids = tokenizer.encode(input_text, return_tensors='pt')

    # Generate completions
    with torch.no_grad():
        outputs = model.generate(
            input_ids=input_ids,
            max_length=max_length,
            num_return_sequences=num_return_sequences,
            do_sample=True,  # Enable sampling for diverse results
            top_k=50,        # Limit sampling to top-k tokens
            top_p=0.95,      # Use nucleus sampling
            temperature=0.7  # Adjust temperature for randomness
        )

    # Decode and return the completions
    return [tokenizer.decode(output, skip_special_tokens=True) for output in outputs]


if __name__ == '__main__':
    # Path to the trained model
    model_path = './gpt2_trained_model'

    # Input string
    input_text = 'Once upon a time in a distant land,'

    # Generate completions
    completions = generate_text(model_path, input_text, num_return_sequences=5, max_length=50)

    # Print the results
    print('Input Text:')
    print(input_text)
    print('\nGenerated Completions:')
    for i, completion in enumerate(completions):
        print(f'{i + 1}. {completion}')
