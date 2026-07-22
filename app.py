import streamlit as st
import tempfile
import os
from pathlib import Path

from src.transcript import fetch_transcript, save_transcript, load_transcript, Transcript
from src.chunking import chunk_transcript
from src.qa_engine import QAEngine
from src.memory import ConversationMemory
from src.voice import speech_to_text, text_to_speech
from src.utils import DATA_DIR

st.set_page_config(
    page_title="Video Tutor Agent",
    page_icon="🎓",
    layout="wide",
)

st.title("🎓 Video Tutor Agent")
st.caption("Paste a YouTube link, get answers grounded in the video transcript.")

if "memory" not in st.session_state:
    st.session_state.memory = ConversationMemory()
if "transcript" not in st.session_state:
    st.session_state.transcript = None
if "qa_engine" not in st.session_state:
    st.session_state.qa_engine = None
if "video_url" not in st.session_state:
    st.session_state.video_url = ""

with st.sidebar:
    st.header("Settings")
    enable_tts = st.toggle("Enable voice output (TTS)", value=False)
    enable_stt = st.toggle("Enable voice input (STT)", value=False)
    if st.button("Clear conversation"):
        st.session_state.memory.clear()
        st.rerun()

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Video Input")
    video_url = st.text_input(
        "YouTube URL",
        placeholder="https://www.youtube.com/watch?v=...",
        value=st.session_state.video_url,
    )

    if st.button("Load Video", type="primary", disabled=not video_url):
        st.session_state.video_url = video_url
        with st.spinner("Fetching transcript..."):
            try:
                transcript = fetch_transcript(video_url)
                st.session_state.transcript = transcript
                chunks = chunk_transcript(transcript)
                st.session_state.qa_engine = QAEngine(transcript, chunks)
                st.session_state.memory.clear()
                save_transcript(transcript)
                st.success(f"Loaded! Language: {transcript.language}, Segments: {len(transcript.segments)}")
            except Exception as e:
                st.error(f"Error: {e}")

    if st.session_state.transcript:
        t = st.session_state.transcript
        st.info(f"**Language:** {t.language}\n**Segments:** {len(t.segments)}")

        with st.expander("View Transcript"):
            for seg in t.segments[:50]:
                st.text(f"[{seg.timestamp}] {seg.text}")
            if len(t.segments) > 50:
                st.text(f"... and {len(t.segments) - 50} more segments")

with col2:
    st.subheader("Chat")

    for turn in st.session_state.memory.get_history():
        with st.chat_message(turn["role"]):
            st.markdown(turn["content"])

    user_input = None

    if enable_stt:
        st.markdown("---")
        audio_bytes = st.audio_input("Ask a question by voice")
        if audio_bytes:
            with st.spinner("Transcribing..."):
                user_input = speech_to_text(audio_bytes)
                st.write(f"You said: {user_input}")

    text_input = st.chat_input("Ask a question about the video...")
    if text_input:
        user_input = text_input

    if user_input:
        if not st.session_state.qa_engine:
            st.warning("Please load a video first!")
        else:
            st.session_state.memory.add_user_message(user_input)

            with st.chat_message("user"):
                st.markdown(user_input)

            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    response = st.session_state.qa_engine.answer(
                        user_input,
                        conversation_history=st.session_state.memory.get_history(),
                    )
                    st.markdown(response.answer)

                    if response.sources:
                        st.caption(f"Sources: {', '.join(response.sources)}")

                    if enable_tts:
                        with st.spinner("Generating audio..."):
                            tts_bytes = text_to_speech(response.answer)
                            if tts_bytes:
                                st.audio(tts_bytes, format="audio/wav")

            st.session_state.memory.add_assistant_message(
                response.answer,
                timestamp_cited=", ".join(response.sources),
            )
