# Import necessary libraries
import openai
import os
from langchain import OpenAI, LLMChain, PromptTemplate
from langchain.memory import ConversationBufferWindowMemory
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Import the selected AI personality
from personalities import AI_PERSONALITY

# Sentiment analysis setup
accumulated_sentiment = 0
ai_mood = "Neutral"

SENTIMENT_SCORES = {
  "positive": 1,
  "neutral": 0,
  "negative": -1
}

MAX_LEVEL = 10
MIN_LEVEL = -10

# Load environment variables from .env file
load_dotenv()

# Initialize the OpenAI API key from the environment variable
openai.api_key = os.environ.get("OPENAI_API_KEY")

# Initialize Flask app and enable Cross-Origin Resource Sharing (CORS)
app = Flask(__name__)
CORS(app)

# Ensure the uploads directory exists for storing audio files
if not os.path.exists('uploads'):
  os.makedirs('uploads')

# Initialize a memory buffer to store conversation history
memory = ConversationBufferWindowMemory(k=5)

@app.route('/')
def hello():
  return "Hello, World!"

# Sentiment analysis
def analyze_sentiment(text):
  # Use OpenAI's model to predict sentiment
  response = openai.Completion.create(
    engine="text-davinci-002",
    prompt=f"Using 1 word (Positive, negative, or neutral), what's the sentiment of the following statement? '{text}'",
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
  elif accumulated_sentiment > 3:
    ai_mood = moods["positive"]
  elif accumulated_sentiment < -8:
    ai_mood = moods["very_negative"]
  elif accumulated_sentiment < -3:
    ai_mood = moods["negative"]
  else:
    ai_mood = moods["neutral"]

# Function to generate AI response based on user input
def get_ai_response(human_input):

  # Sentiment Analysis of User Input
  user_sentiment = analyze_sentiment(human_input)
  print(f"Detected User Sentiment: {user_sentiment}")

  # Update AI's mood based on user sentiment
  update_ai_mood(user_sentiment)

  print(f"Updated AI Mood: {ai_mood}")

  # Define the prompt template with placeholders for history and user input
  template = """
  
  Chat History:
  {history}

  Human: {human_input}
  AI:
  """

  # Combine the AI personality description with the prompt template
  prompt = PromptTemplate.from_template(AI_PERSONALITY["description"] + f"You are feeling {ai_mood}" + template)

  # Initialize LangChain with the specified model and parameters
  chatgpt_chain = LLMChain(
    llm=OpenAI(
      # model_name="text-davinci-003",
      model_name="davinci",
      temperature=0.9,
      max_tokens=10,
      top_p=1,
      frequency_penalty=0,
      presence_penalty=0.6
    ),
    prompt=prompt,
    verbose=True,
    memory=memory,
  )

  # Generate the AI response
  output = chatgpt_chain.predict(human_input=human_input)
  
  return output

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
