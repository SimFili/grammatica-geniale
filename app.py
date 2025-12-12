import streamlit as st
import google.generativeai as genai
import json
from dataclasses import dataclass
from typing import List

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(
    page_title="GrammaticaGeniale AI",
    page_icon="🧠",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- STILI CSS ---
st.markdown("""
    <style>
    .main-header {
        font-family: 'Helvetica Neue', sans-serif;
        color: #1e293b;
        text-align: center;
        padding: 2rem 0;
    }
    .highlight {
        color: #4f46e5;
        font-weight: bold;
    }
    .stButton>button {
        width: 100%;
        border-radius: 12px;
        height: 3em;
        font-weight: bold;
    }
    .success-box {
        padding: 15px;
        background-color: #f0fdf4;
        border: 1px solid #bbf7d0;
        border-radius: 10px;
        color: #166534;
        margin-top: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# --- CONFIGURAZIONE API ---
api_key = st.secrets.get("GOOGLE_API_KEY")

if not api_key:
    st.warning("⚠️ Manca la Google API Key nei secrets.")
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

def get_model():
    # Usiamo il modello Flash che è veloce e supportato
    return genai.GenerativeModel('gemini-1.5-flash')

def generate_lesson(grammar, topic, language, level):
    model = get_model()
    
    prompt = f"""
    Sei un docente di lingue esperto. Crea una lezione in JSON.
    
    Target:
    - Lingua: {language}
    - Livello: {level}
    - Grammatica: {grammar}
    - Tema: {topic}
    
    Rispondi ESCLUSIVAMENTE con un oggetto JSON valido con questa struttura esatta:
    {{
        "title": "Titolo lezione",
        "theme": "{topic}",
        "grammarFocus": "{grammar}",
        "introduction": "Spiegazione breve della regola",
        "examples": ["Esempio 1", "Esempio 2", "Esempio 3"],
        "creativeActivity": "Istruzioni per un esercizio di scrittura",
        "quiz": [
            {{
                "question": "Domanda 1",
                "options": ["Opzione A", "Opzione B", "Opzione C"],
                "correctAnswer": "Testo esatto opzione corretta",
                "explanation": "Perché è corretta"
            }},
             {{
                "question": "Domanda 2",
                "options": ["Opzione A", "Opzione B", "Opzione C"],
                "correctAnswer": "Testo esatto opzione corretta",
                "explanation": "Perché è corretta"
            }}
        ]
    }}
    """
    
    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        # Pulizia JSON se l'AI aggiunge markdown
        if text.startswith("```json"):
            text = text.replace("```json", "").replace("```", "")
        elif text.startswith("```"):
            text = text.replace("```", "")
            
        data = json.loads(text)
        
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
    model = get_model()
    prompt = f"""
    Sei un tutor.
    Compito in {language}: "{task}"
    Risposta studente: "{user_text}"
    
    Dammi un feedback breve: correzione (se serve), spiegazione e incoraggiamento.
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Errore analisi: {e}"

# --- APP STREAMLIT ---

st.markdown("<div class='main-header'><h1>🧠 Grammatica<span class='highlight'>Geniale</span></h1></div>", unsafe_allow_html=True)

# Inizializza session state
if 'lesson' not in st.session_state:
    st.session_state.lesson = None
if 'quiz_submitted' not in st.session_state:
    st.session_state.quiz_submitted = False
if 'lang' not in st.session_state:
    st.session_state.lang = "Italiano"

# Schermata Configurazione
if st.session_state.lesson is None:
    st.markdown("### ⚙️ Crea la tua lezione")
    
    c1, c2 = st.columns(2)
    with c1:
        lang = st.selectbox("Lingua", ["Inglese", "Spagnolo", "Francese", "Tedesco", "Italiano"])
        level = st.select_slider("Livello", ["A1", "A2", "B1", "B2", "C1"])
    with c2:
        grammar = st.text_input("Argomento Grammaticale", placeholder="es. Passato prossimo")
        topic = st.text_input("Le tue passioni", placeholder="es. Calcio, Musica")

    if st.button("✨ Genera Lezione", type="primary"):
        if grammar and topic:
            with st.spinner("Creazione lezione in corso..."):
                res = generate_lesson(grammar, topic, lang, level)
                if res:
                    st.session_state.lesson = res
                    st.session_state.lang = lang
                    st.rerun()
        else:
            st.warning("Compila tutti i campi!")

# Schermata Lezione
else:
    lesson = st.session_state.lesson
    
    if st.button("🔄 Ricomincia"):
        st.session_state.lesson = None
        st.session_state.quiz_submitted = False
        st.rerun()

    st.markdown("---")
    st.title(lesson.title)
    st.info(f"**Tema:** {lesson.theme} | **Grammatica:** {lesson.grammarFocus}")
    st.write(lesson.introduction)
    
    st.subheader("📖 Esempi")
    for ex in lesson.examples:
        st.markdown(f"- *{ex}*")
        
    st.markdown("---")
    
    st.subheader("✍️ Esercizio Creativo")
    st.write(f"**Task:** {lesson.creativeActivity}")
    user_txt = st.text_area("La tua risposta:", height=100)
    
    if st.button("Correggi Esercizio"):
        if user_txt:
            with st.spinner("Analisi..."):
                feedback = analyze_response(user_txt, lesson.creativeActivity, st.session_state.lang)
                st.markdown(f"<div class='success-box'>{feedback}</div>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.subheader("🧠 Quiz")
    with st.form("quiz"):
        answers = {}
        for i, q in enumerate(lesson.quiz):
            st.markdown(f"**{i+1}. {q.question}**")
            answers[i] = st.radio(f"Domanda {i}", q.options, label_visibility="collapsed", key=f"q{i}")
            st.write("")
        
        if st.form_submit_button("Verifica Quiz"):
            st.session_state.quiz_submitted = True

    if st.session_state.quiz_submitted:
        score = 0
        for i, q in enumerate(lesson.quiz):
            user_ans = answers.get(i)
            if user_ans == q.correctAnswer:
                score += 1
                st.success(f"✅ {i+1} Corretta!")
            else:
                st.error(f"❌ {i+1} Errata. Risposta giusta: {q.correctAnswer}")
                st.caption(q.explanation)
        st.metric("Punteggio Finale", f"{score}/{len(lesson.quiz)}")
