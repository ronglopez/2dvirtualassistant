# load_settings.py
import json

def load_settings():
  with open('config/settings.json', 'r') as f:
    settings = json.load(f)
  return settings

# Now load the settings into a variable
settings = load_settings()
