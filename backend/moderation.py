# Import necessary libraries
import openai

# Import settings
from personalities import AI_PERSONALITY
from better_profanity import profanity
from config.settings import MOD_REPLACE_RESPONSE

# Optionally, you can load a custom profanity wordlist
# profanity.load_censor_words(["custom_word1", "custom_word2"])

# Function to filter and replace responses with profanity
def contains_profanity(text):
  return profanity.contains_profanity(text)

# Function to filter profane text
def censor_profanity(text):
  return profanity.censor(text, '-')

# Moderation function
def moderate_output(ai_response):
  response = openai.Moderation.create(
    input=ai_response
  )

  # Uncomment this code block to simulate moderation
  # response = {
  #   "results": [
  #     {
  #       "flagged": True,
  #       "categories": {
  #         "sexual": True,
  #         "hate": False,
  #         "harassment": False,
  #         "self-harm": False,
  #         "sexual/minors": False,
  #         "hate/threatening": False,
  #         "violence/graphic": False,
  #         "self-harm/intent": False,
  #         "self-harm/instructions": False,
  #         "harassment/threatening": False,
  #         "violence": False,
  #       }
  #     }
  #   ]
  # }

  output = response["results"][0]
  flagged = output["flagged"]
  categories = output["categories"]

  if flagged:

    # Show the violation in terminal
    print(ai_response)
    print("Content violates OpenAI's usage policies.")
    print("Violated categories:", categories)

    # Craft new response based on Personality
    moderation = AI_PERSONALITY["ai_moderation"]
    
    # Customize the response based on the violated category
    if categories["sexual"]:
      ai_response = moderation["sexual"]
    elif categories["hate"]:
      ai_response = moderation["hate"]
    elif categories["harassment"]:
      ai_response = moderation["harassment"]
    elif categories["self-harm"]:
      ai_response = moderation["self-harm"]
    elif categories["sexual/minors"]:
      ai_response = moderation["sexual/minors"]
    elif categories["hate/threatening"]:
      ai_response = moderation["hate/threatening"]
    elif categories["violence/graphic"]:
      ai_response = moderation["violence/graphic"]
    elif categories["self-harm/intent"]:
      ai_response = moderation["self-harm/intent"]
    elif categories["self-harm/instructions"]:
      ai_response = moderation["self-harm/instructions"]
    elif categories["harassment/threatening"]:
      ai_response = moderation["harassment/threatening"]
    elif categories["violence"]:
      ai_response = moderation["violence"]
      
  else:
    print("Content complies with OpenAI's usage policies.")

  # Uncomment this code block to simulate profanity
  # ai_response = "what the fuck is that? WTF!"

  # Check for profanity using better-profanity
  if MOD_REPLACE_RESPONSE:

    # Check for profanity using better-profanity
    if contains_profanity(ai_response):
      ai_response = AI_PERSONALITY["profanity_moderation"]
  
  else:

    # Censor profanity using better-profanity
    ai_response = censor_profanity(ai_response)
  
  return ai_response
