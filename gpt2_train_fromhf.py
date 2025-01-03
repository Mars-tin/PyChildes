import os
import torch
from datasets import load_dataset
from torch.utils.data import DataLoader, Subset
from transformers import GPT2Tokenizer, GPT2LMHeadModel, AdamW, get_scheduler
from tqdm import tqdm

# Initialize global constants
CHECKPOINT_DIR = "./checkpoints"
OUTPUT_DIR = "./gpt2_trained_model"
BATCH_SIZE = 8
BLOCK_SIZE = 512
EPOCHS = 2
LEARNING_RATE = 5e-5
CHECKPOINT_INTERVAL = 100


def save_checkpoint(model, optimizer, scheduler, epoch, block_no):
    """
    Save a checkpoint with the model, optimizer, scheduler, and dataset state.
    """
    os.makedirs(CHECKPOINT_DIR, exist_ok=True)
    checkpoint_path = os.path.join(CHECKPOINT_DIR, f"checkpoint_{epoch}_{block_no}.pt")
    torch.save({
        "model_state_dict": model.state_dict(),
        "optimizer_state_dict": optimizer.state_dict(),
        "scheduler_state_dict": scheduler.state_dict(),
        "epoch": epoch,
        "block_no": block_no,
    }, checkpoint_path)
    print(f"Checkpoint saved to {checkpoint_path}")


def load_checkpoint(checkpoint_path, dataset):
    """
    Load a checkpoint and restore the training state.
    """
    checkpoint = torch.load(checkpoint_path)

    # Restore model, optimizer, and scheduler states
    model = GPT2LMHeadModel.from_pretrained("gpt2")
    model.load_state_dict(checkpoint["model_state_dict"])
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    optimizer = AdamW(model.parameters(), lr=LEARNING_RATE)
    optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
    scheduler = get_scheduler(
        "linear", optimizer=optimizer, num_warmup_steps=0, num_training_steps=len(dataset) * EPOCHS
    )
    scheduler.load_state_dict(checkpoint["scheduler_state_dict"])

    # Restore dataset indices
    all_indices = list(range(len(dataset)))
    unused_subset = dataset.select(all_indices[checkpoint["block_no"]*BATCH_SIZE:])
    print(f"now size: {len(unused_subset)} instead of full {len(dataset)}")
    dataloader = DataLoader(unused_subset, batch_size=BATCH_SIZE, shuffle=False)

    metadata = {
        "epoch": checkpoint["epoch"],
        "block_no": checkpoint["block_no"]
    }
    return model, optimizer, scheduler, dataloader, metadata


def tokenize_function(example, tokenizer):
    """
    Tokenize the dataset examples.
    """
    return tokenizer(example["text"], truncation=True, padding="max_length", max_length=BLOCK_SIZE)


def prepare_dataloader(dataset, batch_size):
    """
    Prepare the DataLoader for the unused portion of the dataset.
    """
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=False)
    return dataloader


def train():
    """
    Main training loop with checkpointing and dataset tracking.
    """
    # Load the dataset
    dataset = load_dataset("wonderwind271/ACL-papers")["train"]
    tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
    tokenizer.pad_token = tokenizer.eos_token

    # Tokenize the dataset
    tokenized_dataset = dataset.map(lambda x: tokenize_function(x, tokenizer), batched=True)
    tokenized_dataset.set_format(type="torch", columns=["input_ids", "attention_mask"])

    # Initialize dataset indices
    total_indices = list(range(len(tokenized_dataset)))

    # Check if resuming from a checkpoint
    if os.path.exists(CHECKPOINT_DIR):
        latest_checkpoint = sorted(os.listdir(CHECKPOINT_DIR))[-1]
        print(f"Resuming from checkpoint: {latest_checkpoint}")
        checkpoint_path = os.path.join(CHECKPOINT_DIR, latest_checkpoint)
        model, optimizer, scheduler, dataloader, metadata = load_checkpoint(checkpoint_path, tokenized_dataset)
        start_epoch = metadata["epoch"]
        start_block_no = metadata["block_no"]
    else:
        print("Starting training from scratch.")
        model = GPT2LMHeadModel.from_pretrained("gpt2")
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model.to(device)
        optimizer = AdamW(model.parameters(), lr=LEARNING_RATE)
        scheduler = get_scheduler(
            "linear", optimizer=optimizer, num_warmup_steps=0, num_training_steps=len(total_indices) * EPOCHS
        )
        dataloader = prepare_dataloader(tokenized_dataset, BATCH_SIZE)
        start_epoch = 0
        start_block_no = 0

    # Move model to device
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    complete_dataloader = prepare_dataloader(tokenized_dataset, BATCH_SIZE)
    # Training loop
    model.train()
    global_block_no = start_block_no
    for epoch in range(start_epoch, EPOCHS):
        epoch_loss = 0
        if epoch == start_epoch:
            progress_bar = tqdm(dataloader, desc=f"Epoch {epoch + 1}/{EPOCHS}")
        else:
            progress_bar = tqdm(complete_dataloader, desc=f"Epoch {epoch + 1}/{EPOCHS}")

        for batch_no, batch in enumerate(progress_bar):
            batch = {key: value.to(device) for key, value in batch.items()}

            # Forward pass
            outputs = model(input_ids=batch["input_ids"], attention_mask=batch["attention_mask"], labels=batch["input_ids"])
            loss = outputs.loss

            # Backward pass
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            scheduler.step()

            # Log loss
            epoch_loss += loss.item()
            progress_bar.set_postfix({"loss": loss.item()})

            # Increment global block number
            global_block_no += 1

            # Save checkpoint
            if global_block_no % CHECKPOINT_INTERVAL == 0:
                save_checkpoint(model, optimizer, scheduler, epoch, global_block_no)

        print(f"Epoch {epoch + 1} completed. Average loss: {epoch_loss / len(dataloader)}")
        global_block_no = 0

    # Save the final model
    model.save_pretrained(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)
    print(f"Model saved to {OUTPUT_DIR}.")


if __name__ == "__main__":
    train()
