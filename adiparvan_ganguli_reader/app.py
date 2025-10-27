from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
import json
from indic_transliteration import sanscript
import pandas as pd

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///annotations.db'
db = SQLAlchemy(app)


verse_mapper_df = pd.read_csv("data/mapper_fixed.csv")

# Load your JSON data
with open('./data/adiparvan.json', 'r') as infile:
    original = json.load(infile)

with open('./data/ganguli.json', 'r') as infile:
    translation = json.load(infile)

@app.route('/', methods=['POST',"GET"])
def index():
    # Set default to first chapter and first verse
    if request.method == "POST":
        for button in ["header_prev","footer_prev","header_next","footer_next"]:
            chapter = request.form.get(button, None)
            if chapter is not None:
                chapter = int(chapter)
                if "prev" in button:
                    prevchapter = chapter - 1
                    if prevchapter > 0:
                        chapter = prevchapter
                if "next" in button:
                    nextchapter = chapter + 1
                    if nextchapter <= verse_mapper_df.GanguliArabic.max():
                        chapter = nextchapter
                break
    else:
        default_chapter = 1  # Assuming chapters are indexed from 0
        # Fetch the default verse
        chapter = int(request.args.get('chapter', "1").strip())

    original, translation = process_chapter(chapter)
    return render_template("index.html",
                           original = original,
                           translation = translation,
                           chapter = chapter
                           )

@app.route('/', methods=['POST',"GET"])
def getPrevious():
    # Set default to first chapter and first verse
        original, translation = process_chapter(chapter)
        return render_template("index.html",
                               original = original,
                               translation = translation,
                               chapter = chapter)

def _insert_sloka_number(v):
    return """<div class="item v_num">""" + f'{v["chapter"]}.{v["sloka_number"]}.{v["verse_type_indicator"]}' + "</div>"

def critical_edition_verses(chapter):
    filter_ = verse_mapper_df[verse_mapper_df.GanguliArabic == chapter]

    ce_chapter, ce_vstart, ce_vend = filter_.CE.values[0],\
        filter_.CE_vstart.values[0],\
        filter_.CE_vend.values[0]
    print(chapter, ce_chapter)
    # total_chapter_length = len([v for v in original if v["chapter"] == ce])
    if ce_chapter == -1:
        return("")
    if ce_vend == -1:
        verses = [_insert_sloka_number(v)+
                  v["text"] for v in original\
                  if ((v["chapter"] == ce_chapter) and ((v["sloka_number"] + 1) >= ce_vstart))]
        return(verses)
    else:
        verses = [_insert_sloka_number(v) + v["text"] for v in original\
                  if ((v["chapter"] == ce_chapter)\
                      and ((v["sloka_number"] + 1) >= ce_vstart)\
                      and ((v["sloka_number"] + 1) <= ce_vend)
                      )]
        return(verses)

def process_chapter(chapter):
    """
    Chapter refers to the Ganguli chapter. 
    Extract the mapped verses in the critical edition to match this chapter definition
    """
    
    _original = "<br>".join(critical_edition_verses(chapter))
    _translation = [v["content"].replace("\n","<br>") for v in translation\
                       if ((v["chapter"] == chapter))][0]

    return(_original, _translation)



if __name__ == '__main__':
    app.run(debug=True)
