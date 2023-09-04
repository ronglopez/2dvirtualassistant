# Import necessary libraries
import os
import openai
import pinecone
from dotenv import load_dotenv

# Load environment variables
load_dotenv("../config/.env")

# Initialize API keys
openai.api_key = os.environ.get("OPENAI_EMBEDDINGS_API_KEY")
pinecone_api_key = os.environ.get("PINECONE_API_KEY")
pinecone_environment = os.environ.get("PINECONE_API_ENVIRONMENT")

# Initialize Pinecone
pinecone.init(api_key=pinecone_api_key, environment=pinecone_environment)

# Set variables
OPENAI_EMBEDDING_MODEL = "text-embedding-ada-002"
PINECONE_INDEX_NAME = "openai-embeddings"

# Connect to index
index = pinecone.Index(PINECONE_INDEX_NAME)

# Create embedding for query
def search_query(query):
  xq = res = openai.Embedding.create(
    input=[query],
    engine=OPENAI_EMBEDDING_MODEL
  )['data'][0]['embedding']
  
  res = index.query([xq], top_k=2, include_metadata=True)
  
  return res['matches']
