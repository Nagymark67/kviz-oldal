import streamlit as st
import os
import json
import logging
import random
import uuid
from google import genai
from google.genai import types

# Téma és UI finomhangolás (Futurisztikus/Minimalista)
st.set_page_config(page_title="balekvizsgára", layout="centered")
st.markdown("""
<style>
    /* Futurisztikus gomb és letisztult UI elemek */
    .stButton>button {
        border: 1px solid #00ffaa;
        color: #00ffaa;
        background-color: transparent;
        transition: 0.3s;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .stButton>button:hover {
        background-color: #00ffaa;
        color: #000;
        box-shadow: 0 0 15px #00ffaa;
    }
    #MainMenu, footer, header {visibility: hidden;}
    hr {border-color: #333333;}
</style>
""", unsafe_allow_html=True)

api_key = st.secrets.get("GEMINI_API_KEY")
client = genai.Client(
    api_key=api_key,
    http_options=types.HttpOptions(timeout=60_000),
)

@st.cache_resource
def upload_pdf_to_gemini(file_path):
    return client.files.upload(file=file_path)

@st.cache_data
def generate_quiz_data(_document, question_count, batch_label, document_name, generation_seed, previous_questions, model_name):
    previous_questions_text = "\n".join(f"- {question}" for question in previous_questions)
    if not previous_questions_text:
        previous_questions_text = "Nincs korábbi kérdés."

    prompt = f"""
    Generálj pontosan {question_count} feleletválasztós kérdést a megadott dokumentum alapján magyar nyelven.
    Ez a(z) {batch_label}. kérdéscsomag. Keverd a témákat, ne kövesd a dokumentum sorrendjét.
    Legyen változatos a kérdéstípus: tényfelidézés, fogalommagyarázat, ok-okozat, összehasonlítás,
    következtetés és gyakorlati alkalmazás. Csak a dokumentumban szereplő információkra támaszkodj.
    Ne ismételd vagy fogalmazd át ezeket a korábbi kérdéseket:
    {previous_questions_text}
    Variációazonosító: {generation_seed}. Készíts ehhez új kérdésváltozatokat.
    Kizárólag egy JSON tömböt adj vissza, amely objektumokat tartalmaz a következő kulcsokkal: 
    'question' (sztring), 'options' (4 sztringből álló tömb), és 'answer' (sztring, amelynek pontosan meg kell egyeznie az egyik opcióval).
    """
    
    response = client.models.generate_content(
        model=model_name,
        contents=[
            _document,
            prompt
        ],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
        ),
    )
    return json.loads(response.text)


def generate_quiz_batch(_document, question_count, batch_label, document_name, generation_seed, previous_questions, model_name, progress_text):
    try:
        return generate_quiz_data(
            _document,
            question_count,
            batch_label,
            document_name,
            generation_seed,
            previous_questions,
            model_name,
        )
    except Exception as error:
        if getattr(error, "code", None) != 504 or question_count <= 1:
            raise

        first_count = question_count // 2
        progress_text.write(f"A Gemini időtúllépett; a(z) {batch_label}. csomagot kisebb részekben próbálom újra.")
        first_questions = generate_quiz_batch(
            _document,
            first_count,
            f"{batch_label}a",
            document_name,
            generation_seed,
            previous_questions,
            model_name,
            progress_text,
        )
        second_questions = generate_quiz_batch(
            _document,
            question_count - first_count,
            f"{batch_label}b",
            document_name,
            generation_seed,
            previous_questions + tuple(question["question"] for question in first_questions),
            model_name,
            progress_text,
        )
        return first_questions + second_questions


PDF_FILE_PATH = "document.pdf" 
QUIZ_QUESTION_COUNT = 50
QUESTIONS_PER_BATCH = 10
MODEL_OPTIONS = {
    "Gemini 3.8 Flash (gyorsabb)": "gemini-3.8-flash",
    "Gemini 3.1 Pro Preview (alaposabb)": "gemini-3.1-pro-preview",
}

