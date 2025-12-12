import streamlit as st
import google.generativeai as genai
import json
from dataclasses import dataclass
from typing import List, Optional

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(
    page_title="GrammaticaGeniale AI",
    page_icon="🧠",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- STILI CSS CUSTOM ---
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
    .topic-box {
        background-color: #f8fafc;
        padding: 20px;
        border-radius: 15px;
        border: 1px solid #e2e8f0;
        margin-bottom: 20px;
    }
    .success-box {
        padding: 15px;
        border-radius: 10px;
        background-color: #f0fdf4;
        border: 1px solid #bbf7d0;
        color: #166534;
    }
    </style>
""", unsafe_allow_html=True)

# --- CONFIGURAZIONE API ---
api_key = st.secrets.get("GOOGLE_API_KEY")

if not api_key:
    st.warning("⚠️ Per iniziare, serve la tua API Key di Google.")
    api_key = st.text_input("Incolla qui la tua Google API Key (inizia con AIza...)", type="password")

if api_key:
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

def generate_lesson(grammar, topic, language, level):
    # CORREZIONE: Usiamo il modello Flash, più stabile e veloce per l'API gratuita
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""
    Agisci come un docente di lingue esperto.
    Crea una lezione di lingua personalizzata.
    
    Target:
    - Lingua di studio: {language}
    - Livello: {level}
    - Argomento Grammaticale: {grammar}
    - Interesse dello studente (Tema): {topic}
    
    Output richiesto (tutto in formato JSON valido, SENZA markdown ```json):
    {{
        "title": "Titolo accattivante",
        "theme": "{topic}",
        "grammarFocus": "{grammar}",
        "introduction": "Spiegazione regola (max 100 parole)",
        "examples": ["Frase 1", "Frase 2", "Frase 3"],
        "creativeActivity": "Prompt esercizio scrittura",
        "quiz": [
            {{
                "question": "Domanda 1",
                "options": ["A", "B", "C"],
                "correctAnswer": "Opzione corretta esatta",
                "explanation": "Spiegazione"
            }},
            {{
                "question": "Domanda 2",
                "options": ["A", "B", "C"],
                "correctAnswer": "Opzione corretta esatta",
                "explanation": "Spiegazione"
            }},
             {{
                "question": "Domanda 3",
                "options": ["A", "B", "C"],
                "correctAnswer": "Opzione corretta esatta",
                "explanation": "Spiegazione"
            }}
        ]
    }}
    """
    
    try:
        response = model.generate_content(prompt)
        # Pulizia extra nel caso l'AI metta comunque i backticks
        text_response = response.text.strip()
        if text_response.startswith("```json"):
            text_response = text_response.replace("```json", "").replace("```", "")
        elif text_response.startswith("```"):
            text_response = text_response.replace("```", "")
            
        data = json.loads(text_response)
        
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
        st.error(f"Errore nella generazione: {e}")
        st.error("Dettagli risposta AI (per debug): " + response.text if 'response' in locals() else "Nessuna risposta")
        return None

def analyze_response(user_text, prompt_task, language):
    # CORREZIONE: Anche qui usiamo il modello Flash con le virgolette singole corrette
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""
    Sei un tutor. Compito in {language}: "{prompt_task}".
    Risposta studente: "{user_text}".
    
    Analizza brevemente:
    1. Correzione (se necessaria).
    2. Spiegazione grammaticale.
    3. Incoraggiamento.
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Errore nell'analisi: {e}"

# --- INTERFACCIA STREAMLIT ---

st.markdown("<div class='main-header'><h1>🧠 Grammatica<span class='highlight'>Geniale</span></h1><p>Il modo più smart per imparare le lingue.</p></div>", unsafe_allow_html=True)

if not api_key:
    st.stop()

if 'lesson' not in st.session_state:
    st.session_state.lesson = None
if 'quiz_submitted' not in st.session_state:
    st.session_state.quiz_submitted = False
if 'lang' not in st.session_state:
    st.session_state.lang = "Italiano"

# --- SEZIONE INPUT ---
if st.session_state.lesson is None:
    st.markdown("### ⚙️ Configura la tua lezione")
    
    col1, col2 = st.columns(2)
    with col1:
        lang = st.selectbox("Lingua da studiare", ["Inglese", "Spagnolo", "Francese", "Tedesco", "Italiano (per stranieri)"])
        level = st.select_slider("Il tuo livello", options=["A1", "A2", "B1", "B2", "C1"])
    
    with col2:
        grammar = st.text_input("Argomento Grammaticale", placeholder="es. Past Simple, Congiuntivo...")
        topic = st.text_input("Le tue passioni (Il tema)", placeholder="es. Calcio, Cucina, Viaggi...")

    if st.button("✨ Genera Lezione Personalizzata", type="primary"):
        if grammar and topic:
            with st.spinner("L'AI sta preparando la lezione su misura per te..."):
                lesson_data = generate_lesson(grammar, topic, lang, level)
                if lesson_data:
                    st.session_state.lesson = lesson_data
                    st.session_state.lang = lang
                    st.rerun()
        else:
            st.warning("Inserisci sia la grammatica che un argomento!")

# --- SEZIONE LEZIONE ---
else:
    lesson = st.session_state.lesson
    
    if st.button("🔄 Nuova Lezione"):
        st.session_state.lesson = None
        st.session_state.quiz_submitted = False
        st.rerun()

    st.markdown("---")
    st.markdown(f"## {lesson.title}")
    st.info(f"**Focus:** {lesson.grammarFocus} | **Tema:** {lesson.theme}")
    st.write(lesson.introduction)
    
    st.markdown("### 📖 Esempi")
    for i, ex in enumerate(lesson.examples):
        st.markdown(f"> **{i+1}.** *{ex}*")
    
    st.markdown("---")

    st.markdown("### ✍️ Attività Creativa")
    st.markdown(f"**Task:** {lesson.creativeActivity}")
    user_input = st.text_area("Scrivi qui la tua risposta...", height=100)
    
    if st.button("Invia al Tutor AI"):
        if user_input:
            with st.spinner("Il tutor sta correggendo..."):
                feedback = analyze_response(user_input, lesson.creativeActivity, st.session_state.lang)
                st.success("Ecco il feedback!")
                st.markdown(feedback)
        else:
            st.warning("Scrivi qualcosa prima di inviare!")

    st.markdown("---")

    st.markdown("### 🧠 Quiz Finale")
    score = 0
    with st.form("quiz_form"):
        user_answers = {}
        for i, q in enumerate(lesson.quiz):
            st.markdown(f"**{i+1}. {q.question}**")
            user_answers[i] = st.radio(f"Scegli:", q.options, key=f"q_{i}", label_visibility="collapsed")
            st.write("")
            
        submitted = st.form_submit_button("Controlla Risposte")
        if submitted:
            st.session_state.quiz_submitted = True

    if st.session_state.quiz_submitted:
        st.markdown("### Risultati")
        correct_count = 0
        for i, q in enumerate(lesson.quiz):
            user_choice = user_answers.get(i)
            if user_choice == q.correctAnswer:
                st.success(f"✅ Domanda {i+1}: Corretto!")
                correct_count += 1
            else:
                st.error(f"❌ Domanda {i+1}: Errato. Risposta: {q.correctAnswer}")
                st.caption(f"Spiegazione: {q.explanation}")
        
        st.info(f"Punteggio finale: {correct_count}/{len(lesson.quiz)}")
