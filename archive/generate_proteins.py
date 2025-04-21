import openai
import requests
import pandas as pd
import re 
import requests

# Initialize API keys 
#OPENAI_API_KEY = ""
PERPLEXITY_API_KEY = ""
# ANTHROPIC_API_KEY = ""

# Define LLM APIs
LLM_APIS = {
    #"ChatGPT": ("https://api.openai.com/v1/chat/completions", OPENAI_API_KEY),
    "Perplexity": ("https://api.perplexity.ai/chat/completions", PERPLEXITY_API_KEY),
    # "Anthropic": ("https://api.anthropic.com/v1/messages", ANTHROPIC_API_KEY)
}

# Define list of protein complexes (do in batches?)
complexes = ["""ATP4A-ATP4B complex"",
""Cytochrome bc1 Complex (Complex III)"",
""Synaptonemal Complex"",
""GNA12-GPR55-RGS2 complex"",
""Melanocortin receptor 3"",
""ATP1A1-TSHR complex"",
""ADRA1B-CXCR4 complex"",
""Bdkrb2-Tbxa2r complex"",
""Drd3-Ednrb complex"",
""Egflam-Gpr179 complex"",
""Ceacam1-4L-Syk-Tlr4 complex"",
""KDR-NRP1-VEGF165 complex"",
""NRP1-VEGF121 complex"",
""KDR-VEGF165 complex"",
""FLT4-VEGFC complex"",
""ITGA3-ITGB1 complex"",
"" Golgi-associated retrograde protein complex "",
"" Transmembrane channel-like (TMC) 2 complex "",
""13 subunit eukaryotic initiation factor 3 (eIF3) complex"",
""Tip60 chromatin-remodeling complex "",
""COP9 Signalosome "",
""20S proteosome "",
""HCN1-HCN4 complex"",
""GRIN1-P2RY4 complex "",
"" LY96-TLR4 complex "",
""RAD6-RAD18 ubiquitin ligase complex"",
""PHO85-PHO80 CDK-cyclin complex"",
""DNA polymerase (Pol) episolon (ε)"",
""Golgi transport complex"",
""GPI-anchor transamidase complex"",
""Glycosylphosphatidylinositol-mannosyltransferase I complex"",
""Dsl1 tethering complex"",
""AP-1 adaptor cpmplex (HA1, HA1 clathrin adaptor)"",
""PAN1 actin cytoskeleton-regulatory complex"",
""AMPK complex"",
""Augmin complex"",
""Myb-MuvB transcriptional activation complex"",
""CORVET tethering complex"",
""Sodium leak channel complex"",
""ATG1 protein kinase complex"",
""NXF1-NXT1 mRNA nuclear export factor complex"",
""MON1-CCZ1 guanyl-nucleotide exchange factor complex"",
""HipHop-HOAP telomere-capping complex"",
""ZFP-1(AF10)/DOT-1 complex"",
""ced-3-ced-4-mac-1 complex"",
""Nuclear mitotic cohesin complex"",
""Atk-1/Akt-2/Sgk-1 protein kinase complex"",
""RB1-E2F1-TFDP1 transcription repressor complex"",
""PETISCO, pid-1 variant"",
""PETISCO, tost-1 variant"",
""Ndc80 complex"",
""Kinetochore Mis12 complex"",
""THO complex"",
""Endosomal SNARE complex TLG2-VTI1-TLG1-SNC2"",
""Ste12/Dig1/Dig2 transcription regulation complex"",
""TRAPP II complex "",
""CCM complex "",
""mu-Calpain complex "",
""GINS complex "",
""CMG helicase complex "",
""20S mitochondrial small ribosomal subunit "",
""Cardiac troponin complex """]

