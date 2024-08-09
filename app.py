from flask import Flask, render_template, request, send_file
from google.cloud import translate_v2 as translate
from google.cloud import texttospeech
from google.cloud import speech
import tempfile
import os

app = Flask(__name__)

# Initialize Google Cloud clients
translate_client = translate.Client()
tts_client = texttospeech.TextToSpeechClient()
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
    synthesis_input = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(
        language_code=lang, ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )

    response = tts_client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )

    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio_file:
        temp_audio_file.write(response.audio_content)
        return temp_audio_file.name

@app.route('/', methods=['GET', 'POST'])
def report():
    if request.method == 'POST':
        report_types = request.form.getlist('report_types')
        confidence_level = request.form['confidence_level']
        platform = request.form['platform']
        times = request.form['times']
        frequency = request.form['frequency']
        free_text = request.form['free_text']
        submit_anonymous = request.form.get('submit_anonymous')

        # Speech-to-text processing
        if 'audio_file' in request.files:
            audio_file = request.files['audio_file']
            if audio_file.filename != '':
                audio_content = audio_file.read()
                transcription = speech_to_text(audio_content)
                free_text = transcription

        # Translation processing
        target_language = request.form['target_language']
        translated_report = translate_text(free_text, target_language)

        # Text-to-speech conversion
        audio_path = text_to_speech(translated_report, lang=target_language)
        return send_file(audio_path, as_attachment=True, download_name="translated_report.mp3")

    return render_template('report.html')

if __name__ == '__main__':
    app.run(debug=True)
