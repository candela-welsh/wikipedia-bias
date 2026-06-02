import spacy
import pandas as pd

df = pd.read_csv("dataset.csv")

nlp = spacy.load("en_core_web_lg")

def preprocess(text):
    doc = nlp(text)
    tokens = [token for token in doc if not token.is_stop and not token.is_punct and not token.is_space]
    lemmas = [token.lemma_.lower() for token in tokens]
    return doc, lemmas

output_file = "processed_samples.csv"

df["doc"] = df["text"].apply(lambda x: nlp(x))
df["lemmas"] = df["doc"].apply(lambda doc: [
    token.lemma_.lower() for token in doc
    if not token.is_stop and not token.is_punct and not token.is_space
])

df.to_csv(output_file, index=False)

print(f"Processed {len(df)} articles and saved to {output_file}.")