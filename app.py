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

# --- STILI CSS CUSTOM (Per renderla bella come la versione React) ---
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
# Cerchiamo la chiave nei secrets di Streamlit (per il cloud) o input manuale
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

# --- FUNZIONI AI (IL CERVELLO) ---

def generate_lesson(grammar, topic, language, level):
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""
    Agisci come un docente di lingue esperto e coinvolgente.
    Crea una lezione di lingua personalizzata.
    
    Target:
    - Lingua di studio: {language}
    - Livello: {level}
    - Argomento Grammaticale: {grammar}
    - Interesse dello studente (Tema): {topic}
    
    Output richiesto (tutto in formato JSON valido):
    {{
        "title": "Titolo accattivante che unisce grammatica e tema",
        "theme": "{topic}",
        "grammarFocus": "{grammar}",
        "introduction": "Spiegazione chiara della regola grammaticale usando metafore legate al tema '{topic}'. (Max 100 parole)",
        "examples": ["3 frasi di esempio nella lingua target che usano la regola e parlano del tema"],
        "creativeActivity": "Un prompt per un esercizio di scrittura creativa breve. (es: 'Scrivi 3 righe su...')",
        "quiz": [
            {{
                "question": "Domanda a scelta multipla sulla regola",
                "options": ["Opzione A", "Opzione B", "Opzione C"],
                "correctAnswer": "L'opzione corretta esatta",
                "explanation": "Spiegazione breve del perché è corretta"
            }},
            {{
                "question": "Altra domanda...",
                "options": ["..."],
                "correctAnswer": "...",
                "explanation": "..."
            }},
             {{
                "question": "Terza domanda...",
                "options": ["..."],
                "correctAnswer": "...",
                "explanation": "..."
            }}
        ]
    }}
    Rispondi SOLO con il JSON.
    """
    
    try:
        response = model.generate_content(prompt)
        text_response = response.text.replace("```json", "").replace("```", "")
        data = json.loads(text_response)
        
        # Ricostruzione oggetti
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
        return None

def analyze_response(user_text, prompt_task, language):
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = f"""
    Sei un tutor. Lo studente doveva fare questo compito in {language}: "{prompt_task}".
    Ha scritto: "{user_text}".
    
    Analizza brevemente:
    1. Correzione (riscrivi la frase corretta se ci sono errori).
    2. Spiegazione grammaticale gentile.
    3. Incoraggiamento.
    """
    response = model.generate_content(prompt)
    return response.text

# --- INTERFACCIA UTENTE (STREAMLIT) ---

# Header
st.markdown("<div class='main-header'><h1>🧠 Grammatica<span class='highlight'>Geniale</span></h1><p>Il modo più smart per imparare le lingue.</p></div>", unsafe_allow_html=True)

if not api_key:
    st.stop() # Ferma tutto se non c'è la chiave

# Session State per mantenere i dati tra i refresh
if 'lesson' not in st.session_state:
    st.session_state.lesson = None
if 'quiz_submitted' not in st.session_state:
    st.session_state.quiz_submitted = False

# --- SEZIONE INPUT ---
if st.session_state.lesson is None:
    st.markdown("### ⚙️ Configura la tua lezione")
    
    col1, col2 = st.columns(2)
    with col1:
        lang = st.selectbox("Lingua da studiare", ["Inglese", "Spagnolo", "Francese", "Tedesco", "Italiano (per stranieri)"])
        level = st.select_slider("Il tuo livello", options=["A1", "A2", "B1", "B2", "C1"])
    
    with col2:
        grammar = st.text_input("Argomento Grammaticale", placeholder="es. Past Simple, Congiuntivo, Verbi Modali...")
        topic = st.text_input("Le tue passioni (Il tema)", placeholder="es. Calcio, Cucina, Harry Potter, Viaggi...")

    if st.button("✨ Genera Lezione Personalizzata", type="primary"):
        if grammar and topic:
            with st.spinner("L'AI sta preparando la lezione su misura per te..."):
                lesson_data = generate_lesson(grammar, topic, lang, level)
                if lesson_data:
                    st.session_state.lesson = lesson_data
                    st.session_state.lang = lang # Salviamo la lingua per dopo
                    st.rerun()
        else:
            st.warning("Inserisci sia la grammatica che un argomento!")

# --- SEZIONE LEZIONE ---
else:
    lesson = st.session_state.lesson
    
    # Pulsante Reset
    if st.button("🔄 Nuova Lezione"):
        st.session_state.lesson = None
        st.session_state.quiz_submitted = False
        st.rerun()

    st.markdown("---")
    
    # Hero Section
    st.markdown(f"## {lesson.title}")
    st.info(f"**Concetto Chiave:** {lesson.grammarFocus} applicato al mondo di: {lesson.theme}")
    st.write(lesson.introduction)
    
    # Esempi
    st.markdown("### 📖 Esempi nel contesto")
    for i, ex in enumerate(lesson.examples):
        st.markdown(f"> **{i+1}.** *{ex}*")
    
    st.markdown("---")

    # Attività Creativa
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

    # Quiz
    st.markdown("### 🧠 Quiz Finale")
    
    score = 0
    with st.form("quiz_form"):
        user_answers = {}
        for i, q in enumerate(lesson.quiz):
            st.markdown(f"**{i+1}. {q.question}**")
            user_answers[i] = st.radio(f"Opzioni per domanda {i+1}", q.options, key=f"q_{i}", label_visibility="collapsed")
            st.write("") # Spaziatura
            
        submitted = st.form_submit_button("Controlla Risposte")
        
        if submitted:
            st.session_state.quiz_submitted = True

    # Risultati Quiz
    if st.session_state.quiz_submitted:
        st.markdown("### Risultati")
        correct_count = 0
        for i, q in enumerate(lesson.quiz):
            user_choice = user_answers.get(i)
            if user_choice == q.correctAnswer:
                st.markdown(f"✅ **Domanda {i+1}:** Corretto!")
                correct_count += 1
            else:
                st.markdown(f"❌ **Domanda {i+1}:** Errato. La risposta giusta era: *{q.correctAnswer}*")
                st.caption(f"Spiegazione: {q.explanation}")
        
        final_score = (correct_count / len(lesson.quiz)) * 100
        if final_score == 100:
            st.balloons()
            st.success(f"Punteggio perfetto! {correct_count}/{len(lesson.quiz)}")
        else:
            st.info(f"Punteggio finale: {correct_count}/{len(lesson.quiz)}")