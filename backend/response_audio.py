# Import necessary libraries
import os
from dotenv import load_dotenv
import requests
import subprocess
import logging
import tempfile
import pyaudio
import wave

# Load environment variables from .env file
load_dotenv("config/.env")

# Get GOOGLE_APPLICATION_CREDENTIALS from .env file
google_app_creds = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

# Import Google Cloud text-to-speech
from google.cloud import texttospeech

# Set the environment variable
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = google_app_creds

# Import ElevenLabs text-to-speech
from elevenlabs import generate, play

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Import settings
from .config.load_settings import settings

# Import settings variables
AI_VOICE_ID = settings['AI_AUDIO_SETTINGS']['AI_VOICE_ID']
AI_VOICE = settings['AI_AUDIO_SETTINGS']['AI_VOICE']
ELABS_MODEL = settings['AI_AUDIO_SETTINGS']['ELABS_MODEL']
MIN_SENTENCE_LENGTH = settings['MAIN_AI_SETTINGS']['MIN_SENTENCE_LENGTH']

# Generate audio using ElevenLabs client
def generate_audio(text, voice=AI_VOICE, model=ELABS_MODEL):
  return generate(
    text=text,
    voice=voice,
    model=model
  )

# Check if AI response has multiple long messages. Use with ElevenLabs client
def speak_sentences(sentences):
  if len(sentences) == 1:
    ai_audio = generate_audio(sentences[0])
    play(ai_audio)
  else:
    # Handle multiple sentences
    for sentence in sentences:
      ai_audio = generate_audio(sentence)
      play(ai_audio)

# Split sentences into text chuncks. Use with ElevenLabs client (non-streaming mode)
def split_text(text, max_length=MIN_SENTENCE_LENGTH):
  sentences = []
  while text:
    if len(text) <= max_length:
      sentences.append(text)
      break

    # Find the nearest punctuation mark after max_length
    split_at = max_length
    while split_at < len(text) and text[split_at] not in ['.', '!', '?']:
      split_at += 1

    # If we found a punctuation mark, we include it in the current chunk
    if split_at < len(text):
      split_at += 1

    sentences.append(text[:split_at].strip())
    text = text[split_at:].strip()

  return sentences

# Stream audio using ElevenLabs API
def stream_audio(text, voice=AI_VOICE_ID, model=ELABS_MODEL, api_key=os.environ.get("ELEVEN_API_KEY")):
  CHUNK_SIZE = 1096
  url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice}/stream"

  headers = {
    "Accept": "*/*",
    "Content-Type": "application/json",
    "xi-api-key": api_key
  }

  data = {
    "text": text,
    "model_id": model,
    "voice_settings": {
      "stability": 0.5,
      "similarity_boost": 0.5
    }
  }

  response = requests.post(url, headers=headers, json=data, stream=True)
  response.raise_for_status()

  logging.info(f"Streaming audio for text: {text}")

  # use subprocess to pipe the audio data to ffplay and play it
  ffplay_cmd = ['ffplay', '-nodisp', '-autoexit', '-']
  ffplay_proc = subprocess.Popen(ffplay_cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

  for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
    ffplay_proc.stdin.write(chunk)

  # close the ffplay process when finished
  ffplay_proc.stdin.close()
  ffplay_proc.wait()

# Function to generate audio using Google Text-to-Speech
def google_generate_audio(text):
    
  # Initialize the TextToSpeech client
  client = texttospeech.TextToSpeechClient()
  
  # Prepare the text input for the Text-to-Speech API
  input_text = texttospeech.SynthesisInput(text=text)
  
  # Configure voice settings such as language, voice type, and gender
  voice = texttospeech.VoiceSelectionParams(
    language_code="en-US",
    name="en-US-Standard-F",
    ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
  )
  
  # Configure audio settings like the audio file format and speaking rate
  audio_config = texttospeech.AudioConfig(
    audio_encoding=texttospeech.AudioEncoding.LINEAR16,
    speaking_rate=1.25  # Increase this number to speed up speech
  )
  
  # Make the API call to generate speech
  response = client.synthesize_speech(
    input=input_text, 
    voice=voice, 
    audio_config=audio_config
  )
  
  # Create a temporary file to store the audio
  with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
      
    # Write the audio data to the temporary file
    temp_file.write(response.audio_content)
    
    # Store the path to the temporary file
    temp_file_path = temp_file.name

  try:
    
    # Play the audio using your existing 'play' function
    play_audio_with_pyaudio(temp_file_path)
    
    # Delete the temporary file after playing
    os.remove(temp_file_path)
      
  except Exception as e:
    
    # If something goes wrong, delete the temporary file and log the error
    os.remove(temp_file_path)
    logging.error("Error processing Google TTS request:", exc_info=True)

# Function to play temp audio files
def play_audio_with_pyaudio(file_path):
    
  # Open the file
  wf = wave.open(file_path, 'rb')

  # Initialize PyAudio
  p = pyaudio.PyAudio()

  # Open a streaming stream
  stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                  channels=wf.getnchannels(),
                  rate=wf.getframerate(),
                  output=True)

  # Play audio
  data = wf.readframes(1024)
  while len(data) > 0:
    stream.write(data)
    data = wf.readframes(1024)

  # Close stream and PyAudio
  stream.stop_stream()
  stream.close()
  p.terminate()

# Set default voice engine
def default_audio(text):
  os.system(f'say -v Victoria "{text}"')
