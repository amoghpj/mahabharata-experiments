from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
import json
from indic_transliteration import sanscript

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///annotations.db'
db = SQLAlchemy(app)

# Load your JSON data
with open('./data/adiparvan.json', 'r') as infile:
    original = json.load(infile)

with open('./data/ganguli.json', 'r') as infile:
    translation = json.load(infile)

@app.route('/', methods=['POST',"GET"])
def index():
    # Set default to first chapter and first verse
    default_chapter = 1  # Assuming chapters are indexed from 0
    # Fetch the default verse
    chapter = int(request.args.get('chapter', "1").strip())

    original, translation = process_verse(chapter)
    return render_template("index.html",
                           original = original,
                           translation = translation)


def process_verse(chapter):
    """
    :returns:
    """
    
    _original = "<br>".join([v["text"] for v in original\
                       if ((v["chapter"] == chapter))])
    _translation = [v["content"].replace("\n","<br>") for v in translation\
                       if ((v["chapter"] == chapter))][0]

    return(_original, _translation)



if __name__ == '__main__':
    app.run(debug=True)
