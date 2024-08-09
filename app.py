import streamlit as st
from google.cloud import translate_v2 as translate
from google.cloud import speech
import io

# Set up Google Cloud Translate API
def translate_text(text, target_language='en'):
    translate_client = translate.Client()
    result = translate_client.translate(text, target_language=target_language)
    return result['translatedText']

# Set up Google Cloud Speech-to-Text API
def transcribe_speech(audio_file, language_code='en-US'):
    client = speech.SpeechClient()

    with io.open(audio_file, "rb") as audio:
        content = audio.read()

    audio = speech.RecognitionAudio(content=content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code=language_code,
    )

    response = client.recognize(config=config, audio=audio)

    # Return the first transcription result
    for result in response.results:
        return result.alternatives[0].transcript

# Streamlit UI
st.title("Multilingual Form with Speech-to-Text and Translation")

# Upload audio file for speech-to-text
uploaded_file = st.file_uploader("Upload an audio file for speech-to-text", type=["wav", "mp3"])

if uploaded_file is not None:
    # Transcribe the uploaded audio file
    st.write("Transcribing audio...")
    transcription = transcribe_speech(uploaded_file)
    st.write("Transcription:", transcription)

# Text input
input_text = st.text_input("Enter text to translate")

# Language selection
target_language = st.selectbox("Select target language", ["en", "es", "fr", "de", "zh", "ja"])

if st.button("Translate"):
    if input_text:
        translated_text = translate_text(input_text, target_language=target_language)
        st.write("Translated Text:", translated_text)
    else:
        st.error("Please enter text to translate.")

