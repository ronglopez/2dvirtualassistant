# Import necessary libraries
import os
import requests
import subprocess
import logging

# Import ElevenLabs text-to-speech
from elevenlabs import generate, play

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Import settings
from config.settings import MIN_SENTENCE_LENGTH, ELABS_MODEL, AI_VOICE, AI_VOICE_ID

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

# Split sentences into text chuncks. Use with ElevenLabs client
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