# Define prompting techniques
prompt_techniques = {
    "zero-shot":
    "Perform a thorough analysis of the protein complex: {complex}. Avoid overgeneralization and \
    unnecessarily long answers. In your analysis, only include information that is specific to the organism that \
    the {complex} is most prominent in (either Human, Mouse, C. elegans, Drosophila melanogaster, or \
    Saccharomyces cerevisiae). Your analysis should include the organism the complex belongs to, complex name, \
    complex function, list of proteins the complex consists of, and a list of corresponding genes the proteins \
    belong to. Additionally, list the other organisms (from the 5 previously mentioned) that the protein complex is found in only if applicable. After\
    completing your analysis, also assign a self confidence score for the data findings to help gauge the accuracy of the \
    information. The score should range from 0.00 to 1.00, with 0.00 being the lowest confidence and 1.00 indicating \
    the highest confidence. To determine your score, consider the following grading conventions: consistency of information \
    across different databases/sources(0.3 weight), supporting experimental data regarding the complex(0.3 weight), accuracy \
    of corresponding protein-gene mapping(0.25 weight), and the analysis information being specific to the organism that it is \
    most promininent in(0.15 weight). The weight in parentheses following each grading convention signifies how much each \
    criteria should effect the confidence score with a total of 1.00 if every criteria is completely accurate. For the \
    confidence score portion please only return the full arithmetic equation with its numeric values. Your full analysis should include the following categories: \
    \n'Complex Name'\
    \n'Complex Function' \
    \n'Organism'\
    \n'Other Organisms'\
    \n'Proteins'\
    \n'Genes'\
    \n'Self Confidence Score'",

    "few-shot":        
    "Perform a thorough analysis of the protein \
    complex: {complex}. Avoid overgeneralization and unnecessarily long answers. In your analysis, only include \
    information that is specific to the organism that the {complex} is most prominent in (either Human, Mouse, \
    C. elegans, Drosophila melanogaster, or Saccharomyces cerevisiae). Your analysis should include:\
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
    the confidence score with a total of 1.00 if every criteria is completely accurate. Please only return the final confidence score equation with corresponding weights. Here is an example \
    of the total output for two complexes:\
    \n'Complex Name: ATP4A-ATP4B complex'\
    \n'Complex Function: This is a part of the larger ATP4 or H+/K+ ATPase complex, a proton pump responsible \
    for gastric acid secretion in the stomach.'\
    \n'Organism: Human'\
    \n'Other Organisms: N/A'\
    \n'Proteins: Potassium-transporting ATPase alpha chain 1, Potassium-transporting ATPase subunit beta'\
    \n'Genes: ATP4A, ATP4B'\
    \n'Self Confidence Score: (0.95 × 0.3) + (0.9 × 0.3) + (1.0 × 0.25) + (1.0 × 0.15) = 0.285 + 0.27 + 0.25 + 0.15  = **0.955**'\
    \n\
    \n'Complex Name: Sodium leak channel complex'\
    \n'Complex Function: Voltage-gated ion channel responsible for the depolarizing sodium (Na+) leak currentsthat \
    determine resting Na(+) permeability and control neuronal excitability. Functions downstream of the molecular \
    circadian clock in pacemaker neurons to promote behavioral rhythmicity.'\
    \n'Organism: Drosophila melanogaster'\
    \n'Other Organisms: Human, C. elegans'\
    \n'Proteins: Protein unc-80 homolog, Narrow abdomen isoform F, Uncoordinated 79 isoform B'\
    \n'Genes: unc80, na, unc79'\
    \n'Self Confidence Score: (0.8333 × 0.3) + (0.9 × 0.3) + (1.0 × 0.25) + (1.0 × 0.15) = 0.25 + 0.27 + 0.25 + 0.15 = **0.92**'",

    "contextual": 
    "You are an expert in the field of biology and molecular machines. Perform a thorough analysis of the protein \
    complex: {complex}. Avoid overgeneralization and unnecessarily long answers. In your analysis, only include \
    information that is specific to the organism that the {complex} is most prominent in (either Human, Mouse, \
    C. elegans, Drosophila melanogaster, or Saccharomyces cerevisiae). Your analysis should include:\
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
    the confidence score with a total of 1.00 if every criteria is completely accurate. Please only return the final confidence score equation with corresponding weights. Here is an example \
    of the total output for two complexes:\
    \n'Complex Name: ATP4A-ATP4B complex'\
    \n'Complex Function: This is a part of the larger ATP4 or H+/K+ ATPase complex, a proton pump responsible \
    for gastric acid secretion in the stomach.'\
    \n'Organism: Human'\
    \n'Other Organisms: N/A'\
    \n'Proteins: Potassium-transporting ATPase alpha chain 1, Potassium-transporting ATPase subunit beta'\
    \n'Genes: ATP4A, ATP4B'\
    \n'Self Confidence Score: (0.95 × 0.3) + (0.9 × 0.3) + (1.0 × 0.25) + (1.0 × 0.15) = 0.285 + 0.27 + 0.25 + 0.15  = **0.955**'\
    \n\
    \n'Complex Name: Sodium leak channel complex'\
    \n'Complex Function: Voltage-gated ion channel responsible for the depolarizing sodium (Na+) leak currentsthat \
    determine resting Na(+) permeability and control neuronal excitability. Functions downstream of the molecular \
    circadian clock in pacemaker neurons to promote behavioral rhythmicity.'\
    \n'Organism: Drosophila melanogaster'\
    \n'Other Organisms: Human, C. elegans'\
    \n'Proteins: Protein unc-80 homolog, Narrow abdomen isoform F, Uncoordinated 79 isoform B'\
    \n'Genes: unc80, na, unc79'\
    \n'Self Confidence Score: (0.8333 × 0.3) + (0.9 × 0.3) + (1.0 × 0.25) + (1.0 × 0.15) = 0.25 + 0.27 + 0.25 + 0.15 = **0.92**'",

    
}


