import streamlit as st
from google.cloud import translate_v2 as translate
from google.cloud import speech
from gtts import gTTS
import tempfile
import os
import base64
from io import BytesIO

# Initialize Google Cloud clients
translate_client = translate.Client()
speech_client = speech.SpeechClient()

# Helper functions
def translate_text(text, target_language='en'):
    result = translate_client.translate(text, target_language=target_language)
    return result['translatedText']

def speech_to_text(audio_content):
    audio = speech.RecognitionAudio(content=audio_content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code="en-US",
    )
    response = speech_client.recognize(config=config, audio=audio)
    return response.results[0].alternatives[0].transcript if response.results else ""

def text_to_speech(text, lang='en'):
    tts = gTTS(text=text, lang=lang)
    tts.save("output.mp3")
    with open("output.mp3", "rb") as audio_file:
        audio_bytes = audio_file.read()
    return audio_bytes

# App UI
st.title("Incident Reporting System")

st.header("Select Report Types")
report_types = st.multiselect(
    "Choose the types of incidents you want to report:",
    ["Suspicious Behavior", "Illegal Content", "Request to Move to Private Channel"]
)

confidence_level = st.slider("Confidence Level:", 0, 100, 50)

st.header("Additional Information")
platform = st.text_input("Platform (e.g., Website, App)")
times = st.text_input("Times (e.g., Specific hours)")
frequency = st.text_input("Frequency (e.g., Daily, Weekly)")

st.header("Details")
free_text = st.text_area("Provide additional details")

# Speech-to-text for free text field
if st.button("Use Speech-to-Text"):
    uploaded_file = st.file_uploader("Upload audio file (WAV format)", type="wav")
    if uploaded_file:
        audio_content = uploaded_file.read()
        transcription = speech_to_text(audio_content)
        st.write("Transcribed Text:")
        st.write(transcription)
        free_text = transcription

# Language Translation
st.header("Translation")
target_language = st.selectbox("Translate to language", ["en", "es", "fr", "de", "zh", "ja"])

if st.button("Translate Report"):
    translated_report = translate_text(free_text, target_language)
    st.write("Translated Report:")
    st.write(translated_report)

    # Text-to-Speech for the translated report
    st.audio(text_to_speech(translated_report, lang=target_language))

# Option to submit anonymously or with details
submit_anonymous = st.checkbox("Submit Anonymously")

if submit_anonymous:
    st.success("You have chosen to submit anonymously.")
else:
    user_details = st.text_input("Please provide your contact details (optional)")

# Submit Button
if st.button("Submit Report"):
    st.write("Your report has been submitted with the following details:")
    st.write(f"Report Types: {', '.join(report_types)}")
    st.write(f"Confidence Level: {confidence_level}")
    st.write(f"Platform: {platform}")
    st.write(f"Times: {times}")
    st.write(f"Frequency: {frequency}")
    st.write(f"Details: {free_text}")
    if not submit_anonymous:
        st.write(f"User Details: {user_details}")

    st.success("Thank you for your report!")
