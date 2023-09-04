# Import necessary libraries
import openai
import os
import time
import tempfile
import speech_recognition as sr
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from elevenlabs import set_api_key
from flask_socketio import SocketIO

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
from config.settings import LISTEN_KEYWORD_QUIT, LISTEN_PERIODIC_MESSAGE_TIMER, OPENAI_WHISPER_MODEL
from personalities import AI_PERSONALITY

# Import AI answer functions
from ai_response import *
from image_reader import *

# Endpoint to provide an initial greeting on page load
@app.route('/greeting', methods=['GET'])
def greeting():

  # Set greeting command
  user_input = "Give the User a warm welcome"

  # Get AI response
  ai_response = get_ai_response(user_input, 'system')

  logging.info(f"Greeting request received: {ai_response}")

  return jsonify(ai_response)

# Endpoint to provide a periodic message
@app.route('/periodic_message', methods=['GET'])
def periodic_message():

  # Set periodic message command based on AI personality
  system_input = AI_PERSONALITY["periodic_messages"]["passive"]

  # Get AI response
  ai_response = get_ai_response(system_input, 'system')
  logging.info(f"Banter request received: {ai_response}")
  return jsonify(ai_response)

# Endpoint to handle text-based user prompts
@app.route('/input_message', methods=['POST'])
def input_message():

  # Check for image upload
  image_description, image_error = upload_image(request)
    
  # Check for user text input
  user_input = request.form.get('input') or None
  
  # Error if no image file detected and no text input detected
  if not user_input and not image_description:
    logging.error("No Image, No Text")
    return jsonify(error="No input provided"), 400
  
  # Error in image upload function
  if image_error:
    logging.error("Error in image upload function")
    return jsonify(error=image_error), 400
  
  # Get AI response
  ai_response = get_ai_response(user_input, 'user', image_description)
  
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

  # Create a temporary file
  with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
    audio_file.save(temp_file.name)
    temp_file_path = temp_file.name

  try:
    # Start the monitoring timer
    start_transcription_time = time.time()

    # Transcribe the audio file to text
    with open(temp_file_path, "rb") as file_to_send:
      transcription_result = openai.Audio.transcribe(model=OPENAI_WHISPER_MODEL, file=file_to_send)
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

