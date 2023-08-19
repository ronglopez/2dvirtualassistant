# Import necessary libraries
from pathlib import Path

# Import ElevenLabs text-to-speech
from elevenlabs import generate

# Import settings
from config.settings import MIN_SENTENCE_LENGTH, ELABS_MODEL, AI_VOICE

# Function to initialize ElevenLabs
def generate_audio(text, voice=AI_VOICE, model=ELABS_MODEL):
  return generate(
    text=text,
    voice=voice,
    model=model
  )

# Split sentences into text chuncks
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

# Function to clear message history
def clear_messages_file():
  """Clear the contents of messages.json."""
  file_path = Path("data") / "messages.json"
  with file_path.open("w") as f:
    f.write("")
    