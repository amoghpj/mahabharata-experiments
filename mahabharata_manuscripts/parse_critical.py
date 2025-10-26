import json
import re
from pprint import PrettyPrinter
import typing
import dspy
from typing import List, Literal
import sys

kashmiri = [f"K{i}" for i in range(7)]
maithili = ["V1"]
bangali = [f"B{i}" for i in range(1,5)]
devnagari_arjun = [f"Da{i}" for i in range(1,3)]
devnagari_nila = [f"Dn{i}" for i in range(1,4)]
devnagari_ratna = [f"Dr{i}" for i in range(1,5)]
devnagari= [f"D{i}" for i in range(1,15)]
telugu = [f"T{i}" for i in range(1,3)]
grantha = [f"G{i}" for i in range(1,8)]
malayalam = [f"M{i}" for i in range(1,5)]

allmanuscripts = []

allmanuscripts.extend(kashmiri)
allmanuscripts.extend(maithili)
allmanuscripts.extend(bangali)
allmanuscripts.extend(devnagari_arjun)
allmanuscripts.extend(devnagari_nila)
allmanuscripts.extend(devnagari_ratna)
allmanuscripts.extend(devnagari)
allmanuscripts.extend(telugu)
allmanuscripts.extend(grantha)
allmanuscripts.extend(malayalam)

# print(allmanuscripts)

class Manuscript(dspy.Signature):
    """Parse sentence and return all manuscript IDs.
    A manuscript ID starts with one or two letters  followed by a number. valid examples are K1, Dn3.
    The universe of manuscript IDs is:
    ['K0', 'K1', 'K2', 'K3', 'K4', 'K5', 'K6', 'V1', 'B1', 'B2', 'B3', 'B4', 'Da1', 'Da2', 'Dn1', 'Dn2', 'Dn3', 'Dr1', 'Dr2', 'Dr3', 'Dr4', 'D1', 'D2', 'D3', 'D4', 'D5', 'D6', 'D7', 'D8', 'D9', 'D10', 'D11', 'D12', 'D13', 'D14', 'T1', 'T2', 'G1', 'G2', 'G3', 'G4', 'G5', 'G6', 'G7', 'M1', 'M2', 'M3', 'M4']
    The input sentences reference manuscript IDs in the following ways:
    1. By initial letter: 
       - Input: "Da"
       - Output: ["Da1", "Da2", "Da3"]
    2. By a manuscript range: 
       - Input: "D1-4"
       - Output: ["D1", "D2", "D3", "D4"]
    3. By specific manuscript references, where each manuscript is separated by a ".": 
       - Input: "K1.3.5"
       - Output: ["K1", "K3", "K5"]
       manuscript references might be punctuated by comments: 
    4. Puncutated manuscript references:
       - Input: "G1 (see below).3"
       - Output: ["G1","G3"]
    
    Make sure to pay attention to qualifiers such as 'except' which are used to exclude specific manuscripts."""

    sentence: str = dspy.InputField()
    manuscript: List[Literal[*tuple(allmanuscripts)]] = dspy.OutputField()


lm = dspy.LM("openai/gpt-4o-mini",
             api_key=SECRET)
dspy.configure(lm=lm)


testset = [dspy.Example(sentence="% K4 (line 1 in marg.).5.6 V1 B D (except D14);", 
                        manuscript = ['K4','K5','K6', 'V1', 'B1', 'B2', 'B3', 'B4', 
                                      'D1', 'D2', 'D3', 'D4', 'D5', 'D6', 'D7', 'D8', 
                                      'D9', 'D10', 'D11', 'D12', 'D13']).with_inputs("sentence"),
           # dspy.Example(sentence="% D9-12 (see below) T1 G2.4.5 ins. after 3ab:",
           #              manuscript = ['D9', 'D10', 'D11', 'D12', 'T1', 'G2', 'G4', 'G5']).with_inputs("sentence"),
           # dspy.Example(sentence="% Da Dn3",
           #              manuscript = ['Da1',"Da2","Dn3"]).with_inputs("sentence")
           ]

#parse_manuscript = dspy.Predict(Manuscript)
parse_manuscript = dspy.ChainOfThought(Manuscript)

def score_fn(gt, predict):
    length_gt = float(len(gt["manuscript"]))
    num_correct= 0.
    for mid in gt["manuscript"]:
        if mid in predict["manuscript"]:
            num_correct +=1.
    return(num_correct/length_gt)

