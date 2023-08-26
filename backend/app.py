# Import necessary libraries
import openai
import os
import time
from time import sleep
import tempfile
import speech_recognition as sr
from threading import Timer
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

# Set shared data variable for listen mode
shared_data = {'result': None, 'error': None, 'quit': None}
background_thread_end = False

# Endpoint to provide an initial greeting on page load
@app.route('/greeting', methods=['GET'])
def greeting():
  user_input = "Give the User a warm welcome"
  ai_response = get_ai_response(user_input, 'system')
  logging.info(f"Greeting request received: {ai_response}")
  return jsonify(ai_response)

# Endpoint to provide a periodic message
@app.route('/periodic_message', methods=['GET'])
def periodic_message():
  system_input = "Say something to make conversation"
  message_role = "system"
  ai_response = get_ai_response(system_input, message_role)
  logging.info(f"Banter request received: {ai_response}")
  return jsonify(ai_response)

# Endpoint to handle text-based user prompts
@app.route('/ask', methods=['POST'])
def ask():
  user_input = request.json.get('input', 'user')
  ai_response = get_ai_response(user_input)
  logging.info(f"Ask request received: {user_input} -> {ai_response}")
  return jsonify(ai_response)
    
# Background listening thread
def callback(recognizer, speech):
  global shared_data, background_thread_end  # Declare it as global to modify it

  logging.info("==========================")
  logging.info("User voice input heard")
  
  try:

    # Create a temporary file
    logging.info("Creating temp file")

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
      temp_file.write(speech.get_wav_data())
      temp_file_path = temp_file.name  # Get the path to the temporary file
      logging.info("Temp file created successfully")
      logging.info("Reading temp file")
    
    # Read from the temporary file
    with open(temp_file_path, 'rb') as speech:
      transcription_result = openai.Audio.transcribe(model="whisper-1", file=speech)
      transcription = transcription_result['text']
      logging.info("Temp file read successfully")
    
    # Remove the saved audio file
    os.remove(temp_file_path)
    logging.info("Temp file removed successfully")
    
    # Generate the AI response based on the transcription
    logging.info("Passing transcript to AI")
    logging.info("********************")
    ai_response = get_ai_response(transcription, 'user')
    logging.info("********************")

    # Quit listen mode if keyword LISTEN_KEYWORD_QUIT is heard by itself
    logging.info("Transcription received")
    transcription_lower = transcription.lower()
    
    if transcription_lower == f"{LISTEN_KEYWORD_QUIT}" or f"{LISTEN_KEYWORD_QUIT}." in transcription_lower:
      logging.info("Quitting Listen Mode")
      shared_data['quit'] = {
        "transcription": transcription,
        "ai_response": ai_response
      }
      
    else:
      logging.info("Passing back results")
      shared_data['result'] = {
        "transcription": transcription,
        "ai_response": ai_response
      }

  except:
    logging.error("Could not request results from Google Speech Recognition service")

  # End background thread loop
  background_thread_end = True
  logging.info("Background Thread Ended!")

# Endpoint to handle voice-based user prompts
@socketio.on('start_listening')
def handle_start_listening(data):
  global shared_data, background_thread_end

  # Reset shared_data
  shared_data = {'result': None, 'error': None, 'quit': None}

  # Default to 1 if not provided
  device_index = data.get('device_index', 1) 

   # Check microphone device_index number, make sure to use the correct one
  logging.info(f"Microphone number: {device_index})")

  # Initialize Mic
  r = sr.Recognizer()
  r.dynamic_energy_threshold=False # set to 'True', the program will continuously try to re-adjust the energy threshold to match the environment based on the ambient noise level at that time.
  r.energy_threshold = 400 # 300 is the default value of the SR library
  mic = sr.Microphone()

  with sr.Microphone(device_index=device_index) as source:
    logging.info("Adjusting audio for ambience...")
    r.adjust_for_ambient_noise(source, duration=0.5)

  logging.info("==========================")
  logging.info("Listening in background...")
  stop_listening = r.listen_in_background(mic, callback)
  logging.info("==========================")

  while True:
    time.sleep(0.1)

    if background_thread_end:

      # Check if the thread finished successfully
      if shared_data['result'] is not None:
        logging.info("==========================")
        logging.info("Shared data received")
        socketio.emit('listening_result', shared_data['result'])
        break

      elif shared_data['quit'] is not None:
        socketio.emit('listening_quit', shared_data['quit'])
        break

      elif shared_data['error'] is not None:
        socketio.emit('listening_error', shared_data['error'])
        break
        
      else:
        socketio.emit('listening_error', "Listening timed out or no audio detected")
        break
  
  # Stop listening mode
  stop_listening(wait_for_stop=False)

  # Reset Background Thread flag
  background_thread_end = False
  logging.info("Shared data sent")
  logging.info("==========================")
  
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
    ai_response = get_ai_response(transcription, 'user')

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
