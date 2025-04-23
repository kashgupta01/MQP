import pandas as pd

combined_csv = ("all_62_complexes\combined_llm_results.csv")

df = pd.read_csv(combined_csv)
 

for index, row in df.loc[:, ['Model', 'Technique', 'Confidence Score']].iterrows():
    print (row['Model'], row['Technique'], row['Confidence Score'])