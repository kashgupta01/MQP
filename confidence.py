import pandas as pd

combined_csv = ("all_62_complexes\combined_llm_results.csv")

df = pd.read_csv(combined_csv, usecols=["Confidence Score"]) 

print(df)