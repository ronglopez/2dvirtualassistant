# # # # #
# To use this file, you must run `python generate_pinecone_embeddings.py` in terminal in the directory that this file is in
# This file is not used within the app, instead, it is used to generate embeddings and store them in our Pinecone index
# Uncomment the code that you need to use
# # # # #

# Import necessary libraries
import os
import openai
import pinecone
from dotenv import load_dotenv
from tqdm.auto import tqdm

# Import settings variables
from ..config.load_settings import settings

# Import settings variables
OPENAI_EMBEDDING_MODEL = settings['AI_EMBEDDING_SETTINGS']['OPENAI_EMBEDDING_MODEL']
PINECONE_INDEX_NAME = settings['AI_EMBEDDING_SETTINGS']['PINECONE_INDEX_NAME']

# Load environment variables
load_dotenv("../config/.env")

# Initialize API keys
openai.api_key = os.environ.get("OPENAI_EMBEDDINGS_API_KEY")
pinecone_api_key = os.environ.get("PINECONE_API_KEY")
pinecone_environment = os.environ.get("PINECONE_API_ENVIRONMENT")

# Initialize Pinecone
pinecone.init(api_key=pinecone_api_key, environment=pinecone_environment)

# Connect to index
index = pinecone.Index(PINECONE_INDEX_NAME)

# # # # #
# Generate and store embeddings
# # # # #

## Read the embeddings.txt file
## This file contains the data we want to embed
# with open("embeddings.txt", "r") as file:
#   lines = file.readlines()

# for i, line in enumerate(tqdm(lines)):

#   # Create embeddings
#   res = openai.Embedding.create(
#     input=[line],
#     engine=OPENAI_EMBEDDING_MODEL
#   )

#   # Extract embeddings to a list
#   embeds = [record['embedding'] for record in res['data']]

#   # Prep metadata and upsert batch
#   meta = [{'content': line}]
#   to_upsert = [(str(i), embeds[0], meta[0])]  # Each record is a tuple of (id, vector, metadata)

#   # Upsert to Pinecone
#   index.upsert(vectors=list(to_upsert))

# # # # #

# # # # #
# Sample Query function
# # # # #

# def search_query(query):
#   xq = res = openai.Embedding.create(
#     input=[query],
#     engine=OPENAI_EMBEDDING_MODEL
#   )['data'][0]['embedding']
#   res = index.query([xq], top_k=2, include_metadata=True)
#   return res['matches']

# matches = search_query("What's your easter egg?")
# for match in matches:
#   print(f"{match['score']:.2f}: {match['metadata']}")

# # # # #

# # # # #
# View index stats
# # # # #
# print(index.describe_index_stats())

# # # # #

# # # # #
# Sample view data by id and output to a txt file
# # # # #
# with open("output.txt", "w") as f:
#   f.write(str(index.fetch(ids=["0"])))

# # # # #

# # # # #
# Sample view update data by id
# # # # #
# index.update(id="0", set_metadata={"content": "Ronald Lopez is a Product Designer, a father, and a self-taught developer."})
# print(index.fetch(["0"]))

# # # # #

# # # # #
# Delete data by id
# # # # #
# index.delete(ids=["0", "1"])

# # # # #