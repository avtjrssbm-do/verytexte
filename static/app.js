console.log("loaded");

let errorsGlobal = [];

// =======================
// Загрузка базы документов
// =======================
async function uploadDB() {

    let input = document.getElementById("dbFiles");

    if (!input.files.length) {
        alert("Выберите файлы базы");
        return;
    }

    let formData = new FormData();

    for (let f of input.files) {
        formData.append("files", f);
    }

    let res = await fetch("/upload_db", {
        method: "POST",
        body: formData
    });

    let data = await res.json();

    alert(`Загружено документов: ${data.count}`);
}

// =======================
// Загрузка файла для проверки
// =======================
async function uploadCheckFile() {

    let input = document.getElementById("checkFile");

    if (!input.files.length) {
        alert("Выберите файл");
        return;
    }

    let formData = new FormData();

    formData.append("file", input.files[0]);

    let res = await fetch("/upload_check_file", {
        method: "POST",
        body: formData
    });

    let data = await res.json();

    // Заполняем редактор текстом из загруженного файла
    document.getElementById("editor").innerText =
        data.text || "";
}

// =======================
// Полная проверка текста
// =======================
async function checkAll() {

    let start = performance.now();

    // Получаем текст из редактора
    let text =
        document.getElementById("editor").innerText;

    let res = await fetch("/check_all", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ text })
    });

    let data = await res.json();

    if (data.error) {
        alert(data.error);
        return;
    }

    let end = performance.now();

    // =======================
    // Обновление карточек статистики
    // =======================

    document.getElementById("uniqValue").innerText =
        data.uniqueness + "%";

    document.getElementById("plagValue").innerText =
        data.max_similarity + "%";

    document.getElementById("errorsCount").innerText =
        (data.errors || []).length;

    document.getElementById("checkTime").innerText =
        ((end - start) / 1000).toFixed(2) + "с";

    // =======================
    // Вывод общей статистики текста
    // =======================

    document.getElementById("stats").innerHTML = `
        <div class="stat-line">
            <span>Слов</span>
            <b>${data.stats.words}</b>
        </div>

        <div class="stat-line">
            <span>Символов</span>
            <b>${data.stats.chars}</b>
        </div>

        <div class="stat-line">
            <span>Предложений</span>
            <b>${data.stats.sentences}</b>
        </div>
    `;

    // =======================
    // Отображение совпадений с базой
    // =======================

    let plagiarismHTML = "";

    data.plagiarism_details.forEach(d => {

        plagiarismHTML += `
            <div class="match-row">

                <div class="match-head">
                    <span>${d.file}</span>
                    <span>${d.percent}%</span>
                </div>

                <div class="progress">
                    <div class="fill" style="width:${d.percent}%"></div>
                </div>

            </div>
        `;
    });

    document.getElementById("plagiarism").innerHTML =
        plagiarismHTML;

    // =======================
    // Сохранение и отображение ошибок
    // =======================

    errorsGlobal = data.errors || [];

    renderErrors();
    highlightErrors(-1);
}

// =======================
// Формирование списка ошибок
// =======================
function renderErrors() {

    let box = document.getElementById("errorList");

    box.innerHTML = "";

    if (errorsGlobal.length === 0) {

        box.innerHTML = `
            <div class="success-box">
                ✅ Ошибок не найдено
            </div>
        `;
        return;
    }

    errorsGlobal.forEach((e, i) => {

        let suggestionsHTML = "";

        // Вывод вариантов исправления
        if (e.suggestions && e.suggestions.length > 0) {
            suggestionsHTML = `
                <div style="margin-top:8px; font-size:13px;">
                    <b>Варианты:</b>
                    <div>
                        ${e.suggestions.map(s => `
                            <div style="
                                display:inline-block;
                                margin:3px;
                                padding:4px 8px;
                                background:#fef9c3;
                                border-radius:6px;
                                cursor:default;
                            ">
                                ${s}
                            </div>
                        `).join("")}
                    </div>
                </div>
            `;
        }

        let div = document.createElement("div");
        div.className = "error-item";

        div.innerHTML = `
            <div class="error-number">${i + 1}</div>

            <div class="error-content">
                <strong>${e.error}</strong>
                <br>
                ${e.message || ""}
                ${suggestionsHTML}
            </div>
        `;

        // Переход к ошибке при клике
        div.onclick = () => goToError(i);

        box.appendChild(div);
    });
}

// =======================
// Подсветка ошибок в тексте
// =======================
function highlightErrors(active = -1) {

    let editor = document.getElementById("editor");

    let text = editor.innerText;
    let html = text;

    errorsGlobal.forEach((e, i) => {

        if (!e.error) return;

        // Выделяем активную ошибку отдельно
        let cls = (i === active)
            ? "error active"
            : "error";

        html = html.replaceAll(
            e.error,
            `<span class="${cls}" data-id="${i}">${e.error}</span>`
        );
    });

    editor.innerHTML = html;
}

// =======================
// Переход к выбранной ошибке
// =======================
function goToError(i) {

    // Подсвечиваем выбранную ошибку
    highlightErrors(i);

    let el = document.querySelector(`[data-id="${i}"]`);

    // Плавная прокрутка к ошибке
    if (el) {
        el.scrollIntoView({
            behavior: "smooth",
            block: "center"
        });
    }
}