import json
import pandas as pd

# your target columns/fields
fields = [
    "Complex Name",
    "Organism",
    "Complex Function",
    "Proteins",
    "Genes",
    "Other Organisms",
    "Confidence Score"
]

def extract_fields(text):
    # ignore everything after the divider
    text = text.split('---', 1)[0]

    data = {}
    for i, field in enumerate(fields):
        prefix = field + ":"
        start = text.find(prefix)
        if start == -1:
            data[field] = ""
            continue

        # skip past "FieldName:"
        value_start = start + len(prefix)

        # find where the next field begins (or end‐of‐text)
        if i + 1 < len(fields):
            next_prefix = fields[i+1] + ":"
            end = text.find(next_prefix, value_start)
            if end == -1:
                end = len(text)
        else:
            end = len(text)

        # extract and clean up whitespace/newlines
        raw = text[value_start:end].strip()
        data[field] = " ".join(raw.split())

    return data

# now read your .jsonl, pull out the `content`, parse, and build rows
rows = []
with open("test_output.jsonl", encoding="utf8") as f:
    for line in f:
        obj = json.loads(line)
        content = obj["response"]["body"]["choices"][0]["message"]["content"]
        rec = extract_fields(content)
        rows.append(rec)

# dump to CSV
df = pd.DataFrame(rows, columns=fields)
df.to_csv("test_output.csv", index=False)
