# app/nlp_utils.py

import requests
from bs4 import BeautifulSoup
from transformers import pipeline

summarizer = pipeline(
    "summarization",
    model="facebook/bart-large-cnn",
    tokenizer="facebook/bart-large-cnn",
)

def scrape_and_summarise(url: str) -> str:
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        text = " ".join([p.get_text() for p in soup.find_all("p")])
        if len(text) < 300:
            return "Insufficient content on the provided URL to generate a contextual summary."
        summary = summarizer(text[:4000], max_length=180, min_length=60, do_sample=False)
        return summary[0]["summary_text"]
    except Exception as e:
        return f"Error processing URL: {e}"
