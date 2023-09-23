# Import necessary libraries
from flask import Blueprint, jsonify, request
from html import escape
import logging
from ..app import socketio
from ..ai_response import get_ai_response
from ..image_reader import upload_image

# Create a Blueprint
input_message_app = Blueprint('input_message_app', __name__)

# Endpoint to handle text-based user prompts
@socketio.on('input_message')
def handle_input_message(json_data):

  # Extract form data
  user_input = escape(json_data.get('input', ''))
  uploaded_file_bytes = json_data.get('file_bytes', None)
  uploaded_filename = json_data.get('filename', None)

  # Logging to check file data
  logging.info(f"File Bytes: {uploaded_file_bytes}, Filename: {uploaded_filename}")
  
  # Upload image
  image_description, image_error = upload_image(uploaded_file_bytes, uploaded_filename)

  # Check for errors
  if not user_input and not image_description:
    socketio.emit('error', {'error': 'No input provided'})
    return

  if image_error:
    socketio.emit('error', {'error': image_error})
    return

  # Get AI response
  ai_response = get_ai_response(user_input, 'user', image_description)
  
  # Emit response back to client
  socketio.emit('receive_input', ai_response)
