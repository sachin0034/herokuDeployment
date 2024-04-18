import os
from dotenv import load_dotenv
import openai
from deepgram import Deepgram
from flask import Flask, request
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse

# Load API keys
load_dotenv()

# Twilio account credentials
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

# OpenAI and Deepgram API keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")

# Initialize APIs
client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
openai.api_key = OPENAI_API_KEY
deepgram = Deepgram(DEEPGRAM_API_KEY)

app = Flask(__name__)

@app.route('/incoming', methods=['POST'])
def handle_incoming_call():
    """
    Handle the incoming call and respond with a TwiML response.
    """
    response = VoiceResponse()
    response.say("Hello, welcome to the ChatGPT phone service. Please say your message.")
    response.record(
        action="/transcribe",
        method="POST",
        timeout=10,
        trim="detect-silence"
    )
    return str(response)

@app.route('/transcribe', methods=['POST'])
async def transcribe_message():
    """
    Transcribe the user's recorded message using Deepgram and generate a response using ChatGPT.
    """
    # Retrieve the recorded audio file
    recording_url = request.form['RecordingUrl']

    # Transcribe the audio using Deepgram
    transcription = await transcribe(recording_url)

    # Pass the transcription to ChatGPT and get the response
    chatgpt_response = await request_gpt(transcription)

    # Convert the ChatGPT response to speech and play it back to the user
    play_response_audio(chatgpt_response)

    return "Transcription completed."

async def transcribe(recording_url):
    """
    Transcribe audio using Deepgram API.

    Args:
        - recording_url: The URL of the recorded audio file.

    Returns:
        The transcription of the audio.
    """
    source = {'url': recording_url}
    response = await deepgram.transcription.prerecorded(source)
    return response["results"]["channels"][0]["alternatives"][0]["transcript"]

async def request_gpt(prompt):
    """
    Send a prompt to the ChatGPT API and return the response.

    Args:
        - prompt: The prompt to send to the API.

    Returns:
        The response from the API.
    """
    response = await openai.Completion.acreate(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=1024,
        n=1,
        stop=None,
        temperature=0.7,
    )
    return response.choices[0].text.strip()

def play_response_audio(response_text):
    """
    Convert the ChatGPT response text to speech and play it back to the user.
    """
    # Convert the response text to speech using OpenAI's TTS
    response_stream = openai.Audio.create(
        model="whisper-1",
        prompt=response_text,
        response_format="mp3",
        temperature=0.5,
    )
    with open("response.mp3", "wb") as f:
        f.write(response_stream.audio_stream.read())

    # Play the response audio back to the user
    response = VoiceResponse()
    response.play("response.mp3")
    return str(response)

if __name__ == '__main__':
    app.run()