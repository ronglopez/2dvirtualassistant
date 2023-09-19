# Import necessary libraries
from flask import Blueprint, jsonify, request
from html import escape
import logging
from ..ai_response import get_ai_response
from ..image_reader import upload_image

# Create a Blueprint
input_message_app = Blueprint('input_message_app', __name__)

# Endpoint to handle text-based user prompts
@input_message_app.route('/input_message', methods=['POST'])
def input_message():

  # Check for image upload
  image_description, image_error = upload_image(request)
    
  # Check for user text input and sanitize it
  user_input = escape(request.form.get('input')) or None
  
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
