# script2_train_gpt2_with_checkpoints.py
import os
import torch
from torch.utils.data import DataLoader, Dataset
from transformers import GPT2Config, GPT2LMHeadModel, AdamW, get_scheduler
from tqdm import tqdm

class TokenizedDataset(Dataset):
    def __init__(self, tokenized_data_path):
        self.data = torch.load(tokenized_data_path)

    def __len__(self):
        return self.data.size(0)

    def __getitem__(self, idx):
        return self.data[idx]

def save_checkpoint(model, optimizer, scheduler, epoch, block_no, output_dir):
    """
    Saves a checkpoint of the model, optimizer, and scheduler.
    Args:
        model: The GPT-2 model.
        optimizer: The optimizer instance.
        scheduler: The learning rate scheduler.
        epoch: Current epoch number.
        block_no: Current block number in training.
        output_dir: Directory to save the checkpoint.
    """
    os.makedirs(output_dir, exist_ok=True)
    checkpoint_path = os.path.join(output_dir, f"checkpoint_{epoch}_{block_no}.pt")
    torch.save({
        "model_state_dict": model.state_dict(),
        "optimizer_state_dict": optimizer.state_dict(),
        "scheduler_state_dict": scheduler.state_dict(),
        "epoch": epoch,
        "block_no": block_no
    }, checkpoint_path)
    print(f"Checkpoint saved: {checkpoint_path}")

def train_gpt2_model(
    dataset_path, 
    output_dir, 
    checkpoint_dir, 
    block_size=128, 
    epochs=2, 
    batch_size=8, 
    lr=5e-5, 
    checkpoint_interval=100
):
    """
    Trains GPT-2 on the tokenized dataset and saves checkpoints.
    Args:
        dataset_path (str): Path to the tokenized dataset.
        output_dir (str): Directory to save the trained model.
        checkpoint_dir (str): Directory to save the checkpoints.
        block_size (int): Size of input sequence blocks.
        epochs (int): Number of training epochs.
        batch_size (int): Batch size for training.
        lr (float): Learning rate.
        checkpoint_interval (int): Number of training blocks between checkpoints.
    """
    # Load dataset
    dataset = TokenizedDataset(dataset_path)
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

    # Initialize model and optimizer
    config = GPT2Config(n_positions=block_size)
    model = GPT2LMHeadModel(config)
    optimizer = AdamW(model.parameters(), lr=lr)

    # Scheduler for learning rate decay
    num_training_steps = epochs * len(dataloader)
    lr_scheduler = get_scheduler("linear", optimizer=optimizer, num_warmup_steps=0, num_training_steps=num_training_steps)

    # Device setup
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)

    # Training loop
    model.train()
    global_block_no = 0  # Tracks the total number of processed blocks across epochs

    for epoch in range(epochs):
        epoch_loss = 0
        progress_bar = tqdm(dataloader, desc=f"Epoch {epoch + 1}/{epochs}")
        
        for batch_no, batch in enumerate(progress_bar):
            inputs = batch.to(device)

            # Forward pass
            outputs = model(input_ids=inputs, labels=inputs)
            loss = outputs.loss

            # Backward pass
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            lr_scheduler.step()

            # Log and accumulate loss
            epoch_loss += loss.item()
            progress_bar.set_postfix({"loss": loss.item()})

            # Increment global block number
            global_block_no += 1

            # Save checkpoint at intervals
            if global_block_no % checkpoint_interval == 0:
                save_checkpoint(model, optimizer, lr_scheduler, epoch, global_block_no, checkpoint_dir)

        print(f"Epoch {epoch + 1} completed. Average loss: {epoch_loss / len(dataloader)}")

    # Save the final model
    model.save_pretrained(output_dir)
    print(f"Model saved to {output_dir}.")

if __name__ == "__main__":
    dataset_path = "./tokenized_data.pt"  # Path to the tokenized dataset
    output_dir = "./gpt2_trained_model"  # Directory to save the final trained model
    checkpoint_dir = "./checkpoints"  # Directory to save checkpoints
    checkpoint_interval = 50  # Save checkpoint every 100 blocks

    train_gpt2_model(dataset_path, output_dir, checkpoint_dir, checkpoint_interval=checkpoint_interval)
