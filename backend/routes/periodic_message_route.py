# Import necessary libraries
from flask import Blueprint, jsonify
import logging
import random
from ..ai_response import get_ai_response  # Replace with the actual name or path

# Import settings
from ..personalities import AI_PERSONALITY

# Create a Blueprint
periodic_message_app = Blueprint('periodic_message_app', __name__)

# Endpoint to provide a periodic message
@periodic_message_app.route('/periodic_message', methods=['GET'])
def periodic_message():

  # Set periodic message command based on AI personality
  system_input = random.choice(AI_PERSONALITY["periodic_messages"]["passive"])

  # Get AI response
  ai_response = get_ai_response(system_input, 'system')
  logging.info(f"Banter request received: {ai_response}")
  return jsonify(ai_response)
