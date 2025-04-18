import json
import pandas as pd
import re

data = []

with open("batch_output_6.jsonl", "r") as f:
    for i, line in enumerate(f, start=1):
        obj = json.loads(line)
        
        custom_id = obj.get("custom_id", "")
        if "|" in custom_id:
            complex_name, technique = custom_id.split("|", 1)
        else:
            complex_name, technique = custom_id, "unknown"

        llm_name = "ChatGPT"  # just for now since only testing with chatGPT

        # try to get the content
        try:
            content = obj["response"]["body"]["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"[{i}] Error extracting content for {custom_id}: {e}")
            content = ""

        # clean the string
        content = content.strip().replace("’", "'")
        content = re.sub(r"^'+", "", content)  # remove starting quotes
        content = re.sub(r"\n'+", "\n", content)

        # try regex parse
        match = re.search(
            r"Complex Function:\s*(.*?)\s*Organism:\s*(.*?)\s*Other Organisms:\s*(.*?)\s*Proteins:\s*(.*?)\s*Genes:\s*(.*?)\s*Self Confidence Score:\s*(.*)",
            content,
            re.DOTALL
        )

        if match:
            complex_function, organism, other_organisms, proteins, genes, self_confidence_score = match.groups()
            data.append([
                complex_name.strip(),
                technique.strip(),
                llm_name,
                complex_function.strip(),
                organism.strip(),
                other_organisms.strip(),
                proteins.strip(),
                genes.strip(),
                self_confidence_score.strip(),
            ])
        else:
            print(f"[{i}] ⚠️ No match for {custom_id}. Raw content:\n{content[:300]}\n---")
            data.append([
                complex_name.strip(),
                technique.strip(),
                llm_name,
                "PARSE ERROR",
                "UNKNOWN",
                content.strip()
            ])

# create & save the dataframe
df = pd.DataFrame(data, columns=["Complex", "Technique", "LLM", "Complex Function", "Organism", "Other Organisms", "Proteins", "Genes", "Self Confidence Score"])

if df.empty:
    print("Still no results parsed. Double check your batch_output_6.jsonl format.")
else:
    df.to_csv("protein_complexes_results_from_batch_6.csv", index=False)
    print("Results saved to protein_complexes_results_from_batch_6.csv")
