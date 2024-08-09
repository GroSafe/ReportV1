import logging

# Enable logging
logging.basicConfig(level=logging.DEBUG)

import streamlit as st
import tempfile
import csv
import os
import pandas as pd
from google.cloud import translate_v2 as translate
from google.cloud import speech
from streamlit_webrtc import webrtc_streamer, AudioProcessorBase
import numpy as np
import av

# Initialize Google Cloud clients
logging.debug("Initializing Google Cloud clients...")
translate_client = translate.Client()
speech_client = speech.SpeechClient()

# Function to translate text
def translate_text(text, target_language='en'):
    result = translate_client.translate(text, target_language=target_language)
    return result['translatedText']

# Custom audio processor class
class AudioProcessor(AudioProcessorBase):
    def __init__(self):
        self.recording = []
        self.sampling_rate = 16000  # Set to 16kHz for Google Speech API
        logging.debug("AudioProcessor initialized.")

    def recv(self, frame: av.AudioFrame) -> av.AudioFrame:
        audio = frame.to_ndarray()
        self.recording.append(audio)
        return frame

    def get_wav_bytes(self):
        audio_data = np.concatenate(self.recording, axis=1)
        logging.debug(f"Captured {len(audio_data)} bytes of audio.")
        return audio_data.tobytes()

# Function to save data to CSV
def save_to_csv(transcript, translated_text, filename="reports.csv"):
    file_exists = os.path.isfile(filename)

    with open(filename, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        
        # Write the header if the file is new
        if not file_exists:
            writer.writerow(["Transcription", "Translated Text"])
        
        # Write the data
        writer.writerow([transcript, translated_text])

    st.success(f"Data saved to {filename}")

# Streamlit app UI
logging.debug("Starting Streamlit app...")
st.title("Real-Time Speech-to-Text and Translation")

# Record audio using the webrtc_streamer component
webrtc_ctx = webrtc_streamer(key="speech", audio_processor_factory=AudioProcessor, media_stream_constraints={"audio": True, "video": False})

# Text input for language selection
target_language = st.selectbox("Select target language", ["en", "es", "fr", "de", "zh", "ja"])

if webrtc_ctx.audio_processor:
    if st.button("Process Audio"):
        logging.debug("Processing audio...")
        with tempfile.NamedTemporaryFile(suffix=".wav") as f:
            f.write(webrtc_ctx.audio_processor.get_wav_bytes())
            f.flush()

            with open(f.name, "rb") as audio_file:
                content = audio_file.read()

            # Google Speech-to-Text API
            audio = speech.RecognitionAudio(content=content)
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=16000,
                language_code="en-US",  # Change this based on your desired input language
            )

            response = speech_client.recognize(config=config, audio=audio)
            if response.results:
                transcript = response.results[0].alternatives[0].transcript
                st.write("Transcription:", transcript)

                # Translate the text
                translated_text = translate_text(transcript, target_language=target_language)
                st.write("Translated Text:", translated_text)

                # Save to CSV
                save_to_csv(transcript, translated_text)
                logging.debug("Saved transcript and translation to CSV.")
            else:
                st.write("No transcription found.")

# Add a button to download the CSV file
if os.path.isfile("reports.csv"):
    df = pd.read_csv("reports.csv")
    st.download_button(
        label="Download Reports CSV",
        data=df.to_csv(index=False),
        file_name="reports.csv",
        mime="text/csv",
    )

logging.debug("Streamlit app finished loading.")
