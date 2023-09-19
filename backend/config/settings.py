####################
# MAIN AI SETTINGS #
####################

AI_PERSONALITY = "Debug"                            # "Rin" or "Debug"
USER_NAME = "Ronald"
CHAR_LENGTH = 100                                   # Set character length for AI response (set in the system message)
MIN_SENTENCE_LENGTH = 50                            # For non-streaming mode
MAX_MESSAGES = 8                                    # Set max number of message to store in chat_history

# ChatOpenAI Settings
TEMPERATURE = 0.9                                   # Set from 0 to 1 (the closer to 1 the more creative the responses)
OPENAI_MODEL = "gpt-3.5-turbo"                      # OpenAI chatbot engine
MAX_TOKENS = 50                                     # Set max tockens for response from chatbot


#####################
# AI AUDIO SETTINGS #
#####################
OPENAI_WHISPER_MODEL = "whisper-1"                  # OpenAI transcription engine
LISTEN_KEYWORD_QUIT = "goodbye"                     # Best to use a word with more than 2 sylables + keep it lowercase

# Periodic timer in listen mode
LISTEN_PERIODIC_MESSAGE_TIMER = 60                  # Checks if it's time in seconds to send a periodic message

# ElevenLabs Settings
USE_ELABS = False                                   # Set to True if you want to use ElevenLabs, set to False for testing
ELABS_STREAM = True                                 # Set to True for voice streaming mode
AI_VOICE = "Freya"                                  # For standard client output (For generate_audio function)
AI_VOICE_ID = "jsCqWAovK2LkecY7zXl4"                # ID required for streaming (For stream_audio function)
ELABS_MODEL = "eleven_monolingual_v1"               # Voice engine
USE_GOOGLE = True                                   # Set to True if you want to use Google Cloud's TTS


#########################
# AI EMBEDDING SETTINGS #
#########################
OPENAI_EMBEDDING_MODEL = "text-embedding-ada-002"   # OpenAI embedding engine

# Vector Database Settings
PINECONE_INDEX_NAME = "openai-embeddings"           # Name of vector database (index name)


###############################
# SENTIMENT ANALYSIS SETTINGS #
###############################

# Sentiment analysis scoring system
SENTIMENT_SCORES = {
  "positive": 3,                                    # Positive sentiment multiplier
  "neutral": 0,                                     # Neutral sentiment multiplier
  "negative": -3                                    # Negative sentiment multiplier
}

# Sentiment analysis setup
accumulated_sentiment = 0                           # Initial sentiment score
ai_mood = "neutral"                                 # Initial AI mood

# Sentiment analysis max levels
MAX_LEVEL = 10                                      # Max level on the sentiment scale
MIN_LEVEL = -10                                     # Min level on the sentiment scale


#######################
# MODERATION SETTINGS #
#######################

MOD_REPLACE_RESPONSE = False                        # Set variable to True if you want the whole ai_response to be replaced
MOD_REPLACE_PROFANITY = "-"                         # Set text to replace profanity, ie. Using "-", result in "What the ----!"
