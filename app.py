import streamlit as st
import os
import json
from google import genai
from google.genai import types

# Téma és UI finomhangolás (Futurisztikus/Minimalista)
st.set_page_config(page_title="PDF Kvíz Generátor", layout="centered")
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
client = genai.Client(api_key=api_key)

@st.cache_resource
def upload_pdf_to_gemini(file_path):
    return client.files.upload(file=file_path)

@st.cache_data
def generate_quiz_data(_document):
    prompt = """
    Generálj 5 feleletválasztós kérdést a megadott dokumentum alapján magyar nyelven. 
    Kizárólag egy JSON tömböt adj vissza, amely objektumokat tartalmaz a következő kulcsokkal: 
    'question' (sztring), 'options' (4 sztringből álló tömb), és 'answer' (sztring, amelynek pontosan meg kell egyeznie az egyik opcióval).
    """
    
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=[
            _document,
            prompt
        ],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
        ),
    )
    return json.loads(response.text)

PDF_FILE_PATH = "document.pdf" 

if not os.path.exists(PDF_FILE_PATH):
    st.error(f"A(z) {PDF_FILE_PATH} fájl nem található.")
    st.stop()

st.title("Dinamikus Kvíz")

with st.spinner("Dokumentum feldolgozása..."):
    pdf_ref = upload_pdf_to_gemini(PDF_FILE_PATH)

with st.spinner("Kérdések generálása..."):
    quiz_data = generate_quiz_data(pdf_ref)

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
            st.success(f"{i+1. kérdés}: Helyes!")
        else:
            st.error(f"{i+1. kérdés}: Helytelen. A te válaszod: '{user_ans}'. A helyes válasz: '{correct_ans}'.")
    
    st.metric(label="Végső pontszám", value=f"{score} / {len(quiz_data)}")