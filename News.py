from flask import Flask, render_template, url_for, redirect, session, request
import psycopg2
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import json
import requests
from bs4 import BeautifulSoup
from authlib.integrations.flask_client import OAuth
nltk.download('vader_lexicon')

app = Flask(__name__)
app.secret_key = 'supersecret'

@app.route('/')
def index():
    return 'Congrechlation on render'

if __name__ == '__main__':
    app.run(debug=True)
