from flask import Flask, render_template, request, session, redirect, url_for
import psycopg2
import os
from nltk.tokenize import sent_tokenize, word_tokenize
import nltk
from bs4 import BeautifulSoup
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import re
import json
from authlib.integrations.flask_client import OAuth

app = Flask(__name__, static_folder='data')
app.config['SECRET_KEY'] = "THIS SHOULD BE SECRET"
app.config['GITHUB_CLIENT_ID'] = "992ca9ab81fae0231b83"
app.config['GITHUB_CLIENT_SECRET'] = "a0c7e13b2dfdb91e32c700563eed8420f6594e2b"
github_admin_usernames = [ "atmabodha","rajat-malvi"]

DATABASE_URL = os.getenv('DATABASE_URL', "postgres://dhp2024_44yk_user:hYblUsnTd53xOGdkVu0d70jAP5LR1SBC@dpg-cnlhmc0l6cac73ef0vmg-a.oregon-postgres.render.com/dhp2024_44yk")

oauth = OAuth(app)

# Register GitHub OAuth
github = oauth.register(
    name='github',
    client_id=app.config["GITHUB_CLIENT_ID"],
    client_secret=app.config["GITHUB_CLIENT_SECRET"],
    access_token_url='https://github.com/login/oauth/access_token',
    access_token_params=None,
    authorize_url='https://github.com/login/oauth/authorize',
    authorize_params=None,
    api_base_url='https://api.github.com/',
    client_kwargs={'scope': 'user:email'},
)

def connect_to_db():
    '''Function to connect to the database'''
    conn = psycopg2.connect(DATABASE_URL)
    return conn

def create_table():
    '''Create a table if not exist'''
    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute("""
            CREATE TABLE IF NOT EXISTS news(
                id SERIAL PRIMARY KEY,
                name VARCHAR(1000),
                nowords VARCHAR(100),
                nosentence VARCHAR(100),
                nopostag VARCHAR(1000),
                articlekey VARCHAR(10000),
                pera TEXT,
                author VARCHAR(500),
                link VARCHAR(10000) NOT NULL
            )
        """)
    conn.commit()

def getsoup(s):
    '''Function to return soup(main)'''
    URL = f'{s}'
    page = requests.get(URL)
    soup = BeautifulSoup(page.content, "html.parser")
    return soup

def reax(s):
    '''Regular expression function to clean the text in some specific pattern'''
    raw_html = str(s)
    cleantext = re.sub(r'<.*?>', '', raw_html)
    return cleantext

def thd(s):
    '''Function to scrape news from www.thehindu.com'''
    soup = getsoup(s)
    artical = soup.find('div', class_='articlebodycontent')
    lst = artical.find_all('p')

    cleaned_news = []
    for tag in lst:
        if 'share' not in tag.get('class', []) and 'related-topics-list' not in tag.get('class', []) and 'comments' not in tag.get('class', []):
            cleaned_news.append(tag.get_text().strip())

    pera = ''
    for news in cleaned_news:
        pera += " " + news
    return pera.strip()

def thddict(l):
    '''Function to return important details extracted from the article'''
    soup = getsoup(l)
    string = soup.script.get_text().strip()
    dict1 = json.loads(string[55:-2].replace('\n', "").replace('// when available', "").replace("'", '"'))
    dict2 = dict1['pageDetails']
    return dict2

def toi(s):
    '''Function to scrape news from Times of India'''
    soup = getsoup(s)
    scriptlist = soup.find_all('script')
    dict1 = json.loads(scriptlist[-2].get_text())
    return dict1

def sentence_func(s):
    '''Function to return a list of sentences'''
    sentence = sent_tokenize(s)
    return len(sentence)

def word_func(s):
    '''Function to return a list of words without using punctuation'''
    lst = [',', '.', '?', '!']
    word_list = word_tokenize(s)
    count = 0
    for i in word_list:
        if i not in lst:
            count += 1
    return count

