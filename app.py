import os
from flask import Flask, request, jsonify, render_template
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from docx import Document

app = Flask(__name__)

# =========================
# DATA
# =========================
DATABASE_TEXTS = []
DATABASE_NAMES = []




# =========================
# TEXT EXTRACT
# =========================
def extract_text(file):
    name = file.filename.lower()

    if name.endswith(".txt"):
        return file.read().decode("utf-8", errors="ignore")

    if name.endswith(".docx"):
        doc = Document(file)
        return "\n".join(p.text for p in doc.paragraphs)

    return ""


# =========================
# MAIN PAGE
# =========================
@app.route("/")
def index():
    return render_template("index.html")


# =========================
# DB UPLOAD
# =========================
@app.route("/upload_db", methods=["POST"])
def upload_db():
    global DATABASE_TEXTS, DATABASE_NAMES

    files = request.files.getlist("files")

    DATABASE_TEXTS = []
    DATABASE_NAMES = []

    for f in files:
        text = extract_text(f)
        if text.strip():
            DATABASE_TEXTS.append(text)
            DATABASE_NAMES.append(f.filename)

    return jsonify({
        "message": "ok",
        "count": len(DATABASE_TEXTS)
    })


# =========================
# CHECK FILE LOAD
# =========================
@app.route("/upload_check_file", methods=["POST"])
def upload_check_file():
    file = request.files.get("file")

    if not file:
        return jsonify({"text": ""})

    return jsonify({
        "text": extract_text(file)
    })


# =========================
# MAIN CHECK
# =========================
@app.route("/check_all", methods=["POST"])
def check_all():

    global DATABASE_TEXTS, DATABASE_NAMES

    data = request.get_json(silent=True) or {}
    text = data.get("text", "").strip()

    if not text:
        return jsonify({"error": "empty text"})

    if not DATABASE_TEXTS:
        return jsonify({"error": "database empty"})

    # =========================
    # STATS
    # =========================
    words = len(text.split())
    chars = len(text)
    sentences = text.count(".") + text.count("!") + text.count("?")

    # =========================
    # PLAGIAT CHECK
    # =========================
    docs = DATABASE_TEXTS + [text]

    tfidf = TfidfVectorizer().fit_transform(docs)
    sims = cosine_similarity(tfidf[-1], tfidf[:-1])[0]

    results = []
    for i, sim in enumerate(sims):
        results.append({
            "file": DATABASE_NAMES[i],
            "percent": round(float(sim) * 100, 2)
        })

    max_sim = float(max(sims)) * 100 if len(sims) else 0
    uniq = 100 - max_sim

    # =========================
    # GRAMMAR CHECK
    # =========================

    errors = []
   
    # =========================
    # RESPONSE
    # =========================
    return jsonify({
        "max_similarity": round(max_sim, 2),
        "uniqueness": round(uniq, 2),

        "errors": errors,
        "plagiarism_details": results,

        "stats": {
            "words": words,
            "chars": chars,
            "sentences": sentences
        }
    })


# =========================
# PRODUCTION RUN (IMPORTANT)
# =========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)