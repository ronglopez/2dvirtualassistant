####################
# MAIN AI SETTINGS #
####################

# Select Which Personality to Use
# Rin, Debug, or Megumin
AI_PERSONALITY = "Debug"
USER_NAME = "Ronald"
CHAR_LENGTH = 100
MIN_SENTENCE_LENGTH = 50

# ChatOpenAI Settings
TEMPERATURE = 0.9 # Set from 0 to 1 (the closer to 1 the more creative the responses)
OPENAI_MODEL = "gpt-3.5-turbo"
MAX_TOKENS = 50

# ElevenLabs Settings
USE_ELABS = False # Set to True if you want to use ElevenLabs, set to False for testing
AI_VOICE = "Freya" # For standard client output (For generate_audio function)
AI_VOICE_ID = "jsCqWAovK2LkecY7zXl4" # ID required for streaming (For stream_audio function)
ELABS_MODEL = "eleven_monolingual_v1" # Voice engine
ELABS_STREAM = True # For voice streaming mode

###############################
# SENTIMENT ANALYSIS SETTINGS #
###############################

# Sentiment analysis scoring system
SENTIMENT_SCORES = {
  "positive": 3,
  "neutral": 0,
  "negative": -3
}

# Sentiment analysis setup
accumulated_sentiment = 0
ai_mood = "neutral"

# Sentiment analysis max levels
MAX_LEVEL = 10
MIN_LEVEL = -10


#######################
# MAIN CONFIGURATIONS #
#######################

# Listen mode quit keyword (best to use a word with more than 2 sylables + keep it lowercase)
LISTEN_KEYWORD_QUIT = "goodbye"

# Listen function timeout
LISTEN_PERIODIC_MESSAGE_TIMER = 15

# Define a constant for the maximum number of messages
MAX_MESSAGES = 6

#######################
# MODERATION SETTINGS #
#######################

# Moderation set up to simply replace the profane word
MOD_REPLACE_RESPONSE = False # Set variable to True if you want the whole ai_response to be replaced
MOD_REPLACE_PROFANITY = "-" # Set text to replace profanity, ie. Using "-", result in "What the ----!"
