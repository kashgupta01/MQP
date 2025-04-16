import openai
import json

openai.api_key = ""

complexes = [
    "Kinetochore Mis12 complex",
    "Nuclear mitotic cohesin complex",
    "GPI-anchor transamidase complex"
]

prompt_techniques = {
    "zero-shot": """For each of the following protein {complex}, provide the role of the protein complex by 
    labelling it as 'Complex Function', but avoid overgeneralization and long answers. Give the organism it 
    belongs to (Human, Mouse, Caenorhabditis elegans, Drosophila melanogaster, or Saccharomyces cerevisiae) 
    by labelling it as 'Organism'. Additionally, include a list of proteins the {complex} consists of and label 
    the list 'Proteins'. Additionally, include a list of the corresponding genes the proteins belong to and 
    label this list 'Genes' """,
     
    "few-shot": """For each of the following protein {complex}, provide the role of the protein complex (avoid 
    generalization and long answers) and the organism it belongs to (Human, Mouse, Caenorhabditis elegans, 
    Drosophila melanogaster, or Saccharomyces cerevisiae). Additionally, include a list of proteins the {complex} 
    consists of. Additionally, include a list of corresponding genes for the proteins. Here is an example of the 
    output for one complex:

    'Complex Name: ATP4A-ATP4B complex'
    'Complex Function: This is a part of the larger ATP4 or H+/K+ ATPase complex, a proton pump responsible 
    for gastric acid secretion in the stomach.' 
    'Organism: Human'
    'Proteins: Potassium-transporting ATPase alpha chain 1, Potassium-transporting ATPase subunit beta' 
    'Genes: ATP4A(Human), ATP4B(Human)' """, 
            
    "contextual": """You are an expert in the field of biology and molecular machines. For each of the following 
    protein {complex}, provide the role of the protein complex (avoid generalization and long answers) and the 
    organism it belongs to (Human, Mouse, Caenorhabditis elegans, Drosophila melanogaster, or Saccharomyces 
    cerevisiae). Additionally, include a list of proteins the {complex} consists of. Additionally, include a 
    list of corresponding genes for the proteins. Here is an example of 
    the output for one complex:

    'Complex Name: ATP4A-ATP4B complex'
    'Complex Function: This is a part of the larger ATP4 or H+/K+ ATPase complex, a proton pump responsible 
    for gastric acid secretion in the stomach.' 
    'Organism: Human'
    'Proteins: Potassium-transporting ATPase alpha chain 1, Potassium-transporting ATPase subunit beta' 
    'Genes: ATP4A(Human), ATP4B(Human)' """, 
    
}

# make jsonl file
with open("batch_input.jsonl", "w") as f:
    for complex_name in complexes:
        for technique, template in prompt_techniques.items():
            prompt = template.format(complex=complex_name)
            json_line = {
                "custom_id": f"{complex_name}|{technique}",
                "method": "POST",
                "url": "/v1/chat/completions",
                "body": {
                    "model": "gpt-4",
                    "messages": [{"role": "user", "content": prompt}]
                }
            }
            f.write(json.dumps(json_line) + "\n")

# upload input file
upload = openai.files.create(file=open("batch_input.jsonl", "rb"), purpose="batch")

# create batch task
batch = openai.batches.create(
    input_file_id=upload.id,
    endpoint="/v1/chat/completions",
    completion_window="24h"
)

# save batch id
with open("batch_job_id.txt", "w") as f:
    f.write(batch.id)

print("Batch submitted. ID:", batch.id)
print("Status:", batch.status)
