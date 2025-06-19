import streamlit as st
import json
import os
import re
import requests
import datetime
from io import BytesIO
import plotly.graph_objs as go
import pandas as pd
from langdetect import detect
import spacy

# Load spaCy models
nlp_en = spacy.load("en_core_web_sm")

def extract_named_entities_via_api(text):
    try:
        lang = detect(text)
        doc = nlp_en(text) if lang == "en" else nlp_multi(text)
        return [ent.text for ent in doc.ents]
    except:
        return []

def load_data():
    if os.path.exists("chatbot_data.json"):
        with open("chatbot_data.json", "r") as f:
            return json.load(f)
    return {"history": [], "custom_responses": {}}

def save_data(data):
    with open("chatbot_data.json", "w") as f:
        json.dump(data, f, indent=4)

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

def get_weather(text, key):
    if not key:
        return "No weather API key set."
    match = re.search(r"weather in ([a-zA-Z ]+)", text)
    city = match.group(1) if match else "London"
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={key}&units=metric"
    try:
        res = requests.get(url).json()
        temp = res["main"]["temp"]
        desc = res["weather"][0]["description"]
        return f"Weather in {city.title()}: {temp}°C, {desc}"
    except:
        return f"Could not retrieve weather for {city}."

def get_news(key):
    if not key:
        return "No news API key set."
    url = f"https://newsapi.org/v2/top-headlines?country=us&apiKey={key}"
    try:
        res = requests.get(url).json()
        articles = res.get("articles", [])[:3]
        return "\n\n".join([f"- {a['title']} ({a['source']['name']})" for a in articles])
    except:
        return "News lookup failed."

def get_wikipedia_summary(query):
    try:
        query = re.sub(r"^(who|what|where|when|how)( is| was| are| does| do| did)?", "", query.lower()).strip()
        query = query if query else "Python (programming language)"
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{query.replace(' ', '_')}"
        res = requests.get(url).json()
        return res["extract"] if "extract" in res else "Wikipedia summary not found."
    except:
        return "Wikipedia lookup failed."

def get_crypto_price(text, key):
    if not key:
        return "No crypto API key set."
    match = re.search(r"\b(bitcoin|btc|eth|ethereum|doge)\b", text)
    symbol = match.group(1).upper() if match else "BTC"
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={symbol.lower()}&vs_currencies=usd"
    try:
        res = requests.get(url).json()
        return f"Current price of {symbol}: ${res[symbol.lower()]['usd']}"
    except:
        return "Crypto lookup failed."

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

def get_sports_info(text, key):
    if not key:
        return "No sports API key set."
    return f"(Demo) Sports info for: {text}"

def handle_csv_upload():
    uploaded_file = st.sidebar.file_uploader("Upload stock CSV", type="csv")
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        st.success("CSV uploaded and loaded.")
        return df
    if st.sidebar.button("Fetch Sample CSV"):
        url = "https://query1.finance.yahoo.com/v7/finance/download/AAPL?period1=1663372800&period2=1694908800&interval=1d&events=history"
        try:
            res = requests.get(url)
            df = pd.read_csv(BytesIO(res.content))
            st.success("Sample CSV fetched.")
            return df
        except:
            st.error("Sample CSV fetch failed.")
    return None

def plot_stock_chart(df):
    st.subheader("Stock Price Chart")
    if df is not None:
        start = st.date_input("Start Date", value=pd.to_datetime(df['Date'].min()))
        end = st.date_input("End Date", value=pd.to_datetime(df['Date'].max()))
        if start <= end:
            mask = (pd.to_datetime(df['Date']) >= start) & (pd.to_datetime(df['Date']) <= end)
            filtered = df.loc[mask]
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=filtered['Date'], y=filtered['Close'], mode='lines', name='Close Price'))
            fig.update_layout(title="Stock Price Over Time", xaxis_title="Date", yaxis_title="Close Price")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Start date must be before end date.")

from difflib import get_close_matches

def generate_response(user_input, data, api_keys):
    text = user_input.lower().strip()
    entities = extract_named_entities_via_api(user_input)
    doc = nlp_en(text)
    tokens = [token.text.lower() for token in doc]

    matched = get_close_matches(text, list(data["custom_responses"]) + list(get_default_responses()), n=1, cutoff=0.6)
    if matched:
        return data["custom_responses"].get(matched[0], get_default_responses()[matched[0]])

    if "weather" in tokens:
        return get_weather(text, api_keys.get("weather"))
    elif "news" in tokens:
        return get_news(api_keys.get("news"))
    elif any(w in tokens for w in ["price", "crypto", "bitcoin"]):
        return get_crypto_price(text, api_keys.get("crypto"))
    elif any(w in tokens for w in ["stock", "shares", "company"]):
        return get_stock_price(text, api_keys.get("stock"))
    elif any(w in tokens for w in ["ronaldo", "messi", "match", "haaland", "lebron"]):
        return get_sports_info(text, api_keys.get("sports"))

    return get_wikipedia_summary(entities[0] if entities else user_input)

def main():
    st.set_page_config(page_title="ChatBot App", layout="centered")
    st.title("Tatafo with AI 🗣️")
    st.sidebar.title("🔐 API Key Input")

    data = load_data()
    api_keys = {}

    show_api_input = st.sidebar.button("API KEY Input")
    if show_api_input:
        mode = st.sidebar.radio("Provide API keys:", ["Load from file", "Manual input", "Skip"])
        if mode == "Load from file":
            uploaded = st.sidebar.file_uploader("Upload .txt with API keys")
            if uploaded:
                for line in uploaded.read().decode("utf-8").splitlines():
                    if "=" in line:
                        k, v = line.strip().split("=")
                        api_keys[k.strip()] = v.strip()
                st.sidebar.success("✅ API keys loaded.")
        elif mode == "Manual input":
            for key in ["weather", "news", "crypto", "stock", "sports"]:
                api_keys[key] = st.sidebar.text_input(f"{key.title()} API Key")
            if st.sidebar.button("Save to .txt"):
                with open("api_keys.txt", "w") as f:
                    for k, v in api_keys.items():
                        f.write(f"{k}={v}\n")
                st.sidebar.success("Saved to api_keys.txt")
    elif os.path.exists("api_keys.txt"):
        with open("api_keys.txt") as f:
            for line in f:
                if "=" in line:
                    k, v = line.strip().split("=")
                    api_keys[k.strip()] = v.strip()

    user_input = st.text_input("You:")
    if user_input:
        response = generate_response(user_input, data, api_keys)
        data["history"].append({"user": user_input, "bot": response})
        save_data(data)
        st.write(f"**Bot:** {response}")

    st.sidebar.markdown("---")
    st.sidebar.subheader("➕ Add Custom Response")
    new_key = st.sidebar.text_input("Trigger")
    new_resp = st.sidebar.text_area("Bot Response")
    if st.sidebar.button("Add Response"):
        if new_key and new_resp:
            data["custom_responses"][new_key.lower()] = new_resp
            save_data(data)
            st.sidebar.success("Custom response added!")

    if st.sidebar.button("🗑️ Clear Chat History"):
        data["history"] = []
        save_data(data)
        st.sidebar.success("Chat history cleared.")

    if st.sidebar.checkbox("📓 Show Chat History"):
        for entry in data["history"]:
            st.sidebar.write(f"**You:** {entry['user']}")
            st.sidebar.write(f"**Bot:** {entry['bot']}")

    df_stock = handle_csv_upload()
    if df_stock is not None:
        plot_stock_chart(df_stock)

if __name__ == "__main__":
    main()

