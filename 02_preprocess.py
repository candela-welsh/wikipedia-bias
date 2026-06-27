import spacy
import pandas as pd
import re

df = pd.read_csv("dataset.csv")

nlp = spacy.load("en_core_web_lg")

END_SECTION_PATTERN = re.compile(
    r'\n\s*(?:See also|Notes|References|Bibliography|External links|Further reading)\b.*',
    re.IGNORECASE | re.DOTALL
)

def strip_trailing_sections(text):
    if not isinstance(text, str):
        return text
    return END_SECTION_PATTERN.sub('', text).strip()

def get_lemmas(doc):
    return [
        token.lemma_.lower() for token in doc
        if not token.is_stop and not token.is_punct and not token.is_space
    ]

def get_sentences(doc):
    return [sent.text.strip() for sent in doc.sents if sent.text.strip()]

df["text"] = df["text"].apply(strip_trailing_sections)
df["doc"] = df["text"].apply(nlp)
df["lemmas"] = df["doc"].apply(get_lemmas)
df["sentences"] = df["doc"].apply(get_sentences)
df.drop(columns=["doc"], inplace=True)

output_file = "processed.csv"
df.to_csv(output_file, index=False)

print(f"Processed {len(df)} articles and saved to {output_file}.")