from bs4 import BeautifulSoup
import bs4
import glob
import json
import pandas as pd

collect = []

def clean(body):
    # body = body.replace("\n\n\nSacred Texts\u00a0\n\n Hinduism\u00a0\n\n Mahabharata\u00a0\n\n Index\u00a0\n\n Previous\u00a0\n\n Next\u00a0\n\n","")
    body = body.replace("'\"\n\n\n\n\n\n\n\n | \n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n", "")
    body = body.replace("\n\n\n\u00a0\n\n \u00a0\n\n \u00a0\n\n \u00a0\n\n \u00a0\n\n \u00a0\n\n \n\n","")
    return(body)

df = pd.read_csv("data/pages.csv",names=["url","chapter"],header=None)
df["fname"] = ["data/" + v + ".html" for v in df.chapter.str.replace(" ","_").values]

print(df)
for i, row in df.iterrows():
    data = {}
    with open(row.fname, "r") as infile:
        contents = "\n".join(list(infile.readlines()))        
    soup = BeautifulSoup(contents, "html.parser")
    body_tag = soup.find('body')
    for a in body_tag.find_all('a'):
        if isinstance(a, bs4.element.Tag):
            a.decompose()
    for a in body_tag.find('script').children:
        if isinstance(a, bs4.element.Tag):
            a.decompose()
    data["chapter"] = i + 1
    data["chapter_string"]=row.chapter
    data["content"] = clean(body_tag.get_text())
    collect.append(data)

with open("ganguli.txt","w") as outfile:
    json.dump(collect,outfile)
