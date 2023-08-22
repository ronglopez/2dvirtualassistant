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
TEMPERATURE = 0.9
OPENAI_MODEL = "gpt-3.5-turbo"
MAX_TOKENS = 50

# ElevenLabs Settings
AI_VOICE = "Freya" # For standard client output 
AI_VOICE_ID = "jsCqWAovK2LkecY7zXl4" # For streaming 
ELABS_MODEL = "eleven_monolingual_v1"
ELABS_STREAM = True

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

# Listen function timeout
LISTEN_TIMEOUT = 10

# Give the listen function enough time to complete
# This timeout will continue the main thread will Listen is active if it takes too long
THREAD_TIMEOUT = 20

# Define a constant for the maximum number of messages
MAX_MESSAGES = 4

#######################
# MODERATION SETTINGS #
#######################

# Moderation set up to simply replace the profane word
# Set variable to True if you want the whole ai_response to be replaced
MOD_REPLACE_RESPONSE = False
