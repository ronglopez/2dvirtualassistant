# Import necessary libraries
import openai
import os
import time
import logging
from threading import Thread
from multiprocessing import Process, Queue
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
from elevenlabs import set_api_key
from flask_socketio import SocketIO
import pytchat
import random
import signal
import sys

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
from .config.load_settings import settings
from .config.settings_api import settings_app

# Import routes
from .routes.greeting_route import greeting_app
from .routes.input_message_route import input_message_app
from .routes.periodic_message_route import periodic_message_app
from .routes.voice_route import voice_app

# Import models
from .models.voice_listener import VoiceListener

# Import settings variables
OPENAI_WHISPER_MODEL = settings['AI_AUDIO_SETTINGS']['OPENAI_WHISPER_MODEL']
LISTEN_KEYWORD_QUIT = settings['AI_AUDIO_SETTINGS']['LISTEN_KEYWORD_QUIT']
LISTEN_PERIODIC_MESSAGE_TIMER = settings['AI_AUDIO_SETTINGS']['LISTEN_PERIODIC_MESSAGE_TIMER']

# Register Blueprints with your main app
app.register_blueprint(greeting_app, url_prefix='/greeting')
app.register_blueprint(input_message_app, url_prefix='/input_message')
app.register_blueprint(periodic_message_app, url_prefix='/periodic_message')
app.register_blueprint(settings_app, url_prefix='/settings')
app.register_blueprint(voice_app, url_prefix='/voice')

# Import AI answer functions
from .ai_response import *
from .image_reader import *

# Initialize Queue
shared_queue = Queue(maxsize=5)

# YouTube Manager Class
class YouTubeManager:

  # Initialization function
  def __init__(self, queue):
    logging.info("YouTubeManager initialized.")

    # Instance variable for the monitor thread
    self.monitor_thread = None

    # Instance variable for the stop flag
    self.stop_monitor_thread = False

    # Instance variable for the queue
    self.queue = queue

    # Set streaming status to inactive initially
    self.is_active = False

    # Placeholder for multiprocessing process
    self.process = None

  # Function to start streaming
  def start_streaming(self, video_id):
    logging.info("Attempting to start streaming.")

    # Check if streaming is already active
    if not self.is_active:

      # Set streaming status to active
      self.is_active = True

      # Create a new process for YouTube live chat and start it
      self.process = Process(target=self.youtube_live_chat, args=(video_id,))
      self.process.start()

      # Start the monitor thread
      self.stop_monitor_thread = False
      self.monitor_thread = Thread(target=monitor_queue, args=(self, self.queue))
      self.monitor_thread.start()

  # Function to stop streaming
  def stop_streaming(self):
    logging.info("Attempting to stop streaming.")

    # Set streaming status to inactive
    self.is_active = False

    # Terminate the process if it exists
    if self.process:
      self.process.terminate()
      self.process.join()
      self.process = None

    # Signal that the monitor thread should stop
    self.stop_monitor_thread = True

    if self.monitor_thread:
      self.monitor_thread.join()
      self.monitor_thread = None

  # Function to check if streaming is active
  def is_streaming_active(self):
    return self.is_active

  # Function to manage YouTube live chat
  def youtube_live_chat(self, video_id):
    logging.info("Starting YouTube live chat management.")

    # Reset the stop flag
    self.stop_monitor_thread = False

    # Create a chat object using pytchat
    chat = pytchat.create(video_id=video_id)

    # Loop to fetch chat as long as the chat and stream are alive
    while chat.is_alive() and self.is_active:
      try:

        # Initialize an empty list to collect chat messages
        chat_messages = []

        # Fetch each chat item
        for c in chat.get().sync_items():

          # Collect the chat messages in the list
          chat_messages.append({
            'author': c.author.name,
            'message': c.message
          })

        # Randomly select a chat message and check if queue is full
        if len(chat_messages) > 0:
          selected_message = random.choice(chat_messages)

          # Trim the selected message to 200 characters if it exceeds that
          selected_message['message'] = selected_message['message'][:200]
          
          # Check if the queue is full
          if self.queue.full():
            _ = self.queue.get()  # Remove the oldest item
          
          self.queue.put(selected_message)  # Put the new item

      # Terminate chat on manual interrupt
      except KeyboardInterrupt:
        chat.terminate()
        break

      # Print any other exceptions
      except Exception as e:
        logging.error(f"An error occurred: {e}")

      time.sleep(5)

# Worker for monitoring and enqueueing the queue
def monitor_queue(youtube_manager, queue):
  
  while True:
    if youtube_manager.stop_monitor_thread:
      break

    if not queue.empty():
      selected_message = queue.get()
      
      selected_message_author = selected_message["author"]
      selected_message_content = selected_message["message"]

      # Get AI response
      ai_response = get_ai_response(f"Comment from the Youtube Live Stream. Please respond using 50 characters or less. {selected_message_author}: {selected_message_content}", 'user')

      data_to_emit = {
        'ai_response': ai_response,
        'selected_message_author': selected_message_author,
        'selected_message_content': selected_message_content
      }
      
      try:
        socketio.emit('new_message', data_to_emit, namespace='/')
      
      except Exception as e:
        logging.error(f"Specific error: {e}")

      time.sleep(1)

# Initialize the YouTube Manager
youtube_manager = YouTubeManager(shared_queue)

# Handle YouTube start stream
@socketio.on('start_youtube_stream')
def handle_start_youtube_stream(data):

  # Extract video_id from the data
  video_id = data.get('videoID')

  # Return a message indicating the streaming state has changed
  try:
    socketio.emit('success_streaming_toast', {"toast_message": "Streaming started successfully!"})
  except Exception as e:
    socketio.emit('error_streaming_toast', {"toast_message": str(e)})

  youtube_manager.start_streaming(video_id)

# Handle YouTube stop stream
@socketio.on('stop_youtube_stream')
def handle_stop_youtube_stream():

  youtube_manager.stop_streaming()
  logging.info("Stopped streaming, now attempting to emit toast message.")

  # Return a message indicating the streaming state has changed
  try:
    print("Backend is trying to send stopped_streaming_toast.")
    socketio.emit('stopped_streaming_toast', {"toast_message": "Streaming Stopped successfully!"})

  except Exception as e:
    print("Backend encountered an error:", str(e))
    socketio.emit('error_streaming_toast', {"toast_message": str(e)})

# Endpoints to handle voice-based user prompts and stopping voice listening
voice_listener = VoiceListener()
socketio.on('start_listening')(voice_listener.handle_start_listening)
socketio.on('stop_listening')(voice_listener.handle_stop_listening)

# Cleanup function
def cleanup(signum, frame):
  logging.info("Cleanup initiated...")
  
  # Stop streaming if active
  if youtube_manager.is_streaming_active():
    youtube_manager.stop_streaming()
      
  # Stop any listening activities
  voice_listener.handle_stop_listening()
  
  # Close the shared queue
  shared_queue.close()
  shared_queue.join_thread()
  
  sys.exit(0)

# Register the cleanup function for the interrupt signal
signal.signal(signal.SIGINT, cleanup)

# Run the Flask app in debug mode
if __name__ == "__main__":
  logging.info("Application starting...")
  socketio.run(app, debug=True)
