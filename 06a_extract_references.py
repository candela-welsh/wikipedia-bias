import csv
import os
import re
import requests
import mwparserfromhell


ARTICLES = [
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
LANG = "en"
OUTPUT_DIR = "referencias_wikipedia"
OUTPUT_FILE = "referencias.csv"

KNOWN_REF_TEMPLATES = {
    "citation",                                       
    "sfn", "harvnb", "harvp", "harvsp", "harvs", "harvtxt",
    "efn", "efn-ua", "efn-lr",
    "r", "rp",
    "note", "fn",
    "isbn",
    "qref",                                             
    "uscongrec",                                        
}

HEADERS = {
    "User-Agent": "AnalisisReferenciasBot/1.0 (candela.welsh@outlook.com)"
}

# Patrones para clasificar texto_libre por heuristica
_RE_HARVARD_ANCHOR  = re.compile(r"\[\[#[^\]]+\]\]")
_RE_WIKILINK        = re.compile(r"\[\[[^\]]+\]\]")
_RE_URL             = re.compile(r"https?://")
_RE_BARE_ISBN       = re.compile(r"\bISBN\b", re.IGNORECASE)

# Pagina suelta: "p. 15" o "pp. 12-34" sin apellido
_RE_PAGE_ONLY       = re.compile(r"^,?\s*pp?\.\s*\d")

# Harvard de solo pagina: "Apellido, pp. 12" — apellido puede tener particulas
# minusculas (van, der, du, de, al) y caracteres Unicode (cirílico, polaco...)
_RE_WORD            = r"[\w\u00c0-\u024f\u0400-\u04ff'\-]+"
_RE_NAME_PREFIX     = r"(?:" + _RE_WORD + r"(?:\s+(?:van|der|de|du|al|bin|von|el)\s+)?" + r")*"
_RE_HARVARD_PAGE    = re.compile(
    r"^,?\s*[A-Z\u0400-\u04ff]" + _RE_WORD +
    r"(?:[,;]\s*(?:[A-Z\u0400-\u04ff]" + _RE_WORD + r"|[A-Z]\.))*" +
    r",\s+pp?\.\s*\d",
    re.UNICODE,
)
# Harvard con anno o titulo en texto plano:
#   "Apellido (1987)"  /  "Apellido, ''Titulo''"  /  "Apellido, \"Titulo\""
#   Tambien cubre "Van der Ross, R. E.; ..." y cirílico
_RE_HARVARD_YEAR    = re.compile(
    r"^[A-Z\u0400-\u04ff]" + _RE_WORD +
    r"(?:\s+(?:van|der|de|du|al|bin|von|el)\s+" + _RE_WORD + r")?" +
    r"[\s,;(]",
    re.UNICODE,
)
# Titulo en cursiva wikitext al inicio: ''Texto''
_RE_ITALIC_TITLE    = re.compile(r"^''")


def fetch_wikitext(title, lang):
    url = f"https://{lang}.wikipedia.org/w/api.php"
    params = {
        "action": "parse",
        "page": title,
        "prop": "wikitext",
        "format": "json",
        "formatversion": 2,
    }
    r = requests.get(url, params=params, headers=HEADERS, timeout=30)
    r.raise_for_status()
    data = r.json()
    if "error" in data:
        raise ValueError(f"{title}: {data['error'].get('info', 'error desconocido')}")
    return data["parse"]["wikitext"]


def normalize_template_name(name):
    name = str(name).strip().lower()
    name = re.sub(r"\s+", "_", name)
    name = re.sub(r"[^a-z0-9_]", "", name)
    return name or "sin_nombre"


def is_ref_template(norm_name):
    if norm_name.startswith("cite"):
        return True
    base = norm_name.replace("_", "")
    for known in KNOWN_REF_TEMPLATES:
        if base == known.replace("-", "").replace("_", ""):
            return True
    return False


def classify_free_text(text):
    """
    Asigna un subtipo a referencias sin plantilla reconocida.
    El orden de comprobacion importa: de mas especifico a mas general.
    """
    if not text:
        return "ref_vacia"              # <ref name=X /> reutilizada, sin contenido

    # Plantilla no reconocida por KNOWN_REF_TEMPLATES ({{Algo|...}})
    if text.startswith("{{"):
        return "plantilla_externa"

    # URL presente -> referencia web sin plantilla
    if _RE_URL.search(text):
        return "web_sin_plantilla"

    # ISBN mencionado en texto plano
    if _RE_BARE_ISBN.search(text):
        return "isbn_sin_plantilla"

    # [[#Anchor|Texto]] — Harvard con enlace interno a ancla
    if _RE_HARVARD_ANCHOR.search(text):
        return "harvard_inline"

    # [[Articulo|Texto]] sin ancla — wikilink usado como referencia Harvard
    if _RE_WIKILINK.search(text):
        return "harvard_wikilink"

    # ''Titulo'' al inicio — publicacion en cursiva sin autor explicito
    if _RE_ITALIC_TITLE.match(text):
        return "titulo_cursiva"

    # "p. 15" o "pp. 12-34" sin apellido previo
    if _RE_PAGE_ONLY.match(text):
        return "harvard_pagina"

    # "Apellido, pp. X" — Harvard abreviado solo con pagina
    if _RE_HARVARD_PAGE.match(text):
        return "harvard_pagina"

    # "Apellido (año)" / "Apellido, Titulo" / cirílico / partículas minúsculas
    if _RE_HARVARD_YEAR.match(text):
        return "harvard_texto"

    return "texto_libre"                # nota al pie narrativa sin patron reconocible


def extract_refs(title, wikitext):
    code = mwparserfromhell.parse(wikitext)
    records = []
    ref_num = 0

    for tag in code.filter_tags(matches=lambda t: t.tag == "ref"):
        ref_num += 1
        contents = tag.contents
        if contents is None:
            contents_str = ""
        else:
            contents_str = str(contents).strip()

        templates = contents.filter_templates() if contents else []
        ref_templates = [
            t for t in templates
            if is_ref_template(normalize_template_name(t.name))
        ]

        if ref_templates:
            for tpl in ref_templates:
                tipo = normalize_template_name(tpl.name)
                params = {}
                for p in tpl.params:
                    key = str(p.name).strip()
                    value = str(p.value).strip()
                    params[key] = value
                record = {
                    "articulo": title,
                    "ref_num": ref_num,
                    "tipo": tipo,
                    "texto_referencia": "",
                }
                record.update(params)
                records.append(record)
        else:
            tipo = classify_free_text(contents_str)
            records.append({
                "articulo": title,
                "ref_num": ref_num,
                "tipo": tipo,
                "texto_referencia": contents_str,
            })

    return records


def write_single_csv(all_records, output_dir, filename):
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, filename)

    fixed_cols = ["articulo", "ref_num", "tipo", "texto_referencia"]
    param_cols = sorted({
        k for rec in all_records
        for k in rec
        if k not in fixed_cols
    })
    fieldnames = fixed_cols + param_cols

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for rec in all_records:
            writer.writerow(rec)

    return filepath, len(all_records)


