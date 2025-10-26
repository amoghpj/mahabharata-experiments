from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
import json
from vidyut.cheda import Chedaka
from indic_transliteration import sanscript

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///annotations.db'
db = SQLAlchemy(app)

# Load your JSON data
with open('./data/adiparvan.json', 'r') as infile:
    data = json.load(infile)

# Initialize Chedaka
chedaka = Chedaka("data/vidyut_data")

# Models
class Annotation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chapter = db.Column(db.Integer, nullable=False)
    shloka_id = db.Column(db.Integer, nullable=False)
    text = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f'<Annotation {self.id}>'


def create_db():
    with app.app_context():
        db.create_all()



@app.route('/')
def index():
    # Set default to first chapter and first verse
    default_chapter = 1  # Assuming chapters are indexed from 0
    default_shloka_id = 1  # Assuming shloka_id starts from 1
    # Fetch the default verse
    verse_lines = data[0]
    verse = ' <br> '.join(verse_lines["iast"])  # Use <br> for HTML line breaks
    verse_devnag = ' <br> '.join(verse_lines["devnag"])  # Use <br> for HTML line breaks
    slp1_text = [sanscript.transliterate(data=vl, 
                                        _from=sanscript.IAST, 
                                        _to=sanscript.SLP1)
                 for vl in verse_lines["iast"]]
    tokens_list = [chedaka.run(slpline) for slpline in slp1_text]
    tokenized_list = [[token.text for token in tokens] 
                      for tokens in tokens_list]
    return render_template('index.html', 
                           verse=verse_devnag, 
                           tokenized_list=tokenized_list, 
                           chapter=default_chapter, 
                           shloka_id=default_shloka_id)

def process_verse(chapter, shloka_id):
    """
    :returns:
    - list of strings of devnagari verse
    - list of list of tokenized dictionaries containing parse information
    """
    
    verse_lines_raw = [v for v in data\
                       if ((v["chapter"] == chapter)\
                           and (v["sloka_id"] == (shloka_id)))\
                       ][0]
    verse_lines = []
    verse_lines_devnag = []
    for line, linedn in zip(verse_lines_raw["iast"],
                            verse_lines_raw["devnag"]):
        for l in line.split(";"):
            verse_lines.append(l)
        for l in linedn.split(";"):
            verse_lines_devnag.append(l)


    verse = ' <br> '.join(verse_lines)
    verse_devnag = ' <br> '.join(verse_lines_devnag).replace("'","")
    slp1_text = [sanscript.transliterate(data=vl.replace("[","").replace("]",""), 
                                        _from=sanscript.IAST, 
                                        _to=sanscript.SLP1)
                 for vl in verse_lines]
    
    tokens_by_line = [chedaka.run(tok) for tok in slp1_text]
    tokenized_list = []
    attributes = ["lakara",
                  "prayoga",
                  "vacana",
                  "linga",
                  "vibhakti"]
    for line_tokens in tokens_by_line:
        line = []
        for token in line_tokens:
            meta = {"text": sanscript.transliterate(data=token.text,
                                                    _from = sanscript.SLP1,
                                                    _to=sanscript.IAST
                                                    )}
            for attr in attributes:
                if hasattr(token.data, attr):
                    meta[attr] = sanscript.transliterate(data=str(getattr(token.data, attr)),
                                                    _from = sanscript.SLP1,
                                                    _to=sanscript.IAST
                                                    )
                else:
                    meta[attr] = ""
            line.append(meta)
        tokenized_list.append(line)
    return(verse_devnag, tokenized_list)

@app.route('/get_shloka', methods=['POST'])
def get_shloka():
    chapter = int(request.form['chapter'])
    shloka_id = int(request.form['shloka_id'])
    verse_devnag, tokenized_list = process_verse(chapter, shloka_id)
    return jsonify({'verse': verse_devnag, 'tokenized_list': tokenized_list})

@app.route('/annotate', methods=['POST'])
def annotate():
    chapter = request.form['chapter']
    shloka_id = request.form['shloka_id']
    text = request.form['text']
    
    new_annotation = Annotation(chapter=chapter, shloka_id=shloka_id, text=text)
    db.session.add(new_annotation)
    db.session.commit()
    
    return redirect(url_for('index'))


if __name__ == '__main__':
    create_db()
    app.run(debug=True)
