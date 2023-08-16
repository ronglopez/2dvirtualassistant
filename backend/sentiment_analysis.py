import openai
from personalities import AI_PERSONALITY
from config.settings import SENTIMENT_SCORES, MAX_LEVEL, MIN_LEVEL

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
def update_ai_mood(user_sentiment, ai_mood, accumulated_sentiment):
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

  return ai_mood, accumulated_sentiment
