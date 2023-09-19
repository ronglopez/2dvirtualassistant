from flask import Blueprint, request, jsonify
import json

from .load_settings import settings

# Import main AI settings variables
AI_PERSONALITY = settings['MAIN_AI_SETTINGS']['AI_PERSONALITY']
USER_NAME = settings['MAIN_AI_SETTINGS']['USER_NAME']
CHAR_LENGTH = settings['MAIN_AI_SETTINGS']['CHAR_LENGTH']
MIN_SENTENCE_LENGTH = settings['MAIN_AI_SETTINGS']['MIN_SENTENCE_LENGTH']
MAX_MESSAGES = settings['MAIN_AI_SETTINGS']['MAX_MESSAGES']
TEMPERATURE = settings['MAIN_AI_SETTINGS']['TEMPERATURE']
OPENAI_MODEL = settings['MAIN_AI_SETTINGS']['OPENAI_MODEL']
MAX_TOKENS = settings['MAIN_AI_SETTINGS']['MAX_TOKENS']

# Import AI audio settings variables
OPENAI_WHISPER_MODEL = settings['AI_AUDIO_SETTINGS']['OPENAI_WHISPER_MODEL']
LISTEN_KEYWORD_QUIT = settings['AI_AUDIO_SETTINGS']['LISTEN_KEYWORD_QUIT']
LISTEN_PERIODIC_MESSAGE_TIMER = settings['AI_AUDIO_SETTINGS']['LISTEN_PERIODIC_MESSAGE_TIMER']
USE_ELABS = settings['AI_AUDIO_SETTINGS']['USE_ELABS']
ELABS_STREAM = settings['AI_AUDIO_SETTINGS']['ELABS_STREAM']
AI_VOICE = settings['AI_AUDIO_SETTINGS']['AI_VOICE']
AI_VOICE_ID = settings['AI_AUDIO_SETTINGS']['AI_VOICE_ID']
ELABS_MODEL = settings['AI_AUDIO_SETTINGS']['ELABS_MODEL']

# Import AI embedding settings variables
OPENAI_EMBEDDING_MODEL = settings['AI_EMBEDDING_SETTINGS']['OPENAI_EMBEDDING_MODEL']
PINECONE_INDEX_NAME = settings['AI_EMBEDDING_SETTINGS']['PINECONE_INDEX_NAME']

# Import AI sentiment settings variables
SENTIMENT_SCORES = settings['SENTIMENT_ANALYSIS_SETTINGS']['SENTIMENT_SCORES']
accumulated_sentiment = settings['SENTIMENT_ANALYSIS_SETTINGS']['accumulated_sentiment']
ai_mood = settings['SENTIMENT_ANALYSIS_SETTINGS']['ai_mood']
MAX_LEVEL = settings['SENTIMENT_ANALYSIS_SETTINGS']['MAX_LEVEL']
MIN_LEVEL = settings['SENTIMENT_ANALYSIS_SETTINGS']['MIN_LEVEL']

# Import AI moderation settings variables
MOD_REPLACE_RESPONSE = settings['MODERATION_SETTINGS']['MOD_REPLACE_RESPONSE']
MOD_REPLACE_PROFANITY = settings['MODERATION_SETTINGS']['MOD_REPLACE_PROFANITY']

settings_app = Blueprint('settings_app', __name__)

settings_data = {
  "AI_PERSONALITY": AI_PERSONALITY,
  "USER_NAME": USER_NAME,
  "CHAR_LENGTH": CHAR_LENGTH,
  "MIN_SENTENCE_LENGTH": MIN_SENTENCE_LENGTH,
  "MAX_MESSAGES": MAX_MESSAGES,
  "TEMPERATURE": TEMPERATURE,
  "OPENAI_MODEL": OPENAI_MODEL,
  "MAX_TOKENS": MAX_TOKENS,
  "OPENAI_WHISPER_MODEL": OPENAI_WHISPER_MODEL,
  "LISTEN_KEYWORD_QUIT": LISTEN_KEYWORD_QUIT,
  "LISTEN_PERIODIC_MESSAGE_TIMER": LISTEN_PERIODIC_MESSAGE_TIMER,
  "USE_ELABS": USE_ELABS,
  "ELABS_STREAM": ELABS_STREAM,
  "AI_VOICE": AI_VOICE,
  "AI_VOICE_ID": AI_VOICE_ID,
  "ELABS_MODEL": ELABS_MODEL,
  "OPENAI_EMBEDDING_MODEL": OPENAI_EMBEDDING_MODEL,
  "PINECONE_INDEX_NAME": PINECONE_INDEX_NAME,
  "accumulated_sentiment": accumulated_sentiment,
  "SENTIMENT_SCORES": SENTIMENT_SCORES,
  "ai_mood": ai_mood,
  "MAX_LEVEL": MAX_LEVEL,
  "MIN_LEVEL": MIN_LEVEL,
  "MOD_REPLACE_RESPONSE": MOD_REPLACE_RESPONSE,
  "MOD_REPLACE_PROFANITY": MOD_REPLACE_PROFANITY
}

@settings_app.route('/get_settings', methods=['GET'])
def get_settings():
  try:
    return jsonify({"message": "Settings fetched successfully", "settings": settings_data}), 200
  except Exception as e:
    return jsonify({"error": str(e)}), 400

@settings_app.route('/update_settings', methods=['POST'])
def update_settings(): 
  try:

    # Get the new settings from the request body
    new_settings = request.json

    # Update the in-memory settings variables directly
    for category, settings_group in settings.items():
      for key, value in new_settings.items():
        if key in settings_group:
          if isinstance(value, dict):  # Handle nested settings
            settings[category][key].update(value)
          else:
            settings[category][key] = value

    # Save updated settings back to JSON file
    with open('config/settings.json', 'w') as f:
      json.dump(settings, f, indent=2)

    return jsonify({"message": "Settings updated successfully"}), 200

  except Exception as e:
    return jsonify({"error": str(e)}), 400
  