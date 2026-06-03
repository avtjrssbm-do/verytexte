import os
from flask import Flask, request, jsonify, render_template
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from docx import Document

app = Flask(__name__)

# =========================
# Глобальное хранилище базы документов
# =========================
DATABASE_TEXTS = []
DATABASE_NAMES = []


# =========================
# Извлечение текста из файла
# =========================
def extract_text(file):
    name = file.filename.lower()

    # Чтение текстового файла
    if name.endswith(".txt"):
        return file.read().decode("utf-8", errors="ignore")

    # Чтение документа Word
    if name.endswith(".docx"):
        doc = Document(file)
        return "\n".join(p.text for p in doc.paragraphs)

    # Неподдерживаемый формат
    return ""


# =========================
# Главная страница приложения
# =========================
@app.route("/")
def index():
    return render_template("index.html")


# =========================
# Загрузка базы для проверки уникальности
# =========================
@app.route("/upload_db", methods=["POST"])
def upload_db():
    global DATABASE_TEXTS, DATABASE_NAMES

    files = request.files.getlist("files")

    # Очищаем текущую базу
    DATABASE_TEXTS = []
    DATABASE_NAMES = []

    for f in files:
        text = extract_text(f)

        # Сохраняем только непустые документы
        if text.strip():
            DATABASE_TEXTS.append(text)
            DATABASE_NAMES.append(f.filename)

    return jsonify({
        "message": "ok",
        "count": len(DATABASE_TEXTS)
    })


# =========================
# Загрузка файла для проверки
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
# Основная проверка текста
# =========================
@app.route("/check_all", methods=["POST"])
def check_all():

    global DATABASE_TEXTS, DATABASE_NAMES

    data = request.get_json(silent=True) or {}
    text = data.get("text", "").strip()

    # Проверяем наличие текста
    if not text:
        return jsonify({"error": "empty text"})

    # Проверяем наличие загруженной базы
    if not DATABASE_TEXTS:
        return jsonify({"error": "database empty"})

    # =========================
    # Подсчёт статистики текста
    # =========================
    words = len(text.split())
    chars = len(text)
    sentences = text.count(".") + text.count("!") + text.count("?")

    # =========================
    # Проверка на заимствования
    # =========================

    # Добавляем проверяемый текст к базе
    docs = DATABASE_TEXTS + [text]

    # Строим TF-IDF матрицу
    tfidf = TfidfVectorizer().fit_transform(docs)

    # Вычисляем сходство с каждым документом базы
    sims = cosine_similarity(tfidf[-1], tfidf[:-1])[0]

    results = []

    for i, sim in enumerate(sims):
        results.append({
            "file": DATABASE_NAMES[i],
            "percent": round(float(sim) * 100, 2)
        })

    # Максимальный процент совпадения
    max_sim = float(max(sims)) * 100 if len(sims) else 0

    # Процент уникальности текста
    uniq = 100 - max_sim

    # =========================
    # Проверка орфографии и грамматики
    # =========================

    errors = []

    # Здесь можно добавить LanguageTool,
    # pymorphy2 или другую систему проверки

    # =========================
    # Формирование ответа клиенту
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
# Запуск приложения
# =========================
if __name__ == "__main__":

    # Получаем порт из переменных окружения
    # (например, для Render или Railway)
    port = int(os.environ.get("PORT", 5000))

    # Запускаем Flask-сервер
    app.run(
        host="0.0.0.0",
        port=port
    )