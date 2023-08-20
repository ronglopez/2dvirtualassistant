# Import necessary libraries
import openai
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer

# Import settings
from personalities import AI_PERSONALITY
from config.settings import SENTIMENT_SCORES, MAX_LEVEL, MIN_LEVEL

def analyze_sentiment_vader(text):
  nltk.data.path.append('./resources/nltk_data')
  sia = SentimentIntensityAnalyzer()
  sentiment_score = sia.polarity_scores(text)
  compound_score = sentiment_score['compound']

  # Classify sentiment and intensity based on the compound score
  if compound_score >= 0.05:
    return "positive", compound_score
  elif compound_score <= -0.05:
    return "negative", -compound_score
  else:
    return "neutral", 0

# Sentiment analysis
# todo: Further testing required, sometimes will use other words and that will break the system. This NEEDS to be consistent
def analyze_sentiment(text):
  
  # Use OpenAI's model to predict sentiment
  response = openai.Completion.create(
    engine="text-davinci-002",
    prompt = f"I expect 1 word and 1 integer separated by a comma. First answer, classify the sentiment of the following text (Use ONLY 1 word in lowercase and only these words: positive, negative, or neutral). Second answer, rate the intensity of the following text on a scale from 1 to 5: '{text}'",
    temperature=0.1,
    max_tokens=10,
    top_p=1,
    frequency_penalty=0,
    presence_penalty=0
  )

  # Response should give a sentiment and an number
  response_text = response.choices[0].text.strip()

  return response_text

# Update AI's Mood depending on sentiment analysis
def update_ai_mood(user_sentiment, ai_mood, accumulated_sentiment):

  # Get sentiment and intensity
  sentiment, intensity = user_sentiment

  # Get sentiment score 
  base_score = SENTIMENT_SCORES[sentiment]

  print(f"User sentiment was: {sentiment}, and scored: {base_score}")
  print(f"Intensity level was: {intensity}")

  # Adjust score based on intensity 
  adjusted_score = base_score * intensity
  print(f"Sentiment score was: {adjusted_score}")

  # Update accumulated sentiment
  accumulated_sentiment += adjusted_score

  # Ensure accumulated sentiment is within max and min levels
  accumulated_sentiment = max(MIN_LEVEL, min(accumulated_sentiment, MAX_LEVEL))
  print(f"Total score is at: {accumulated_sentiment}")

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
