# Import necessary libraries
from flask import Blueprint, jsonify
import logging
from ..ai_response import get_ai_response  # Replace 'your_project_name' with the actual name or path

# Create a Blueprint
greeting_app = Blueprint('greeting_app', __name__)

# Endpoint to provide an initial greeting on page load
@greeting_app.route('/greeting', methods=['GET'])
def greeting():

  # Set greeting command
  user_input = "Give the User a warm welcome"

  # Get AI response
  ai_response = get_ai_response(user_input, 'system')

  logging.info(f"Greeting request received: {ai_response}")

  return jsonify(ai_response)
