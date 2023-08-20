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
  "positive": 1,
  "neutral": 0,
  "negative": -1
}

# Sentiment analysis setup
accumulated_sentiment = 0
ai_mood = "neutral"

# Sentiment analysis max levels
MAX_LEVEL = 10
MIN_LEVEL = -10


#################################
# CHAT MESSAGE HISTORY SETTINGS #
#################################

# Define a constant for the maximum number of messages
MAX_MESSAGES = 4