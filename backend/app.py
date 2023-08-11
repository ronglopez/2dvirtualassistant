# Import necessary libraries
import openai
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize the OpenAI API key from environment variable
openai.api_key = os.environ.get("OPENAI_API_KEY")

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Ensure the uploads directory exists
if not os.path.exists('uploads'):
  os.makedirs('uploads')

MIME_TYPE_MAP = {
  "audio/wav": ".wav",
  "audio/mp4": ".m4a",
  # Add more mappings if needed
}

@app.route('/')
def hello():
  return "Hello, World!"

@app.route('/ask', methods=['POST'])
def ask():
  user_input = request.json.get('input', '')
  response = openai.Completion.create(
    engine="davinci",
    prompt=user_input,
    max_tokens=50,
    temperature=0.8
  )
  return jsonify(response.choices[0].text.strip())

@app.route('/voice', methods=['POST'])
def voice():
  print("Received request.")
  print(request.files)

  if 'file' not in request.files:
    return jsonify(error="No file part"), 400

  audio_file = request.files['file']

  if audio_file.filename == '':
    return jsonify(error="No selected file"), 400

  # Get the content type of the uploaded file
  content_type = audio_file.content_type

  # Determine the file extension based on the content type
  if "audio/wav" in content_type:
    extension = ".wav"
  elif "audio/webm" in content_type:
    extension = ".webm"
  else:
    extension = ".unknown"  # or handle other types as needed

  # Save the uploaded file locally with the determined extension
  file_path = os.path.join("uploads", "uploaded_audio" + extension)
  audio_file.save(file_path)

  try:
    print(file_path)
    # Transcribe the audio file using Whisper ASR API
    with open(file_path, "rb") as file_to_send:
      transcription_result = openai.Audio.transcribe(model="whisper-1", file=file_to_send)
      print(f"Transcription Result: {transcription_result}")  # Print the entire result
      transcription = transcription_result['text']  # Adjusted this line

    print(f"Transcription: {transcription}")

    print("Querying GPT-3.")
    # Get a response from GPT-3 using the transcription
    response = openai.Completion.create(
      engine="davinci",
      prompt=transcription,
      max_tokens=50,
      temperature=0.8
    )

    # Delete the saved file
    os.remove(file_path)

    return jsonify({
      "transcription": transcription,
      "ai_response": response.choices[0].text.strip()
    })

  except Exception as e:
    print(f"Error: {str(e)}")
    return jsonify(error=str(e)), 500

if __name__ == "__main__":
  app.run(debug=True)
