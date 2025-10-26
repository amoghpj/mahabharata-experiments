import pandas as pd
import wget
import time
import os

df = pd.read_csv("pages.csv",header=None, names=["url","section"])
# help(wget)
for i, row in df.iterrows():
    print(row.section)
    outfile = "data/" + row.section.replace(" ", "_") + ".html"
    time.sleep(3)
    if not os.path.exists(outfile):
        wget.download(row.url, 
                      out= outfile)

