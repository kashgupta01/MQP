import openai
import json
import os
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.environ["OPENAI_API_KEY"]

complexes = [
    "Sodium leak channel complex",
    "Glycosylphosphatidylinositol-mannosyltransferase I complex"
]
 
prompt_techniques = {
    "zero-shot":
    "Perform a thorough analysis of the protein complex: {complex}. Avoid overgeneralization and \
    unnecessarily long answers. In your analysis, only include information that is specific to the organism that \
    the {complex} is most prominent in (either Human, Mouse, Caenorhabditis elegans, Drosophila melanogaster, or \
    Saccharomyces cerevisiae). Your analysis should include the organism the complex belongs to, complex name, \
    complex function, list of proteins the complex consists of, and a list of corresponding genes the proteins \
    belong to. Additionally, list the other organisms that the protein complex is found in only if applicable. After\
    completing your analysis, also assign a self confidence score for the data findings to help gauge the accuracy of the \
    information. The score should range from 0.00 to 1.00, with 0.00 being the lowest confidence and 1.00 indicating \
    the highest confidence. To determine your score, consider the following grading conventions: consistency of information \
    across different databases/sources(0.3 weight), supporting experimental data regarding the complex(0.3 weight), accuracy \
    of corresponding protein-gene mapping(0.25 weight), and the analysis information being specific to the organism that it is \
    most promininent in(0.15 weight). The weight in parentheses following each grading convention signifies how much each \
    criteria should effect the confidence score with a total of 1.00 if every criteria is completely accurate.", 

    "few-shot":        
    "Perform a thorough analysis of the protein \
    complex: {complex}. Avoid overgeneralization and unnecessarily long answers. In your analysis, only include \
    information that is specific to the organism that the {complex} is most prominent in (either Human, Mouse, \
    Caenorhabditis elegans, Drosophila melanogaster, or Saccharomyces cerevisiae). Your analysis should include:\
    \n-The organism the complex belongs to\
    \n-Complex name\
    \n-Complex function\
    \n-List of proteins the complex consists of\
    \n-List of corresponding genes the proteins belong to\
    \n-List of other organisms that the protein complex is found in only if applicable\
    \n\
    After completing your analysis, also assign a self confidence score for the data findings to help gauge the \
    accuracy of the information. The score should range from 0.00 to 1.00, with 0.00 being the lowest confidence \
    and 1.00 indicating the highest confidence. To determine your score, consider the following grading conventions:\
    \n-Consistency of information across different databases/sources(0.30 weight)\
    \n-Supporting experimental data regarding the complex(0.3 weight)\
    \n-Accuracy of corresponding protein-gene mapping(0.25 weight)\
    \n-The analysis information being specific to the organism that it is most promininent in(0.15 weight).\
    \n\
    The weight in parentheses following each grading convention signifies how much each criteria should effect \
    the confidence score with a total of 1.00 if every criteria is completely accurate. Here is an example \
    of the total output for two complexes:\
    \n'Complex Name: ATP4A-ATP4B complex'\
    \n'Complex Function: This is a part of the larger ATP4 or H+/K+ ATPase complex, a proton pump responsible \
    for gastric acid secretion in the stomach.'\
    \n'Organism: Human'\
    \n'Other Organisms: N/A'\
    \n'Proteins: Potassium-transporting ATPase alpha chain 1, Potassium-transporting ATPase subunit beta'\
    \n'Genes: ATP4A, ATP4B'\
    \n'Self Confidence Score: 0.97'\
    \n\
    \n'Complex Name: Sodium leak channel complex'\
    \n'Complex Function: Voltage-gated ion channel responsible for the depolarizing sodium (Na+) leak currentsthat \
    determine resting Na(+) permeability and control neuronal excitability. Functions downstream of the molecular \
    circadian clock in pacemaker neurons to promote behavioral rhythmicity.'\
    \n'Organism: Drosophila melanogaster'\
    \n'Other Organisms: Human, Caenorhabditis elegans'\
    \n'Proteins: Protein unc-80 homolog, Narrow abdomen isoform F, Uncoordinated 79 isoform B'\
    \n'Genes: unc80, na, unc79'\
    \n'Self Confidence Score: 0.92'",

    "contextual": 
    "You are an expert in the field of biology and molecular machines. Perform a thorough analysis of the protein \
    complex: {complex}. Avoid overgeneralization and unnecessarily long answers. In your analysis, only include \
    information that is specific to the organism that the {complex} is most prominent in (either Human, Mouse, \
    Caenorhabditis elegans, Drosophila melanogaster, or Saccharomyces cerevisiae). Your analysis should include:\
    \n-The organism the complex belongs to\
    \n-Complex name\
    \n-Complex function\
    \n-List of proteins the complex consists of\
    \n-List of corresponding genes the proteins belong to\
    \n-List of other organisms that the protein complex is found in only if applicable\
    \n\
    After completing your analysis, also assign a self confidence score for the data findings to help gauge the \
    accuracy of the information. The score should range from 0.00 to 1.00, with 0.00 being the lowest confidence \
    and 1.00 indicating the highest confidence. To determine your score, consider the following grading conventions:\
    \n-Consistency of information across different databases/sources(0.30 weight)\
    \n-Supporting experimental data regarding the complex(0.3 weight)\
    \n-Accuracy of corresponding protein-gene mapping(0.25 weight)\
    \n-The analysis information being specific to the organism that it is most promininent in(0.15 weight).\
    \n\
    The weight in parentheses following each grading convention signifies how much each criteria should effect \
    the confidence score with a total of 1.00 if every criteria is completely accurate. Here is an example \
    of the total output for two complexes:\
    \n'Complex Name: ATP4A-ATP4B complex'\
    \n'Complex Function: This is a part of the larger ATP4 or H+/K+ ATPase complex, a proton pump responsible \
    for gastric acid secretion in the stomach.'\
    \n'Organism: Human'\
    \n'Other Organisms: N/A'\
    \n'Proteins: Potassium-transporting ATPase alpha chain 1, Potassium-transporting ATPase subunit beta'\
    \n'Genes: ATP4A, ATP4B'\
    \n'Self Confidence Score: 0.97'\
    \n\
    \n'Complex Name: Sodium leak channel complex'\
    \n'Complex Function: Voltage-gated ion channel responsible for the depolarizing sodium (Na+) leak currentsthat \
    determine resting Na(+) permeability and control neuronal excitability. Functions downstream of the molecular \
    circadian clock in pacemaker neurons to promote behavioral rhythmicity.'\
    \n'Organism: Drosophila melanogaster'\
    \n'Other Organisms: Human, Caenorhabditis elegans'\
    \n'Proteins: Protein unc-80 homolog, Narrow abdomen isoform F, Uncoordinated 79 isoform B'\
    \n'Genes: unc80, na, unc79'\
    \n'Self Confidence Score: 0.92'" 
    
}


# make jsonl file
with open("batch_input.jsonl", "w") as f:
    for complex_name in complexes:
        for technique, template in prompt_techniques.items():
            prompt = template.format(complex=complex_name).replace("    ", "")
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
