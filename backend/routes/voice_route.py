# Import necessary libraries
from flask import Blueprint, jsonify, request
import logging
import tempfile
import time
import os
import openai
from ..ai_response import get_ai_response

# Import settings
from ..config.load_settings import settings

# Import settings variables
OPENAI_WHISPER_MODEL = settings['AI_AUDIO_SETTINGS']['OPENAI_WHISPER_MODEL']

# Create a Blueprint
voice_app = Blueprint('voice_app', __name__)

# Endpoint to handle voice-based user prompts
@voice_app.route('/voice', methods=['POST'])
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
