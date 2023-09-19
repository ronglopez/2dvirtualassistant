# Import necessary libraries
import time
import logging
import openai

# Import utility files
from .utils import split_text, speak_sentences, stream_audio, default_audio
from .moderation import moderate_output

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Import settings
from .personalities import AI_PERSONALITY
from .config.load_settings import settings

# Import settings variables
MAX_MESSAGES = settings['MAIN_AI_SETTINGS']['MAX_MESSAGES']
accumulated_sentiment = settings['SENTIMENT_ANALYSIS_SETTINGS']['accumulated_sentiment']
ai_mood = settings['SENTIMENT_ANALYSIS_SETTINGS']['ai_mood']
TEMPERATURE = settings['MAIN_AI_SETTINGS']['TEMPERATURE']
OPENAI_MODEL = settings['MAIN_AI_SETTINGS']['OPENAI_MODEL']
MAX_TOKENS = settings['MAIN_AI_SETTINGS']['MAX_TOKENS']
USE_ELABS = settings['AI_AUDIO_SETTINGS']['USE_ELABS']
ELABS_STREAM = settings['AI_AUDIO_SETTINGS']['ELABS_STREAM']

# Import sentiment analysis
from .sentiment_analysis import update_ai_mood, analyze_sentiment_vader

# Import embeddings
from .embeddings.embedding_functions import search_query

# Initialize an empty list to store chat messages
chat_history = []

# Function to check if the text is a question
def is_question(text):
  question_words = ["who", "what", "where", "when", "why", "how"]
  question_starts = ["is", "are", "will", "can", "do", "does"]
  
  # Check for question mark
  if "?" in text:
    return True
  
  # Check for question words
  if any(word in text.lower().split() for word in question_words):
    return True
  
  # Check for common question starting words
  if any(text.lower().startswith(start) for start in question_starts):
    return True
  
  return False

# Function to generate AI response based on user input
def get_ai_response(message_input, message_role, image_description=None):

  logging.info("\n==========================\nGetting AI Response\n==========================")
  
  # Global variables
  global chat_history, ai_mood, accumulated_sentiment

  # Start the ai response monitoring timer
  start_response_time = time.time()

  # Sentiment Analysis if user sent message
  if message_role == "user" and message_input is not None:

    # Select using VADER or non VADER analysis
    # user_sentiment = analyze_sentiment(message_input)
    user_sentiment = analyze_sentiment_vader(message_input)
    
    logging.info(user_sentiment)

    # Update AI's mood based on user sentiment
    ai_mood, accumulated_sentiment = update_ai_mood(user_sentiment, ai_mood, accumulated_sentiment)

  # Initialize chat messages
  messages = []

  # Add AI background/personality and ai mood to system template
  system_template = f"{AI_PERSONALITY['description']}\n\nYou will emulate feeling {ai_mood}"

  # Check if the message is a question
  if message_input is not None and is_question(message_input):

    system_template = system_template + "\n\nChat Context:"
        
    # Check embeddings for better context
    matches = search_query(message_input)
    for match in matches:
      system_template = f"{system_template}\n{match['metadata']}"

  logging.info(f"System template:\n{system_template}")

  # Add the system template to messages
  messages.append({"role": "system", "content": system_template})

  # Set chat history
  if chat_history:
    
    # Non-system messages
    non_system_messages = [msg for msg in chat_history if msg["role"] != "system"]
    
    # Trim non-system messages
    trimmed_non_system_messages = non_system_messages[-MAX_MESSAGES:]

    # Combine system and non-system messages
    chat_history_str = f"Chat History:\n{trimmed_non_system_messages}"
    logging.info(chat_history_str)

    # Add chat history to messages
    messages += trimmed_non_system_messages # Use += to concatenate the lists

  # Check for message input
  if not message_input:

    # Add default image upload message
    message_input = "Tell me what the image that was uploaded is."
    
  logging.info(f"Incoming Message: {message_input}")

  # Add uploaded image generated description
  if image_description is not None:
    messages.append({"role": "system", "content": f"An image has been uploaded. You MUST pretend to being able to see the image. Here's a description of the image from an Image-To-Text engine that you can use to describe what you see: '{image_description}'. Tell the user what you see."})
    logging.info(f"Added uploaded image description: {image_description}")
  
  # Add formatted message to AI bot into messages 
  messages.append({"role": message_role, "content": message_input})
  logging.info(f"Messages: {messages}")

  # Use OpenAI's model to predict sentiment
  ai_response = openai.ChatCompletion.create(
    model=OPENAI_MODEL,
    temperature=TEMPERATURE,
    max_tokens=MAX_TOKENS,
    top_p=1,
    frequency_penalty=0,
    presence_penalty=0,
    messages=messages
  )

  try:
    
    # Get the AI response
    ai_response = ai_response["choices"][0]["message"]["content"]
    logging.info(f"AI response: {ai_response}")

    # Moderate AI response
    ai_response = moderate_output(ai_response)

    # End the ai response monitoring timer
    end_response_time = time.time()  
    ai_response_time = end_response_time - start_response_time
    logging.info(f"AI response time: {ai_response_time:.2f} seconds")

    # Save messages to memory (in-memory chat history)
    chat_history.append({"role": message_role, "content": message_input})
    chat_history.append({"role": "assistant", "content": ai_response})

    # Trim the chat history to only keep the latest MAX_MESSAGES
    chat_history = chat_history[-MAX_MESSAGES:]

  # Error handling for exceeding OpenAI max token use
  except Exception as e:
    logging.error("An error occurred, possibly due to token limit. Clearing message history and restarting.", exc_info=True)
    
    ai_response = AI_PERSONALITY["error_message"]

    return ai_response

  # Convert the AI's text response into audio using ElevenLabs
  # Start the text-to-speech monitoring timer
  start_text_to_speech_time = time.time()

  # ElevenLabs text-to-speech functions
  if USE_ELABS:
    try:
      if ELABS_STREAM:

        # Use ElevenLabs streaming method for text-to-speech
        stream_audio(ai_response)

      else:

        # Use ElevenLabs sentence-by-sentence method for text-to-speech
        sentences = split_text(ai_response)
        speak_sentences(sentences)

    except Exception as e:
      logging.error(f"An error occurred while using ElevenLabs: {e}")
      ai_response = f"{ai_response} {AI_PERSONALITY['error_message']}"
      
      # Fallback to default system text-to-speech functions
      default_audio(ai_response)

  # Default to system text-to-speech functions
  else:
    default_audio(ai_response)

  # End the text-to-speech monitoring timer
  end_text_to_speech_time = time.time()
  text_to_speech_time = end_text_to_speech_time - start_text_to_speech_time
  logging.info(f"Text-to-Speech Generation Time: {text_to_speech_time:.2f} seconds")

  # Monitor memory variable
  logging.info(f"Number of messages before writing to memory: {len(chat_history)}\n==========================")

  
  return ai_response
