import streamlit as st
import google.generativeai as genai
import json
from dataclasses import dataclass
from typing import List

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="GrammaticaGeniale AI", page_icon="🧠", layout="centered")

st.markdown("""
    <style>
    .main-header {text-align: center; padding: 2rem 0; color: #1e293b;}
    .stButton>button {width: 100%; border-radius: 12px; height: 3em; font-weight: bold;}
    .success-box {padding: 15px; background-color: #f0fdf4; border-radius: 10px; border: 1px solid #bbf7d0; color: #166534;}
    </style>
""", unsafe_allow_html=True)

# --- API KEY ---
api_key = st.secrets.get("GOOGLE_API_KEY")
if not api_key:
    st.error("⚠️ API Key mancante. Inseriscila nei 'Secrets' di Streamlit.")
    st.stop()

genai.configure(api_key=api_key)

# --- MODELLO DATI ---
@dataclass
class QuizQuestion:
    question: str
    options: List[str]
    correctAnswer: str
    explanation: str

@dataclass
class LessonContent:
    title: str
    theme: str
    grammarFocus: str
    introduction: str
    examples: List[str]
    creativeActivity: str
    quiz: List[QuizQuestion]

# --- FUNZIONI AI ---

def clean_json(text):
    # Pulisce la risposta dell'AI per trovare solo il JSON
    text = text.strip()
    start = text.find('{')
    end = text.rfind('}') + 1
    if start != -1 and end != -1:
        return text[start:end]
    return text

def generate_lesson(grammar, topic, language, level):
    # USIAMO GEMINI PRO: Il modello più stabile
    model = genai.GenerativeModel('gemini-pro')
    
    prompt = f"""
    Sei un docente di lingue. Crea una lezione strutturata.
    
    Dati:
    - Lingua: {language}
    - Livello: {level}
    - Grammatica: {grammar}
    - Tema: {topic}
    
    OUTPUT: Devi rispondere SOLO con un JSON valido.
    Struttura JSON:
    {{
        "title": "Titolo lezione",
        "theme": "{topic}",
        "grammarFocus": "{grammar}",
        "introduction": "Spiegazione regola (max 2 frasi)",
        "examples": ["Frase 1", "Frase 2", "Frase 3"],
        "creativeActivity": "Task scrittura breve",
        "quiz": [
            {{
                "question": "Domanda 1",
                "options": ["A", "B", "C"],
                "correctAnswer": "Testo A",
                "explanation": "Motivo"
            }},
             {{
                "question": "Domanda 2",
                "options": ["A", "B", "C"],
                "correctAnswer": "Testo B",
                "explanation": "Motivo"
            }}
        ]
    }}
    """
    
    try:
        response = model.generate_content(prompt)
        json_str = clean_json(response.text)
        data = json.loads(json_str)
        
        quiz_list = [QuizQuestion(**q) for q in data['quiz']]
        return LessonContent(
            title=data['title'],
            theme=data['theme'],
            grammarFocus=data['grammarFocus'],
            introduction=data['introduction'],
            examples=data['examples'],
            creativeActivity=data['creativeActivity'],
            quiz=quiz_list
        )
    except Exception as e:
        st.error(f"Errore generazione: {e}")
        return None

def analyze_response(user_text, task, language):
    model = genai.GenerativeModel('gemini-pro')
    prompt = f"Sei un tutor. Compito in {language}: '{task}'. Studente: '{user_text}'. Dai feedback breve."
    try:
        return model.generate_content(prompt).text
    except:
        return "Errore connessione tutor."

# --- INTERFACCIA ---
st.markdown("<div class='main-header'><h1>🧠 Grammatica Geniale</h1></div>", unsafe_allow_html=True)

if 'lesson' not in st.session_state: st.session_state.lesson = None
if 'quiz_submitted' not in st.session_state: st.session_state.quiz_submitted = False

if st.session_state.lesson is None:
    c1, c2 = st.columns(2)
    with c1:
        lang = st.selectbox("Lingua", ["Inglese", "Spagnolo", "Francese", "Tedesco"])
        level = st.select_slider("Livello", ["A1", "A2", "B1", "B2"])
    with c2:
        grammar = st.text_input("Grammatica", placeholder="es. Present Perfect")
        topic = st.text_input("Passione", placeholder="es. Calcio")

    if st.button("Genera Lezione", type="primary"):
        if grammar and topic:
            with st.spinner("Creo la lezione..."):
                res = generate_lesson(grammar, topic, lang, level)
                if res:
                    st.session_state.lesson = res
                    st.session_state.lang = lang
                    st.rerun()
else:
    lesson = st.session_state.lesson
    if st.button("🔄 Nuova Lezione"):
        st.session_state.lesson = None
        st.session_state.quiz_submitted = False
        st.rerun()

    st.header(lesson.title)
    st.info(f"{lesson.introduction}")
    
    st.subheader("Esempi")
    for ex in lesson.examples: st.write(f"- {ex}")
    
    st.markdown("---")
    st.subheader("Esercizio")
    st.write(lesson.creativeActivity)
    user_txt = st.text_area("Tua risposta:")
    if st.button("Correggi") and user_txt:
        fb = analyze_response(user_txt, lesson.creativeActivity, st.session_state.lang)
        st.success(fb)
    
    st.markdown("---")
    st.subheader("Quiz")
    with st.form("quiz"):
        ans = {}
        for i, q in enumerate(lesson.quiz):
            ans[i] = st.radio(q.question, q.options, key=i)
        if st.form_submit_button("Verifica"):
            st.session_state.quiz_submitted = True
            
    if st.session_state.quiz_submitted:
        score = 0
        for i, q in enumerate(lesson.quiz):
            if ans[i] == q.correctAnswer:
                score += 1
                st.success(f"Domanda {i+1}: Giusta!")
            else:
                st.error(f"Domanda {i+1}: Sbagliata. Era: {q.correctAnswer}")
