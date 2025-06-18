# chatbot_app.py

import streamlit as st
import json
import os
import re
import requests
import datetime
import subprocess
import sys
from io import BytesIO
import matplotlib.pyplot as plt

# === Ensure NLTK and matplotlib are installed ===

import nltk
from nltk.tokenize import word_tokenize

# Ensure punkt tokenizer is available
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')


from difflib import get_close_matches

# === Load Default Responses and Chat History ===
def load_data():
    if os.path.exists("chatbot_data.json"):
        with open("chatbot_data.json", "r") as f:
            return json.load(f)
    return {"history": [], "custom_responses": {}}

def save_data(data):
    with open("chatbot_data.json", "w") as f:
        json.dump(data, f, indent=4)

# === Default Responses ===
def get_default_responses():
    return {
        "hi": "Hello! How can I assist you?",
        "hello": "Hi there! What can I help you with?",
        "bye": "Goodbye! Come back soon.",
        "what is python": "Python is a versatile programming language used in many fields.",
        "how are you": "I'm a chatbot — always operational!",
        "what programming language are you learning?": "Python.",
        "where are you learning data science": "Sail Innovation Lab."
    }

# === Handle User Input ===
from nltk.tokenize import PunktSentenceTokenizer, word_tokenize
from difflib import get_close_matches

def generate_response(user_input, data, api_keys):
    text = user_input.lower().strip()

    # Manually tokenize using Punkt to avoid broken punkt_tab path issue
    tokenizer = PunktSentenceTokenizer()
    sentences = tokenizer.tokenize(text)
    tokens = []
    for sent in sentences:
        tokens.extend(word_tokenize(sent))

    matched = get_close_matches(
        text,
        list(data["custom_responses"].keys()) + list(get_default_responses().keys()),
        n=1,
        cutoff=0.6
    )

    if matched:
        if matched[0] in data["custom_responses"]:
            return data["custom_responses"][matched[0]]
        return get_default_responses()[matched[0]]

    # Keyword checks
    if "weather" in tokens:
        return get_weather(text, api_keys.get("weather"))
    elif "news" in tokens:
        return get_news(api_keys.get("news"))
    elif any(word in text for word in ["price", "bitcoin", "crypto"]):
        return get_crypto_price(text, api_keys.get("crypto"))
    elif any(word in text for word in ["stock", "shares", "company"]):
        return get_stock_price(text, api_keys.get("stock"))
    elif any(word in text for word in ["ronaldo", "match", "messi", "lebron", "haaland"]):
        return get_sports_info(text, api_keys.get("sports"))
    elif "wikipedia" in text or text.startswith("who") or text.startswith("what"):
        return get_wikipedia_summary(text)

    return "I'm not sure how to respond to that yet."


# === Weather API ===
def get_weather(text, key):
    if not key:
        return "No weather API key set."
    match = re.search(r"weather in ([a-zA-Z ]+)", text)
    city = match.group(1) if match else "London"
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={key}&units=metric"
    try:
        res = requests.get(url).json()
        if res.get("main"):
            temp = res["main"]["temp"]
            desc = res["weather"][0]["description"]
            return f"Weather in {city.title()}: {temp}°C, {desc}"
        return f"Could not retrieve weather for {city}."
    except Exception as e:
        return f"Weather lookup failed: {str(e)}"

# === News API ===
def get_news(key):
    if not key:
        return "No news API key set."
    url = f"https://newsapi.org/v2/top-headlines?country=us&apiKey={key}"
    try:
        res = requests.get(url).json()
        articles = res.get("articles", [])[:3]
        return "\n\n".join([f"- {a['title']} ({a['source']['name']})" for a in articles])
    except Exception as e:
        return f"News lookup failed: {str(e)}"

# === Wikipedia ===
def get_wikipedia_summary(query):
    try:
        res = requests.get(f"https://en.wikipedia.org/api/rest_v1/page/summary/{query.split()[-1]}").json()
        return res.get("extract", "Wikipedia article not found.")
    except:
        return "Wikipedia lookup failed."

# === Crypto ===
def get_crypto_price(text, key):
    if not key:
        return "No crypto API key set."
    match = re.search(r"\b(bitcoin|btc|eth|ethereum|doge)\b", text)
    symbol = match.group(1).upper() if match else "BTC"
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={symbol.lower()}&vs_currencies=usd"
    try:
        res = requests.get(url).json()
        price = res[symbol.lower()]["usd"]
        return f"Current price of {symbol}: ${price}"
    except:
        return "Crypto lookup failed."

# === Stocks ===
def get_stock_price(text, key):
    if not key:
        return "No stock API key set."
    match = re.search(r"stock (price )?of ([A-Za-z]+)", text)
    symbol = match.group(2).upper() if match else "AAPL"
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={key}"
    try:
        res = requests.get(url).json()
        price = res["Global Quote"]["05. price"]
        return f"Current price of {symbol}: ${price}"
    except:
        return "Stock lookup failed."

# === Sports ===
def get_sports_info(text, key):
    if not key:
        return "No sports API key set."
    return f"(Demo) Sports info for: {text}"

# === Streamlit App ===
st.set_page_config(page_title="ChatBot App", layout="centered")
st.title("Tatafo with AI 🗣️")

# === API Key Management ===
st.sidebar.title("🔑 API Key Setup")
api_keys = {}

def handle_api_keys():
    mode = st.sidebar.radio("Choose how to provide API keys:", ["Load from file", "Manual input", "Skip"])
    if mode == "Load from file":
        uploaded = st.sidebar.file_uploader("Upload .txt file with API keys (key=value per line)")
        if uploaded:
            content = uploaded.read().decode("utf-8").splitlines()
            for line in content:
                if "=" in line:
                    k, v = line.strip().split("=")
                    api_keys[k.strip()] = v.strip()
            st.sidebar.success("\u2705 API keys loaded from file.")
    elif mode == "Manual input":
        api_keys["weather"] = st.sidebar.text_input("Weather API Key")
        api_keys["news"] = st.sidebar.text_input("News API Key")
        api_keys["crypto"] = st.sidebar.text_input("Crypto API Key")
        api_keys["stock"] = st.sidebar.text_input("Stock API Key")
        api_keys["sports"] = st.sidebar.text_input("Sports API Key")

        if st.sidebar.button("Save Keys to .txt"):
            with open("api_keys.txt", "w") as f:
                for k, v in api_keys.items():
                    f.write(f"{k}={v}\n")
            st.sidebar.success("✅ Keys saved to api_keys.txt")

handle_api_keys()

# === Chat System ===
data = load_data()
user_input = st.text_input("You:")
if user_input:
    response = generate_response(user_input, data, api_keys)
    data["history"].append({"user": user_input, "bot": response})
    save_data(data)
    st.write(f"**Bot:** {response}")

# === Add Custom Response ===
st.sidebar.markdown("---")
st.sidebar.subheader("🤝 Add Custom Response")
new_key = st.sidebar.text_input("Trigger phrase")
new_resp = st.sidebar.text_area("Bot's response")
if st.sidebar.button("Add Response"):
    if new_key and new_resp:
        data["custom_responses"][new_key.lower()] = new_resp
        save_data(data)
        st.sidebar.success("Added!")

# === View/Reset History ===
if st.sidebar.button("❌ Clear Chat History"):
    data["history"] = []
    save_data(data)
    st.sidebar.success("Chat history cleared.")

if st.sidebar.checkbox("📓 Show Chat History"):
    st.sidebar.markdown("---")
    for entry in data["history"]:
        st.sidebar.write(f"**You:** {entry['user']}")
        st.sidebar.write(f"**Bot:** {entry['bot']}")