if not os.path.exists(PDF_FILE_PATH):
    st.error(f"A(z) {PDF_FILE_PATH} fájl nem található.")
    st.stop()

st.title("balekvizsgára")
selected_model_label = st.selectbox("Gemini modell", list(MODEL_OPTIONS))
selected_model = MODEL_OPTIONS[selected_model_label]

if "quiz_model" in st.session_state and st.session_state.quiz_model != selected_model:
    st.info("A modellváltás az új kvíz generálásakor lép életbe.")

with st.spinner("Dokumentum feldolgozása..."):
    pdf_ref = upload_pdf_to_gemini(PDF_FILE_PATH)

if "quiz_data" in st.session_state and st.button("Új kvíz generálása"):
    for key in ("quiz_data", "quiz_seed", "quiz_model", "user_answers", "submitted"):
        st.session_state.pop(key, None)
    st.rerun()

if "quiz_data" not in st.session_state:
    if "quiz_seed" not in st.session_state:
        st.session_state.quiz_seed = uuid.uuid4().hex

    quiz_data = []
    progress_text = st.empty()
    progress_bar = st.progress(0)
    try:
        for batch_number, start in enumerate(range(0, QUIZ_QUESTION_COUNT, QUESTIONS_PER_BATCH)):
            question_count = min(QUESTIONS_PER_BATCH, QUIZ_QUESTION_COUNT - start)
            progress_text.write(f"Kérdések generálása: {len(quiz_data)} / {QUIZ_QUESTION_COUNT}")
            quiz_data.extend(generate_quiz_batch(
                pdf_ref,
                question_count,
                str(batch_number + 1),
                pdf_ref.name,
                st.session_state.quiz_seed,
                tuple(question["question"] for question in quiz_data),
                selected_model,
                progress_text,
            ))
            progress_bar.progress(len(quiz_data) / QUIZ_QUESTION_COUNT)
        random.shuffle(quiz_data)
        st.session_state.quiz_data = quiz_data
        st.session_state.quiz_model = selected_model
        progress_text.empty()
        progress_bar.empty()
    except Exception as error:
        progress_text.empty()
        progress_bar.empty()
        error_code = getattr(error, "code", None)
        logging.error("Quiz generation failed: %s (Gemini API status %s)", type(error).__name__, error_code)
        if error_code is not None:
            if error_code == 504:
                st.error("A Gemini API 504-es átjáró-időtúllépést jelzett még a kisebb kérdéscsomagoknál is. Próbáld a Flash modellt, vagy indítsd újra később.")
            else:
                st.error(f"A kérdésgenerálás sikertelen (Gemini API hiba: {error_code}).")
        else:
            st.error("A kérdésgenerálás időtúllépés vagy más hiba miatt megszakadt. Próbáld újra később.")
        st.stop()
else:
    quiz_data = st.session_state.quiz_data

if "user_answers" not in st.session_state:
    st.session_state.user_answers = {}
if "submitted" not in st.session_state:
    st.session_state.submitted = False

with st.form("quiz_form"):
    for i, q in enumerate(quiz_data):
        st.markdown(f"**{i+1}. {q['question']}**")
        st.session_state.user_answers[i] = st.radio(
            "Válassz egy opciót:",
            q['options'],
            key=f"q_{i}",
            index=None
        )
        st.markdown("---")
    
    submit = st.form_submit_button("Válaszok beküldése")
    if submit:
        st.session_state.submitted = True

if st.session_state.submitted:
    score = 0
    st.subheader("Eredmények")
    
    for i, q in enumerate(quiz_data):
        user_ans = st.session_state.user_answers.get(i)
        correct_ans = q['answer']
        
        if user_ans == correct_ans:
            score += 1
            st.success(f"{i+1}. kérdés: Helyes!")
        else:
            st.error(f"{i+1}. kérdés: Helytelen. A te válaszod: '{user_ans}'. A helyes válasz: '{correct_ans}'.")
    
    st.metric(label="Végső pontszám", value=f"{score} / {len(quiz_data)}")