def main():
    all_records = []
    for title in ARTICLES:
        try:
            wikitext = fetch_wikitext(title, LANG)
            records = extract_refs(title, wikitext)
            all_records.extend(records)
            sin_plantilla = sum(1 for r in records if r["tipo"] in (
                "texto_libre", "harvard_inline", "harvard_wikilink",
                "harvard_pagina", "harvard_texto", "titulo_cursiva",
                "web_sin_plantilla", "isbn_sin_plantilla",
                "plantilla_externa", "ref_vacia"))
            print(f"{title}: {len(records)} refs ({len(records)-sin_plantilla} con plantilla, {sin_plantilla} sin plantilla)")
        except Exception as e:
            print(f"ERROR en '{title}': {e}")

    if not all_records:
        print("No se extrajo ninguna referencia.")
        return

    filepath, total = write_single_csv(all_records, OUTPUT_DIR, OUTPUT_FILE)

    tipos = {}
    for rec in all_records:
        tipos[rec["tipo"]] = tipos.get(rec["tipo"], 0) + 1

    print(f"\nTotal: {total} referencias -> {filepath}")
    print("\nDesglose por tipo:")
    for tipo, count in sorted(tipos.items(), key=lambda x: -x[1]):
        print(f"  {tipo}: {count}")


if __name__ == "__main__":
    main()