# Initialize results list
results = []

#Method to call each API  
def call_api(llm_name, prompt):
    url, api_key = LLM_APIS[llm_name]
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    
    if llm_name == "ChatGPT":
        data = {"model": "gpt-4", "messages": [{"role": "user", "content": prompt}]}
    elif llm_name == "Perplexity":
        data = {"model": "sonar-pro", "messages": [{"role": "user", "content": prompt}]}
    # elif llm_name == "Anthropic":
    #     data = {"model": "claude-2", "messages": [{"role": "user", "content": prompt}]}
    
    response = requests.post(url, json=data, headers=headers)
    return response.json().get("choices", [{}])[0].get("message", {}).get("content", "")

data = []
# Loop through each complex and each prompt technique
#Right now it just records responses in 1 row, but find a way to do it in separated columns 
for complex_name in complexes:
    for technique, template in prompt_techniques.items():
        prompt = template.format(complex=complex_name)
        
        for llm_name in LLM_APIS.keys():
            response_text = call_api(llm_name, prompt)
            match = re.search(
                    r"Complex Function:\s*(.*?)\s*"
                    r"Organism:\s*(.*?)\s*"
                    r"Other Organisms:\s*(.*?)\s*"
                    r"Proteins:\s*(.*?)\s*"
                    r"Genes:\s*(.*?)\s*"
                    r"Confidence Score:\s*(.*)", 
                    response_text, 
                    re.DOTALL)
            if match:
                complex_function, organism, other_organisms, proteins, genes, confidence_score = match.groups()
                data.append([technique, complex_name, organism, other_organisms, complex_function, proteins, genes, confidence_score])


# Convert results to DataFrame
results_df = pd.DataFrame(data, columns = ["Technique", "Complex Name","Organism", "Other Organisms", "Complex Function", "Proteins", "Genes", "Confidence Score"])
results_df.to_csv("Perplexity_results.csv", index=False)

print("Data collection complete. Results saved to protein_complexes_results.csv.")
