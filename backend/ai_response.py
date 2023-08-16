from pathlib import Path
import json

# Import LangChain
from langchain import PromptTemplate, LLMChain
from langchain.memory import ConversationBufferWindowMemory, ChatMessageHistory
from langchain.chat_models import ChatOpenAI
from langchain.schema import messages_from_dict, messages_to_dict

# Import ElevenLabs text-to-speech
from elevenlabs import generate, play

# Import settings
from personalities import AI_PERSONALITY
from config.settings import MAX_MESSAGES, accumulated_sentiment, ai_mood, TEMPERATURE, MODEL_ENGINE, MAX_TOKENS

# Import sentiment analysis
from sentiment_analysis import analyze_sentiment, update_ai_mood

# Function to generate AI response based on user input
def get_ai_response(human_input):

  # Sentiment Analysis of User Input
  global ai_mood, accumulated_sentiment
  user_sentiment = analyze_sentiment(human_input)

  # Update AI's mood based on user sentiment
  ai_mood, accumulated_sentiment = update_ai_mood(user_sentiment, ai_mood, accumulated_sentiment)

  # Initialize LangChain with the specified model and parameters
  llm = ChatOpenAI(temperature=TEMPERATURE, model_name=MODEL_ENGINE, max_tokens=MAX_TOKENS)

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
  file_path = Path("data") / "messages.json"
  
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
  prompt = PromptTemplate(input_variables=["history", "human_input"], template=system_template + f"You are will emulate feeling {ai_mood}" + template)

  conversation_bufw = LLMChain(   # - todo: This should actually be ConversationChain, but bug seems to be breaking at this moment
    llm=llm,
    prompt=prompt,
    memory=ConversationBufferWindowMemory(chat_memory=history, k=MAX_MESSAGES),
    verbose=True,
  )

  ai_response = conversation_bufw.predict(human_input=human_input)

  conversation_messages = conversation_bufw.memory.chat_memory.messages

  messages = messages_to_dict(conversation_messages)

  with file_path.open("w") as f:
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