def upos1(s):
    '''Function to return POS tags'''
    words = word_tokenize(s)
    lst = nltk.pos_tag(words, tagset='universal')
    dict1 = {}
    for i in lst:
        if i[1] not in dict1:
            dict1[i[1]] = 1
        else:
            dict1[i[1]] += 1
    dict1 = json.dumps(dict1)
    return dict1

def classify_sentiment(text):
    '''Function to analyze the sentiment of a paragraph'''
    analyzer = SentimentIntensityAnalyzer()
    scores = analyzer.polarity_scores(text)
    if scores['compound'] > 0.05:
        return True
    elif scores['compound'] < -0.05:
        return False
    else:
        return "neutral"

def articleTags(s):
    '''Function to split the string'''
    if '|' in s:
        lst = s.split('|')
    elif ',' in s:
        lst = s.split(',')
    return lst

def textCleaner(s):
    '''Function to clean text'''
    new = re.sub(r'[0-9]+', ' ', s)
    res = re.sub(r'([a-z])([A-Z])', r'\1 \2', new)
    res = re.sub(r'[^\w\s]', '', res)
    res = re.sub(r'\s+', ' ', res)
    return res

@app.route("/", methods=('GET', 'POST'))
def portal():
    conn = connect_to_db()
    cur = conn.cursor()
    try:
        sentence = '0'
        words = '0'
        upos = ''
        link = ''
        pera = ''
        heading = 'Today Headline'
        articleTag = ''
        istrue = 'neutral'
        option = ''
        name = ''
        authename = 'Writer'
        dictmain = {}
        
        if request.method == "POST":
            option = request.form.get('news')
            name = request.form.get('user')
            if option == 'The_Hindu':
                link = request.form['link']
                pera = thd(link)
                new_dict = thddict(link)
                articleTag = articleTags(new_dict['articleTags'])
                heading = new_dict['headline']
                authename = new_dict['authorName']
                cur.execute('insert into news(name,nowords,nosentence,nopostag,articlekey,pera,author,link) values(%s,%s,%s,%s,%s,%s,%s,%s)', (name, word_func(pera), sentence_func(pera), upos1(pera), new_dict['articleTags'], pera, new_dict['authorName'], link))
                conn.commit()
                
            elif option == 'toi':
                link = request.form['link']
                new_dict = toi(link)
                pera = textCleaner(new_dict['articleBody'])
                heading = new_dict['headline']
                articleTag = articleTags(new_dict['keywords'])
                authename = new_dict['author']['name']
                cur.execute('insert into news(name,nowords,nosentence,nopostag,articlekey,pera,author,link) values(%s,%s,%s,%s,%s,%s,%s,%s)', (name, word_func(pera), sentence_func(pera), upos1(pera), new_dict['keywords'], pera, authename, link))
                conn.commit()

            dictmain['sentence'] = sentence_func(pera)
            dictmain['words'] = word_func(pera)
            dictmain['upos'] = upos1(pera)
            dictmain['istrue'] = classify_sentiment(pera)
            dictmain['heading'] = heading
            dictmain['articleTag'] = articleTag
            dictmain['authername'] = authename
            conn.close()

        return render_template('News.html', dictmain=dictmain, pera=pera, name=name)
    except Exception as e:
        return render_template('News.html', dictmain=dictmain, name=name)

@app.route('/login/github')
def github_login():
    github = oauth.create_client('github')
    redirect_uri = url_for('github_authorize', _external=True)
    return github.authorize_redirect(redirect_uri)

@app.route('/login/github/authorize')
def github_authorize():
    conn = connect_to_db()
    cur = conn.cursor()
    try:
        github = oauth.create_client('github')
        token = github.authorize_access_token()
        session['github_token'] = token
        resp = github.get('user').json()
        logged_in_username = resp.get('login')
        if logged_in_username in github_admin_usernames:
            cur.execute('select * from news')
            data = cur.fetchall()
            conn.close()
            return render_template("Searchhistory.html", lst=data)
        else:
            return render_template("News.html", dictmain={})
    except:
        return render_template("News.html", dictmain={})

@app.route('/logout/github')
def github_logout():
    session.pop('github_token', None)
    return redirect(url_for('portal'))

if __name__ == '__main__':
    create_table()
    app.run(debug=True)
