# Import necessary libraries
import openai
import atexit
import os
from pathlib import Path
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from elevenlabs import set_api_key

# Load environment variables from .env file
load_dotenv("config/.env")

# Initialize the OpenAI API key from the environment variable
openai.api_key = os.environ.get("OPENAI_API_KEY")
set_api_key(os.environ.get("ELEVEN_API_KEY"))

# Initialize Flask app and enable Cross-Origin Resource Sharing (CORS)
app = Flask(__name__)
CORS(app)

# Import AI answer functions
from ai_response import *

# Ensure the uploads directory exists for storing audio files
if not os.path.exists('uploads'):
  os.makedirs('uploads')

# Function to clear message history
def clear_messages_file():
  """Clear the contents of messages.json."""
  file_path = Path("data") / "messages.json"
  with file_path.open("w") as f:
    f.write("")

# Register the function to be called on exit
atexit.register(clear_messages_file)

# Endpoint to provide an initial greeting on page load
@app.route('/greeting', methods=['GET'])
def greeting():
  user_input = "Hello"
  ai_response = get_ai_response(user_input)
  return jsonify(ai_response)

# Endpoint to handle text-based user prompts
@app.route('/ask', methods=['POST'])
def ask():
  user_input = request.json.get('input', '')
  ai_response = get_ai_response(user_input)
  return jsonify(ai_response)

# Endpoint to handle voice-based user prompts
@app.route('/voice', methods=['POST'])
def voice():
  # Check if the audio file is present in the request
  if 'file' not in request.files:
    return jsonify(error="No file part"), 400

  audio_file = request.files['file']
  
  # Check if a filename is provided
  if audio_file.filename == '':
    return jsonify(error="No selected file"), 400

  # Determine the file extension based on content type
  content_type = audio_file.content_type
  extension = ".unknown"
  if "audio/wav" in content_type:
    extension = ".wav"
  elif "audio/webm" in content_type:
    extension = ".webm"

  # Save the uploaded audio file
  file_path = os.path.join("uploads", "uploaded_audio" + extension)
  audio_file.save(file_path)

  try:
    # Transcribe the audio file to text
    with open(file_path, "rb") as file_to_send:
      transcription_result = openai.Audio.transcribe(model="whisper-1", file=file_to_send)
      transcription = transcription_result['text']

    # Generate the AI response based on the transcription
    ai_response = get_ai_response(transcription)

    # Remove the saved audio file
    os.remove(file_path)

    return jsonify({
      "transcription": transcription,
      "ai_response": ai_response
    })

  except Exception as e:
    return jsonify(error=str(e)), 500

# Run the Flask app in debug mode
if __name__ == "__main__":
  app.run(debug=True)
