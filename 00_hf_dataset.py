import pandas as pd
from datasets import load_dataset

dataset = load_dataset("omarkamali/wikipedia-monthly", "latest.en", split="train", streaming=True)

batch_size = 1000

processed_batch_count = 0
current_batch = []

for i, record in enumerate(dataset):
    current_batch.append(record)

    if len(current_batch) == batch_size:
        batch_df = pd.DataFrame(current_batch)
        filename = f'wikipedia_batch_{processed_batch_count}.csv'
        batch_df.to_csv(filename, index=False)
        print(f'Saved {len(batch_df)} records to {filename}')

        current_batch = []
        processed_batch_count += 1

if current_batch:
    batch_df = pd.DataFrame(current_batch)
    filename = f'wikipedia_batch_{processed_batch_count}.csv'
    batch_df.to_csv(filename, index=False)
    print(f'Saved {len(batch_df)} records to {filename}')
    processed_batch_count += 1

print(f"Finished processing and saving {processed_batch_count} batches.")