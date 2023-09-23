# Import necessary libraries
import os
import logging
import requests
import tempfile
import base64
from transformers import pipeline
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv("config/.env")

# Initialize the Hugging Face API key from the environment variable
hface_api_key = os.environ.get("HUGGINGFACEHUB_API_TOKEN")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

API_URL = "https://api-inference.huggingface.co/models/Salesforce/blip-image-captioning-large"
headers = {"Authorization": f"Bearer {hface_api_key}"}

# Function to check if the file has an allowed extension
def allowed_file(filename):

  # Allowed file types for image upload
  ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

  return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def upload_image(file_bytes, filename):
  
  # Check if the file bytes are present
  if not file_bytes:
    return None, None
  
  # Decode base64 to bytes
  file_bytes = base64.b64decode(file_bytes)
  
  # Check if a filename is provided
  if not filename:
    return None, "No selected file"
    
  # Check for allowed file extensions
  if allowed_file(filename):

    # Extract the file extension from the filename
    file_extension = filename.rsplit('.', 1)[1].lower()

    # Create a temporary file with the same extension
    with tempfile.NamedTemporaryFile(suffix=f".{file_extension}", delete=False) as temp_file:
      temp_file.write(file_bytes)
      temp_file_path = temp_file.name

    # Process the image here
    image_description = image2text(temp_file_path)

    # Remove the temporary image file
    os.remove(temp_file_path)

    return image_description, None

  else:
    return None, "File type not allowed"

# Function to get image description
def image2text(filename):
  try:

    # Read uploaded file
    with open(filename, "rb") as f:
      data = f.read()

    # Get response from image-to-text model
    response = requests.post(API_URL, headers=headers, data=data)

  except Exception as e:
    logging.error(f"An error occurred while using Image-To-Text model: {e}")

  try:
    return response.json()[0]['generated_text']
  
  except KeyError:
    logging.error(f"KeyError: The key does not exist in the JSON response.")
    return "Error: Could not generate text from image."
