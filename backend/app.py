# Import necessary libraries
import openai
import json
import atexit
import os
from pathlib import Path
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from elevenlabs import set_api_key, generate, play

# Import LangChain
from langchain import PromptTemplate, LLMChain
from langchain.memory import ConversationBufferWindowMemory, ChatMessageHistory
from langchain.chat_models import ChatOpenAI
from langchain.schema import messages_from_dict, messages_to_dict

# Load environment variables from .env file
load_dotenv()

# Initialize the OpenAI API key from the environment variable
openai.api_key = os.environ.get("OPENAI_API_KEY")
set_api_key(os.environ.get("ELEVEN_API_KEY"))

# Initialize Flask app and enable Cross-Origin Resource Sharing (CORS)
app = Flask(__name__)
CORS(app)

# Import the selected AI personality
from personalities import AI_PERSONALITY

# Sentiment analysis setup
accumulated_sentiment = 0
ai_mood = "neutral"

# Sentiment analysis scoring system
SENTIMENT_SCORES = {
  "positive": 1,
  "neutral": 0,
  "negative": -1
}

# Sentiment analysis max levels
MAX_LEVEL = 10
MIN_LEVEL = -10

# Define a constant for the maximum number of messages
MAX_MESSAGES = 4

# Ensure the uploads directory exists for storing audio files
if not os.path.exists('uploads'):
  os.makedirs('uploads')

@app.route('/')
def hello():
  return "Hello, World!"

# Function to clear message history
def clear_messages_file():
  """Clear the contents of messages.json."""
  with Path("messages.json").open("w") as f:
    f.write("")

# Register the function to be called on exit
atexit.register(clear_messages_file)

# Sentiment analysis
# todo: Further testing required, sometimes will use other words and that will break the system. This NEEDS to be consistent
def analyze_sentiment(text):
  # Use OpenAI's model to predict sentiment
  response = openai.Completion.create(
    engine="text-davinci-002",
    prompt=f"Using ONLY 1 word in lowercase (and only these words: positive, negative, or neutral), what's the sentiment of the following text? '{text}'",
    temperature=0.5,
    max_tokens=10,
    top_p=1,
    frequency_penalty=0,
    presence_penalty=0
  )

  sentiment = response.choices[0].text.strip()

  return sentiment

# Update AI's Mood depending on sentiment analysis
def update_ai_mood(user_sentiment):
  global ai_mood, accumulated_sentiment

  # Update accumulated sentiment
  accumulated_sentiment += SENTIMENT_SCORES[user_sentiment]

  # Ensure accumulated sentiment is within max and min levels
  accumulated_sentiment = max(MIN_LEVEL, min(accumulated_sentiment, MAX_LEVEL))

  # Update AI mood based on thresholds
  moods = AI_PERSONALITY["moods"]

  if accumulated_sentiment > 8:
    ai_mood = moods["very_positive"]
  elif accumulated_sentiment > 2:
    ai_mood = moods["positive"]
  elif accumulated_sentiment < -8:
    ai_mood = moods["very_negative"]
  elif accumulated_sentiment < -2:
    ai_mood = moods["negative"]
  else:
    ai_mood = moods["neutral"]

# Function to generate AI response based on user input
def get_ai_response(human_input):

  # Sentiment Analysis of User Input
  user_sentiment = analyze_sentiment(human_input)

  # Update AI's mood based on user sentiment
  update_ai_mood(user_sentiment)

  # Initialize LangChain with the specified model and parameters
  llm = ChatOpenAI(
    temperature=0.9,
    model_name="gpt-3.5-turbo",
    max_tokens=10
  )

  history = ChatMessageHistory()

  # Add AI background/persoality
  system_template = AI_PERSONALITY["description"]

  # Define the prompt template with placeholders for history and user input
  template = """
  
  Chat History:
  {history}

  Human: {human_input}
  AI:
  """

  # Check if the file is empty
  file_path = Path("messages.json")
  if file_path.stat().st_size == 0:
    loaded_messages = []
  else:
    with file_path.open("r") as f:
      loaded_messages = json.load(f)[-MAX_MESSAGES:]

  if loaded_messages:
    history = ChatMessageHistory(messages=messages_from_dict(loaded_messages))

    # Separate system and non-system messages
    system_messages = [msg for msg in loaded_messages if msg["type"] == "system"]
    non_system_messages = [msg for msg in loaded_messages if msg["type"] != "system"]

    # Calculate the number of non-system messages to keep
    num_non_system_to_keep = MAX_MESSAGES - len(system_messages)
    
    # Trim non-system messages
    trimmed_non_system_messages = non_system_messages[-num_non_system_to_keep:]

    # Combine system and non-system messages
    loaded_messages = system_messages + trimmed_non_system_messages


  # Combine the AI personality description with the prompt template
  prompt = PromptTemplate(input_variables=["history", "human_input"], template=system_template + f"You are feeling {ai_mood}" + template)

  conversation_bufw = LLMChain(   # - todo: This should actually be ConversationChain, but bug seems to be breaking at this moment
    llm=llm,
    prompt=prompt,
    memory=ConversationBufferWindowMemory(chat_memory=history, k=MAX_MESSAGES),
    verbose=True,
  )

  ai_response = conversation_bufw.predict(human_input=human_input)

  conversation_messages = conversation_bufw.memory.chat_memory.messages

  messages = messages_to_dict(conversation_messages)

  with Path("messages.json").open("w") as f:
    json.dump(messages, f, indent=2)

  # Convert the AI's text response into audio using ElevenLabs
  ai_audio = generate(
    text=ai_response,
    voice="Freya",  # You can choose a different voice if needed
    model="eleven_monolingual_v1"
  )

  play(ai_audio)

  print(f"Number of messages before writing to JSON: {len(messages)}")
  
  return ai_response

# Endpoint to provide an initial greeting on page load
@app.route('/greeting', methods=['GET'])
def greeting():
  user_input = "Hello"
  ai_response = get_ai_response(user_input)
  return jsonify(ai_response)

# Endpoint to handle text-based user prompts
@app.route('/ask', methods=['POST'])
def ask():
  user_input = request.json.get('input', '')
  ai_response = get_ai_response(user_input)
  return jsonify(ai_response)

# Endpoint to handle voice-based user prompts
@app.route('/voice', methods=['POST'])
def voice():
  # Check if the audio file is present in the request
  if 'file' not in request.files:
    return jsonify(error="No file part"), 400

  audio_file = request.files['file']
  
  # Check if a filename is provided
  if audio_file.filename == '':
    return jsonify(error="No selected file"), 400

  # Determine the file extension based on content type
  content_type = audio_file.content_type
  extension = ".unknown"
  if "audio/wav" in content_type:
    extension = ".wav"
  elif "audio/webm" in content_type:
    extension = ".webm"

  # Save the uploaded audio file
  file_path = os.path.join("uploads", "uploaded_audio" + extension)
  audio_file.save(file_path)

  try:
    # Transcribe the audio file to text
    with open(file_path, "rb") as file_to_send:
      transcription_result = openai.Audio.transcribe(model="whisper-1", file=file_to_send)
      transcription = transcription_result['text']

    # Generate the AI response based on the transcription
    ai_response = get_ai_response(transcription)

    # Remove the saved audio file
    os.remove(file_path)

    return jsonify({
      "transcription": transcription,
      "ai_response": ai_response
    })

  except Exception as e:
    return jsonify(error=str(e)), 500

# Run the Flask app in debug mode
if __name__ == "__main__":
  app.run(debug=True)
