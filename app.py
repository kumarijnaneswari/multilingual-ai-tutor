import streamlit as st
import ollama
from deep_translator import GoogleTranslator
from gtts import gTTS
import speech_recognition as sr
import tempfile
from langdetect import detect

st.set_page_config(page_title="Multilingual AI Tutor", page_icon="🤖", layout="wide")

# ---------------- SIDEBAR DASHBOARD ----------------

st.sidebar.title("⚙️ Tutor Dashboard")

mode = st.sidebar.selectbox(
    "Select Mode",
    ["Tutor Mode", "Quiz Mode"]
)

language = st.sidebar.selectbox(
    "Select Language",
    ["Auto Detect", "English", "Telugu", "Hindi"]
)

voice_output = st.sidebar.checkbox("Enable Voice Answer", value=True)

lang_code = {
    "English": "en",
    "Telugu": "te",
    "Hindi": "hi"
}

# ---------------- CHAT SESSIONS ----------------

if "chats" not in st.session_state:
    st.session_state.chats = {"Chat 1": []}

if "current_chat" not in st.session_state:
    st.session_state.current_chat = "Chat 1"

if st.sidebar.button("➕ New Chat"):
    new_chat = f"Chat {len(st.session_state.chats)+1}"
    st.session_state.chats[new_chat] = []
    st.session_state.current_chat = new_chat

selected_chat = st.sidebar.radio(
    "📜 Chat History",
    list(st.session_state.chats.keys()),
    index=list(st.session_state.chats.keys()).index(st.session_state.current_chat)
)

st.session_state.current_chat = selected_chat
messages = st.session_state.chats[selected_chat]

# ---------------- LEARNING MEMORY ----------------

if "learning_topics" not in st.session_state:
    st.session_state.learning_topics = []

st.sidebar.markdown("---")
st.sidebar.subheader("🧠 Learning Memory")

for topic in st.session_state.learning_topics[-5:]:
    st.sidebar.write("•", topic[:40])

# ---------------- MAIN TITLE ----------------

st.title("🤖 Multilingual AI Tutor")
st.write("Ask questions using text or voice.")

# ---------------- DISPLAY CHAT ----------------

for msg in messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ---------------- VOICE INPUT ----------------

def listen_voice():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        st.info("🎤 Listening...")
        audio = r.listen(source)

    try:
        text = r.recognize_google(audio)
        return text
    except:
        return "Sorry, I could not understand."

if st.sidebar.button("🎤 Speak Question"):
    prompt = listen_voice()
    st.success(f"You said: {prompt}")
else:
    prompt = st.chat_input("Type your question...")

# ---------------- PROCESS QUESTION ----------------

if prompt:

    with st.chat_message("user"):
        st.markdown(prompt)

    messages.append({"role": "user", "content": prompt})

    # Language detection
    if language == "Auto Detect":
        try:
            detected_lang = detect(prompt)
        except:
            detected_lang = "en"
    else:
        detected_lang = lang_code[language]

    # Translate question to English
    if detected_lang != "en":
        translated_question = GoogleTranslator(
            source=detected_lang,
            target="en"
        ).translate(prompt)
    else:
        translated_question = prompt

    # ---------------- SYSTEM PROMPT ----------------

    if mode == "Tutor Mode":

        system_prompt = f"""
        You are a helpful tutor.
        Give short answers in 3 to 5 sentences.

        Previously learned topics:
        {st.session_state.learning_topics}

        Occasionally ask a small follow-up question.
        """

    else:

        system_prompt = f"""
        You are a teacher giving quizzes.

        Previously learned topics:
        {st.session_state.learning_topics}

        Ask quiz questions related to these topics.
        """

    # ---------------- AI RESPONSE ----------------

    with st.chat_message("assistant"):

        response = ollama.chat(
            model="phi3:mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": translated_question}
            ],
            options={"num_predict": 150}
        )

        answer = response["message"]["content"]

        # Translate answer back
        if detected_lang != "en":
            answer = GoogleTranslator(
                source="en",
                target=detected_lang
            ).translate(answer)

        st.markdown(answer)

        # Voice output
        if voice_output:
            tts = gTTS(text=answer, lang=detected_lang)
            tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
            tts.save(tmp_file.name)
            st.audio(tmp_file.name)

    messages.append({"role": "assistant", "content": answer})

    # Save topic to memory
    if translated_question not in st.session_state.learning_topics:
        st.session_state.learning_topics.append(translated_question)