# Listen mode
class VoiceListener:
  def __init__(self):
    self.shared_data = {'result': None, 'error': None, 'quit': None} # Initialize data set to pass between the listener and the listen events
    self.background_thread_end = False # Indicate to listen while loop that a voice input has been detected
    self.should_stop = False # Stop listen while loop
    self.periodic_message_timer = 0 # Initialize timer
    self.should_pause_counter = False # Pause timer
    self.consecutive_periodic_messages = 0 # Initialize counter to track number of consectutive periodic messages

  # Create a temporary audio file
  def create_temp_file(self, speech):
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
      temp_file.write(speech.get_wav_data())
      return temp_file.name

  # Read from the temporary audio file
  def transcribe_audio(self, temp_file_path):
    with open(temp_file_path, 'rb') as speech:
      transcription_result = openai.Audio.transcribe(model=OPENAI_WHISPER_MODEL, file=speech)
      return transcription_result['text']

  def handle_stop_listening(self):
    logging.info("Listen Mode Deactivated")
    self.should_stop = True

  # Background listening thread
  def callback(self, recognizer, speech):

    logging.info("\n==========================\nUser voice input heard")

    # Pause Periodic Message Timer
    self.should_pause_counter = True
    
    try:

      # Create a temporary file
      temp_file_path = self.create_temp_file(speech)
      
      # Read from the temporary file
      transcription = self.transcribe_audio(temp_file_path)
      
      # Remove the saved audio file
      os.remove(temp_file_path)
      
      # Generate the AI response based on the transcription
      ai_response = get_ai_response(transcription, 'user')

      # Quit listen mode if keyword LISTEN_KEYWORD_QUIT is heard by itself
      transcription_lower = transcription.lower()
      
      if transcription_lower == f"{LISTEN_KEYWORD_QUIT}" or f"{LISTEN_KEYWORD_QUIT}." in transcription_lower:
        logging.info("Quitting Listen Mode")
        self.shared_data['quit'] = {
          "transcription": transcription,
          "ai_response": ai_response
        }
        
      else:
        self.shared_data['result'] = {
          "transcription": transcription,
          "ai_response": ai_response
        }

    except Exception as e:
      logging.error(f"Specific error: {e}")
      self.shared_data['error'] = "Could not process audio"

    # End background thread loop
    self.background_thread_end = True
    logging.info("Background Thread Ended!")

  # Main listening thread
  def handle_start_listening(self, data):

    # Reset shared_data
    self.shared_data = {'result': None, 'error': None, 'quit': None}

    # Default to 1 if not provided
    device_index = data.get('device_index', 1) 

    # Check microphone device_index number, make sure to use the correct one
    logging.info(f"Microphone number: {device_index}")

    # Initialize counter for periodic messages
    self.periodic_message_timer = 0
    self.should_pause_counter = False

    # Initialize Mic
    r = sr.Recognizer()
    r.dynamic_energy_threshold=False # set to 'True', the program will continuously try to re-adjust the energy threshold to match the environment based on the ambient noise level at that time.
    r.energy_threshold = 400 # 300 is the default value of the SR library
    mic = sr.Microphone()

    try:
      with sr.Microphone(device_index=device_index) as source:
        logging.info("Adjusting audio for ambience...")
        r.adjust_for_ambient_noise(source, duration=0.5)

    except AttributeError:
      logging.error("An error occurred while initializing the microphone. Deactivating listening mode.")
      
      # Notify the frontend that listening mode is being deactivated
      system_input = "Seems that the user's Microphone is not compatible with Listen Mode. Inform the user of this and tell them to try using the record function."
      ai_response = get_ai_response(system_input, "system")
      socketio.emit('listening_deactivated', ai_response)
      
      # Set the flag to stop listening
      self.should_stop = True
      return


    logging.info("\n==========================\nListening in background...")
    stop_listening = r.listen_in_background(mic, self.callback)

    while True:
      socketio.sleep(0.1)

      # Check the pause flag before incrementing the counter
      if not self.should_pause_counter:

        # Increment the counter
        self.periodic_message_timer += 0.1

      # Check if it's time to send a periodic message
      if self.periodic_message_timer >= LISTEN_PERIODIC_MESSAGE_TIMER:

        # Increment the consecutive_periodic_messages counter
        self.consecutive_periodic_messages += 1

        # Stop listening mode
        logging.info("\n==========================\nStopped Listening")
        stop_listening(wait_for_stop=False)

        # Pause Periodic Message Timer
        self.should_pause_counter = True

        if self.consecutive_periodic_messages < 3:
          system_input = AI_PERSONALITY["periodic_messages"]["passive"]
          ai_response = get_ai_response(system_input, "system")
          logging.info(f"Periodic message sent: {ai_response}")

          # Send periodic message
          socketio.emit('listening_periodic_message', ai_response)

        else:
          system_input = AI_PERSONALITY["periodic_messages"]["final"]
          ai_response = get_ai_response(system_input, "system")
          logging.info("Periodic message triggered 3 times consecutively. Stopping listen mode.")
    
          # Notify the frontend that listening mode is being deactivated
          socketio.emit('listening_deactivated', ai_response)

          # Reset Consecutive Periodic Message Counter
          self.consecutive_periodic_messages = 0
          break

        break

      # Check if frontend deactivated listen mode
      if self.should_stop:

        # Stop listening mode
        logging.info("\n==========================\nStopped Listening")
        stop_listening(wait_for_stop=False)

        # Pause Periodic Message Timer
        self.should_pause_counter = True
        self.should_stop = False

        # Reset Consecutive Periodic Message Counter
        self.consecutive_periodic_messages = 0

        break

      # Check listen mode recorded voice input
      if self.background_thread_end:

        # Stop listening mode
        logging.info("\n==========================\nStopped Listening")
        stop_listening(wait_for_stop=False)

        # Paused Periodic Message Timer in stop_listening callback function

        # Reset Consecutive Periodic Message Counter
        self.consecutive_periodic_messages = 0

        # Check if the thread finished successfully
        if self.shared_data['result'] is not None:
          logging.info("\n==========================")
          socketio.emit('listening_result', self.shared_data['result'])

          break

        elif self.shared_data['quit'] is not None:
          socketio.emit('listening_quit', self.shared_data['quit'])

          break

        elif self.shared_data['error'] is not None:
          socketio.emit('listening_error', self.shared_data['error'])

          break
          
        else:
          socketio.emit('listening_error', "Listening timed out or no audio detected")

          break

    # Reset Background Thread flag
    self.background_thread_end = False

# Endpoints to handle voice-based user prompts and stopping voice listening
voice_listener = VoiceListener()
socketio.on('start_listening')(voice_listener.handle_start_listening)
socketio.on('stop_listening')(voice_listener.handle_stop_listening)

# Run the Flask app in debug mode
if __name__ == "__main__":
  logging.info("Running the Flask app in debug mode...")
  socketio.run(app, debug=True)
