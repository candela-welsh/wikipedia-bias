import pandas as pd
import glob


'Replace items in the keywords list to select the target articles. Returns exact matches'

keywords = [
    "Unidentified flying object",
    "1953 Iranian coup d'état",
    "1963 South Vietnamese coup d'état",
    "Apartheid",
    "Armenian genocide",
    "Cambodian genocide",
    "Anfal campaign",
    "Native Americans in the United States",
    "Scientology",
    "Soviet war crimes",
    "Chris Brown",
    "Angelina Jolie",
    "Brad Pitt",
    "Marilyn Manson",
    "Ozzy Osbourne",
    "Mikhail Gorbachev",
    "Saddam Hussein",
    "Vladimir Lenin",
    "Karl Marx",
    "Mother Teresa",
    "Elon Musk",
    "Andrew Tate",
    "Vladimir Putin",
    "Ronald Reagan",
    "Margaret Thatcher",
    "2003 invasion of Iraq",
    "Bashar al-Assad",
    "September 11 attacks",
    "Tibet",
    "Hezbollah",
    "Hamas",
    "Al-Qaeda",
    "Palestine Liberation Organization",
    "Same-sex marriage",
    "Saudi Arabia",
    "Abortion",
    "Gun control",
    "Healthcare reform in the United States",
    "Anarcho-capitalism",
    "Anti-Americanism",
    "Black supremacy",
    "National-anarchism",
    "Black Lives Matter",
    "Masculism",
    "People for the Ethical Treatment of Animals",
    "LGBTQ rights by country or territory",
    "Chinese intelligence activity abroad",
    "Cuba",
    "Politics of North Korea",
    "History of Israel",
    "Plame affair",
    "NATO",
    "CNN",
    "Criticism of Walmart",
    "Domestic violence",
    "Genocide denial",
    "Holodomor",
    "Russian interference in the 2016 United States elections",
    "Vector Marketing",
    "Salvador Allende",
    "Christian right",
    "Christian Science",
    "Anti-Christian sentiment",
    "Divorce",
    "Feminism",
    "Religion and LGBTQ people",
    "Islamophobia",
    "Mormonism",
    "Quran",
    "Sharia",
    "HIV/AIDS denialism",
    "Assisted suicide",
    "Euthanasia",
    "Eugenics",
    "Family planning",
    "Female genital mutilation",
    "Homeopathy",
    "Self-harm",
    "Surrogacy",
    "Veganism",
]


csv_files = sorted(glob.glob('wikipedia_batch_*.csv'))
all_matches = []

for file in csv_files:
    df = pd.read_csv(file)
    matches = df[df["title"].isin(keywords)]
    if not matches.empty:
        all_matches.append(matches)

if all_matches:
    result = pd.concat(all_matches, ignore_index=True)
    result = result.drop_duplicates(subset=["id"]).reset_index(drop=True)
    result.to_csv("dataset.csv", index=False)
    print(f"{len(result)} articles saved to dataset.csv.")
else:
    print("No matches found.")