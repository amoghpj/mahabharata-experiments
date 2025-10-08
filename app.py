from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import json
import re

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///annotations.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Define the Annotation model
class Annotation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chapter_verse = db.Column(db.String, nullable=False, unique=True)
    text = db.Column(db.Text, nullable=False)

# Load verses from the JSON file
def load_verses():
    with open('./dat/gita.json', 'r') as f:
        return json.load(f)

def convert_references(annotation):
    def replace_reference(match):
        ch, vs = match.group().split('_')
        return f'<a href="?chapter={ch}&verse={vs}">Verse {ch}:{vs}</a>'
    
    return re.sub(r'\d+_\d+', replace_reference, annotation)


def buttonify(text, chapter, verse):
    s = "<a href=?chapter=" + str(chapter) + "&verse=" + str(verse) + ">" + text + "</a>"
    return s

@app.route('/', methods=['GET', 'POST'])
def index():
    verses = load_verses()
    search_query = request.args.get('search', '').strip()
    search_verses = []
    if search_query:
        # Filter verses based on the transliteration matching the search query
        search_verses = [buttonify(v["text"], v["chapter_number"],v["verse_number"])
                         for v in verses if search_query.lower()\
                         in v['transliteration'].lower()]

    chapter_number = int(request.args.get('chapter', 1))
    verse_number = int(request.args.get('verse', 1))

    verse = next((v for v in verses if v['chapter_number'] == chapter_number and v['verse_number'] == verse_number), None)

    if request.method == 'POST':
        annotation_text = request.form['annotation'].strip()

        if annotation_text:
            # Check if the annotation already exists
            existing_annotation = Annotation.query.filter_by(chapter_verse=f"{chapter_number}_{verse_number}").first()

            if existing_annotation:
                # Update existing annotation
                existing_annotation.text = annotation_text
            else:
                # Save the new annotation to the database
                annotation_entry = Annotation(chapter_verse=f"{chapter_number}_{verse_number}", text=annotation_text)
                db.session.add(annotation_entry)

            db.session.commit()

            return redirect(url_for('index', chapter=chapter_number, verse=verse_number))

    # Retrieve existing annotation from the database
    annotation = Annotation.query.filter_by(chapter_verse=f"{chapter_number}_{verse_number}").first()
    annotation_text = annotation.text if annotation else ""
    annotated_text = convert_references(annotation_text)

    # Find all annotations that refer to this verse
    referring_annotations = Annotation.query.filter(Annotation.text.like(f"%{chapter_number}_{verse_number}%")).all()
    referring_annotated_texts = {a.chapter_verse: "[" + buttonify(a.chapter_verse, 
                                                                  a.chapter_verse.split("_")[0],
                                                                  a.chapter_verse.split("_")[1])
                                 + "] "\
                                 +  convert_references(a.text) for a in referring_annotations}
    vtext = verse.get("text","")
    delim_idx = vtext.find("।")
    verse["text_0"] = vtext[:delim_idx]
    verse["text_1"] = vtext[delim_idx + 1 :]
    # Add these variables before rendering the template in `index()`
    total_chapters = max([v["chapter_number"] for v in verses])  # Assuming verses is a list of chapters
    verses_in_chapter = {chapter: len([v for v in verses if v["chapter_number"] == chapter])\
                         for chapter in range(1,total_chapters)}  # Adjust per actual structure
    return render_template('index.html',
                           verse=verse,
                           chapter_number=chapter_number,
                           verse_number=verse_number,
                           annotation=annotated_text,
                           referring_annotations=referring_annotated_texts,
                           search_query=search_query,
                           search_verses = search_verses,
                           total_chapters=total_chapters,
                           chapter = verse["chapter_number"],
                           verses_in_chapter=verses_in_chapter)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create the database tables within the application context
    app.run(debug=True)
