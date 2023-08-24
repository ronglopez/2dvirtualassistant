# Import necessary libraries
import openai
import os
import time
import tempfile
import speech_recognition as sr
import threading
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from elevenlabs import set_api_key
from flask_socketio import SocketIO, emit

# Load environment variables from .env file
load_dotenv("config/.env")

# Initialize the OpenAI API key from the environment variable
openai.api_key = os.environ.get("OPENAI_API_KEY")
set_api_key(os.environ.get("ELEVEN_API_KEY"))

# Initialize Flask app and enable Cross-Origin Resource Sharing (CORS)
app = Flask(__name__)
CORS(app)

# Initialize SocketIO with the Flask app
socketio = SocketIO(app, cors_allowed_origins="*")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logging.info("Starting the application...")

# Import settings
from config.settings import LISTEN_TIMEOUT, THREAD_TIMEOUT, LISTEN_KEYWORD_QUIT

# Import AI answer functions
from ai_response import *

# Endpoint to provide an initial greeting on page load
@app.route('/greeting', methods=['GET'])
def greeting():
  user_input = "Hello"
  ai_response = get_ai_response(user_input)
  logging.info(f"Greeting request received: {ai_response}")
  return jsonify(ai_response)

# Endpoint to handle text-based user prompts
@app.route('/ask', methods=['POST'])
def ask():
  user_input = request.json.get('input', '')
  ai_response = get_ai_response(user_input)
  logging.info(f"Ask request received: {user_input} -> {ai_response}")
  return jsonify(ai_response)
    
# Function to handle listening in a separate thread
def listen_thread(shared_data, device_index):

  # Check microphone device_index number, make sure to use the correct one
  logging.info(f"Microphone number: {device_index})")

  # Initialize Mic
  r = sr.Recognizer()
  r.dynamic_energy_threshold=False
  r.energy_threshold = 400

  with sr.Microphone(device_index=device_index) as source:
    logging.info("\nListening...")
    r.adjust_for_ambient_noise(source, duration=0.5)

    try:
      audio = r.listen(source, timeout=LISTEN_TIMEOUT)

    except:
      logging.warning("Audio Timed Out!")
      shared_data['error'] = "Audio Timed Out!"
      return []

  logging.warning("No longer listening")

  if audio:

    # Create a temporary file
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
      temp_file.write(audio.get_wav_data())
      temp_file_path = temp_file.name  # Get the path to the temporary file

    # Read from the temporary file
    with open(temp_file_path, 'rb') as speech:
      transcription_result = openai.Audio.transcribe(model="whisper-1", file=speech)
      transcription = transcription_result['text']

    # Remove the saved audio file
    os.remove(temp_file_path)

    # Generate the AI response based on the transcription
    ai_response = get_ai_response(transcription)

    # Quit listen mode if keyword "Quit" is heard by itself
    transcription_lower = transcription.lower()
    
    if transcription_lower == f"{LISTEN_KEYWORD_QUIT}" or f"{LISTEN_KEYWORD_QUIT}." in transcription_lower:
      shared_data['quit'] = {
        "transcription": transcription,
        "ai_response": ai_response
      }
      
    else:
      shared_data['result'] = {
        "transcription": transcription,
        "ai_response": ai_response
      }

    return 
  
# Endpoint to handle voice-based user prompts
@socketio.on('start_listening')
def handle_start_listening(data):
  device_index = data.get('device_index', 1)  # Default to 1 if not provided
  shared_data = {'result': None, 'error': None}

  # Create a thread to handle the listening
  t = threading.Thread(target=listen_thread, args=(shared_data, device_index))
  t.start()

  # Wait for the thread to finish, with a timeout (e.g., 10 seconds)
  t.join(timeout=THREAD_TIMEOUT)

  # Check if the thread finished successfully
  if shared_data['result'] is not None:
    emit('listening_result', shared_data['result'])
  elif shared_data['quit'] is not None:
    emit('listening_quit', shared_data['quit'])  
  elif shared_data['error'] is not None:
    emit('listening_error', shared_data['error'])
  else:
    emit('listening_error', "Listening timed out or no audio detected")
  
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

  # Create a temporary file
  with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
    audio_file.save(temp_file.name)
    temp_file_path = temp_file.name

  try:
    # Start the monitoring timer
    start_transcription_time = time.time()

    # Transcribe the audio file to text
    with open(temp_file_path, "rb") as file_to_send:
      transcription_result = openai.Audio.transcribe(model="whisper-1", file=file_to_send)
      transcription = transcription_result['text']
    
    # End the transcription monitoring timer
    end_transcription_time = time.time()
    transcription_time = end_transcription_time - start_transcription_time
    logging.info(f"Audio Transcription Time: {transcription_time:.2f} seconds")

    # Generate the AI response based on the transcription
    ai_response = get_ai_response(transcription)

    # Remove the temporary audio file
    os.remove(temp_file_path)

    return jsonify({
      "transcription": transcription,
      "ai_response": ai_response
    })

  except Exception as e:
    # Remove the temporary audio file in case of an exception
    os.remove(temp_file_path)
    logging.error("Error processing voice request:", exc_info=True)
    return jsonify(error=str(e)), 500

# Run the Flask app in debug mode
if __name__ == "__main__":
  logging.info("Running the Flask app in debug mode...")
  socketio.run(app, debug=True)
