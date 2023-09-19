# Import settings
import logging
import tempfile
import openai
import os
import speech_recognition as sr
from ..app import socketio
from ..ai_response import get_ai_response

# Import settings
from ..personalities import AI_PERSONALITY
from ..config.load_settings import settings

# Import settings variables
OPENAI_WHISPER_MODEL = settings['AI_AUDIO_SETTINGS']['OPENAI_WHISPER_MODEL']
LISTEN_KEYWORD_QUIT = settings['AI_AUDIO_SETTINGS']['LISTEN_KEYWORD_QUIT']
LISTEN_PERIODIC_MESSAGE_TIMER = settings['AI_AUDIO_SETTINGS']['LISTEN_PERIODIC_MESSAGE_TIMER']

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
        logging.info(device_index)
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
