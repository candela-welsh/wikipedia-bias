import pandas as pd
import glob


'Replace items in the keywords list to select the target articles. Returns exact matches'

keywords = ["Amber Heard", "Brad Pitt", "The Bible and homosexuality", "LGBTQ people and Islam", "Elizabeth II", "Hezbollah", "Thomas Sankara", "United States and state-sponsored terrorism", "Holodomor", "Peninsular War"]


pattern = "|".join(keywords)

csv_files = sorted(glob.glob('wikipedia_batch_*.csv'))

output_file = "dataset.csv"
first_write = True
match_count = 0

for file in csv_files:
    df = pd.read_csv(file)
    mask = df["title"].isin(keywords)
    matches = df[mask]
    
    if not matches.empty:
        matches.to_csv(output_file, mode="a", header=first_write, index=False)
        first_write = False
        match_count += len(matches)

print(f"{match_count} articles saved to {output_file}.")