scores = []
for i, ex in enumerate(testset):
    pred = parse_manuscript(sentence=ex.inputs())
    
    print(f"Example {i}")
    print("\tSentence:",ex.inputs())
    print("\tGround Truth:",ex.labels)
    score = score_fn(ex.labels(), pred)
    print("\tManuscripts identified:", pred.manuscript)
    print("\tReasoning:", pred.reasoning)
    scores.append(score)
print(scores)
# evaluation = dspy.Evaluate(devset = testset)
# print(evaluation(Manuscript))
sys.exit()
             

pp = PrettyPrinter()

### First parse and build the main text
def parse_critical(fname):
    text = []
    with open(fname, "r") as infile:
        for entry in infile.readlines():
            if not entry.startswith("%"):
                data = {}
                uuid, line = entry.strip().split(" ", maxsplit = 1)
                ## uuid = 01001000a
                ## UUID = BBCCCVVVX
                data["uuid"] = uuid
                data["book"], data["chapter"], data["sloka_number"] = int(uuid[:2]),\
                    int(uuid[2:5]),\
                    int(uuid[5:8])
                data["text"] = line
                if len(uuid) == 9:
                    verse_type_indicator = uuid[-1]
                    if verse_type_indicator in ["A","B","C","D"]:
                        verse_type = "prose"
                    elif verse_type_indicator in ["a","b","c","d"]:
                        verse_type = "verse"
                else:
                    verse_type_indicator = ""
                    verse_type = "dialog"
                data["verse_type"] = verse_type
                data["verse_type_indicator"] = verse_type_indicator
                text.append(data)

    with open(fname.replace(".txt","json"),"w", encoding="utf-8") as out:
        json.dump(text, out, ensure_ascii=False)


def coarse_classifier(passage : str ) -> list:
    classification = []
    for line in passage.split("\n"):
        if line.startswith("%"):
            classification.append({"rawstring":line,
                                   "class": "metadata"})
        else:
            classification.append({"rawstring":line,
                                   "class": "content"})
    return(classification)


def annotator(classes : list) -> list:
    identifier_crit_re = re.compile(r"\% [\d]*\.[\d]*\.[\d]*")
    ## Chapter VerseNum LineNum VerseContent
    identifier_star_re = re.compile(r"(\d*)\*(\d*)_(\d*) (.*)")

    for i, line in enumerate(classes):
        if line["class"] == "metadata":
            if identifier_crit_re.match(line["rawstring"]):
                classes[i]["class_annotation"] = "identifier"
            else:
                classes[i]["class_annotation"] = "reference"
        if line["class"] == "content":
            matcher = identifier_star_re.match(line["rawstring"])
            if matcher:
                classes[i]["chapter"] = matcher.group(1)
                classes[i]["verse_num"] = matcher.group(2)
                classes[i]["line_num"] = matcher.group(3)
                classes[i]["verse"] = matcher.group(4)
            
    return(classes)


def split_group(an_class : list) -> list[list]:
    pass

def parse_grouped_star(gpass):
    ### On each line, first assign a coarse class, "metadata" or "content"
    classes = coarse_classifier(gpass)
    
    ### Do a second, pass, add annotations on each metadata object, classifying it either as
    ### identifier or reference
    annotated_classes = annotator(classes)

    ### Split passages based on groups of metadata
    grouped_passages = split_group(annotated_classes)
    return(annotated_classes)



def parse_supp(fname):
    text = []
    grouped_passages = []
    with open(fname, "r") as infile:
        fulltext = "\n".join([l.strip() for l in infile.readlines()])
    grouped_passages = fulltext.split("\n\n")
    for gpass in grouped_passages[3:10]:
        data = {}
        description = ""
        content = ""
        parsedlines = parse_grouped_star(gpass)
        pp.pprint(parsedlines)

        # group = .split("\n")
        # startnewgroup = False
        # for line in group:
        #     if line.startswith("% ") and not startnewgroup:
        #         startnewgroup = True
        #         description = description + line
        #     else:
        #         content = content + line
                
    # with open(fname.replace(".txt","json"),"w", encoding="utf-8") as out:
    #     json.dump(text, out, ensure_ascii=False)
    return(grouped_passages)


#parse_critical("MBh01.txt")
ret = parse_supp("MBh01_star.txt")

        
