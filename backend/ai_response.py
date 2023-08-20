# Import necessary libraries
from pathlib import Path
import json
import time

# Import LangChain
from langchain import PromptTemplate, LLMChain
from langchain.memory import ConversationBufferWindowMemory, ChatMessageHistory
from langchain.chat_models import ChatOpenAI
from langchain.schema import messages_from_dict, messages_to_dict

# Import utility files
from utils import clear_messages_file, split_text, speak_sentences, stream_audio
from moderation import moderate_output

# Import settings
from personalities import AI_PERSONALITY
from config.settings import MAX_MESSAGES, accumulated_sentiment, ai_mood, TEMPERATURE, OPENAI_MODEL, MAX_TOKENS, ELABS_STREAM

# Import sentiment analysis
from sentiment_analysis import analyze_sentiment, update_ai_mood, analyze_sentiment_vader

# Function to generate AI response based on user input
def get_ai_response(human_input):

  # Start the ai response monitoring timer
  start_response_time = time.time()

  # Sentiment Analysis of User Input
  global ai_mood, accumulated_sentiment

  # Select using VADER or non VADER analysis
  # user_sentiment = analyze_sentiment(human_input)
  user_sentiment = analyze_sentiment_vader(human_input)
  
  print(user_sentiment)

  # Update AI's mood based on user sentiment
  ai_mood, accumulated_sentiment = update_ai_mood(user_sentiment, ai_mood, accumulated_sentiment)

  # Initialize LangChain with the specified model and parameters
  llm = ChatOpenAI(temperature=TEMPERATURE, model_name=OPENAI_MODEL, max_tokens=MAX_TOKENS)

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

  try:
    # Get the AI response
    ai_response = conversation_bufw.predict(human_input=human_input)

    # Moderate AI response
    ai_response = moderate_output(ai_response)

    # End the ai response monitoring timer
    end_response_time = time.time()  
    ai_response_time = end_response_time - start_response_time
    print(f"AI Response Time: {ai_response_time:.2f} seconds")

    # Save messages to memory file
    conversation_messages = conversation_bufw.memory.chat_memory.messages

    messages = messages_to_dict(conversation_messages)

    with file_path.open("w") as f:
      json.dump(messages, f, indent=2)

  # Error handling for exceeding OpenAI max token use
  except Exception as e:
    print("An error occurred, possibly due to token limit. Clearing message history and restarting.")

    # Clear the message history
    clear_messages_file() 
    return "I'm sorry, I encountered an error. Please try again."

  # Convert the AI's text response into audio using ElevenLabs
  # Start the text-to-speech monitoring timer
  start_text_to_speech_time = time.time()

  # ElevenLabs text-to-speech functions
  if ELABS_STREAM:
    # Use ElevenLabs streaming method for text-to-speech
    stream_audio(ai_response)
  else:
    # Use ElevenLabs sentence-by-sentence method for text-to-speech
    sentences = split_text(ai_response)
    speak_sentences(sentences)

  # End the text-to-speech monitoring timer
  end_text_to_speech_time = time.time()
  text_to_speech_time = end_text_to_speech_time - start_text_to_speech_time
  print(f"Text-to-Speech Generation Time: {text_to_speech_time:.2f} seconds")

  # Monitor JSON memory file
  print(f"Number of messages before writing to JSON: {len(messages)}")
  
  return ai_response
