TO RUN BATCHES:

1. adjust complexes as needed in make_batch.py
2. run make_batch.py to generate batches in .jsonl file 
3. check to see if batch (in terminal or openAI dashboard) is done then run download_output.py (function kinda bugged rn)
   - check to see if the downloaded file actually contains the data
   - if nothing just download the data from the openAI dashboard
4. run parse_output.py to convert to csv
   - it should work but the parsing is also messed up atm









`future`
- add .env so we don't have to manually enter/remove api key
- fix parsing with batches
- possibilty add dataset capability so don't have to manually enter complex names
