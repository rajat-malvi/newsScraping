from flask import Flask, render_template, url_for, redirect, session,request
import psycopg2 
from nltk import *
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
# nltk.download('vader_lexicon')
import json
import requests
# from urllib import request
import re
from bs4 import BeautifulSoup
from authlib.integrations.flask_client import OAuth


app=Flask(__name__,static_folder='data')

# oAuth acount
oauth = OAuth(app)
# oautherized id
app.config['SECRET_KEY'] = "THIS SHOULD BE SECRET"
app.config['GITHUB_CLIENT_ID'] = "992ca9ab81fae0231b83"
app.config['GITHUB_CLIENT_SECRET'] = "a0c7e13b2dfdb91e32c700563eed8420f6594e2b"

# registration id 
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


# backend (psycopg2)
def connect_to_db():
    conn=psycopg2.connect(
        host='localhost',  database='dhp2024', user='postgres', password='rajat')
    return conn

conn=connect_to_db()
cursor = conn.cursor()

cursor.execute("""
        create table if not exists news(
            id serial primary key,
            heading varchar(100),
            nowords varchar(100),
            nosentence varchar(100),
            nopostag varchar(1000),
            articlekey varchar(10000),
            author varchar(500),
            link varchar(10000) not null
        )
    """)
conn.commit()


# ---------------------------------------------------------------------------------------------------------------------------------------


# bs4 code
def getsoup(s):
    URL=f'{s}'
    page=requests.get(URL)
    soup=BeautifulSoup(page.content,"html.parser")
    return soup

def reax(s):
    raw_html=str(s)
    cleantext=re.sub(r'<.*?>','',raw_html)
    return cleantext

# www.thehindu.com
def thd(s):
    soup=getsoup(s)
    # for purely pera
    artical = soup.find('div', class_='articlebodycontent')
    lst = artical.find_all('p')

    cleaned_news = []
    for tag in lst:
        if 'share' not in tag.get('class', []) and 'related-topics-list' not in tag.get('class', []) and 'comments' not in tag.get('class', []):
            cleaned_news.append(tag.get_text().strip())
    pera=''
    for news in cleaned_news:
        pera+=" " + news
    return pera.strip()

def thddict(l):
    soup=getsoup(l)
    string=soup.script.get_text().strip()
    dict1=json.loads(string[55:-2].replace('\n',"").replace('// when available',"").replace("'",'"'))
    dict2=dict1['pageDetails']
    return dict2

# TOI
def toi(s):
    # dict return
    soup=getsoup(s)
    scriptlist=soup.find_all('script')    
    dict1=json.loads(scriptlist[-2].get_text())
    return dict1

# ---------------------------------------------------------------------------------------------------------------------------------------

# NLTK
def sentence_func(s):
    sentence= sent_tokenize(s) 
    return len(sentence)

def word_func(s):
    lst=[',','.','?','!']
    word_list=word_tokenize(s)
    count=0
    for i in word_list:
        if i not in lst:
            count+=1   
    return count

# def s_word(s):
#     lst=nltk.corpus.stopwords.words('english')
#     count=0
#     word_list=word_tokenize(s)
#     for i in word_list:
#         if i in lst:
#             count+=1
#     return count

def upos1(s):
    # it tell about noun, verb.
    words=word_tokenize(s)
    lst = nltk.pos_tag(words,tagset='universal') # in this list we have tuple that indicate word is verb, noun or somthing else
    dict1={}
    for i in lst:
        if i[1] not in dict1:
            dict1[i[1]]=1
        else:
            dict1[i[1]]+=1
    # hear it convert dict to string format
    dict1=json.dumps(dict1)
    return dict1

# ----------------------------------------------------------------------------------------------------------------------------------

# other stuff
def classify_sentiment(text):
  """
  Analyzes the sentiment of a paragraph and returns "positive", "negative", or "neutral".

  Args:
      text: A string containing a paragraph of text.

  Returns:
      A string: "positive", "negative", or "neutral", indicating the sentiment of the text.
  """
  # Use VADER sentiment analyzer
  analyzer = SentimentIntensityAnalyzer()
  # scores is a dict   
  scores = analyzer.polarity_scores(text)
  # Determine sentiment based on compound score
  if scores['compound'] > 0.05:
    return True
  elif scores['compound'] < -0.05:
    return False
  else:
    return "neutral"


# split the string
def articleTags(s):
    if '|' in s:
        lst=s.split('|') 
    elif ',' in s:
        lst=s.split(',')
    return lst

# text cleaner 
def textCleaner(s):
    new=re.sub(r'[0-9]+',' ',s)
    res = re.sub(r'([a-z])([A-Z])', r'\1 \2', new)
    res=re.sub(r'[^\w\s]','',res)
    res=re.sub(r'\s+',' ',res)
    return res


@app.route("/",methods=('GET','POST'))
def portal():
    # connection
    conn=connect_to_db()
    cur=conn.cursor()
    try:
        sentence='0'
        words='0'
        upos=''
        link=''
        pera=''
        heading='Today Headline'
        articleTag=''
        istrue='neutral'
        option=''
        name=''
        authename='Writer'
        dictmain={}
        news=''
        
        if request.method=="POST":
            option=request.form.get('news')
            name=request.form.get('user')                
            if option=='The_Hindu':
                link=request.form['link']
                pera=thd(link)
                new_dict=thddict(link)
                articleTag=articleTags(new_dict['articleTags'])
                heading=new_dict['headline']
                authename=new_dict['authorName']
                news='The Hindu'
                # store in data base
                cur.execute('insert into news(heading,nowords,nosentence,nopostag,articlekey,author,link) values(%s,%s,%s,%s,%s,%s,%s)',(news,word_func(pera),sentence_func(pera),upos1(pera),new_dict['articleTags'],new_dict['authorName'],link))
                conn.commit()
                
            elif option=='toi':
                link=request.form['link']
                new_dict=toi(link)
                pera=textCleaner(new_dict['articleBody'])
                heading=new_dict['headline']
                articleTag=articleTags(new_dict['keywords'])
                authename=new_dict['author']['name']
                news='The Times of India'
                # store in data base
                cur.execute('insert into news(heading,nowords,nosentence,nopostag,articlekey,author,link) values(%s,%s,%s,%s,%s,%s,%s)',(news,word_func(pera),sentence_func(pera),upos1(pera),new_dict['articleTags'],new_dict['authorName'],link))
                conn.commit()

            # four tag
            dictmain['sentence']=sentence_func(pera)
            dictmain['words']=word_func(pera)
            dictmain['upos']=upos1(pera)
            dictmain['istrue']=classify_sentiment(pera)
            dictmain['heading']=heading
            dictmain['articleTag']=articleTag
            dictmain['authername']=authename
            # backend save
            conn.close()
            
        return render_template('News.html',dictmain=dictmain,pera=pera,name=name)
    except Exception as e:
        return render_template('News.html',dictmain=dictmain,name=name)


# Github login route
@app.route('/login/github')
def github_login():
    github = oauth.create_client('github')
    redirect_uri = url_for('github_authorize', _external=True)
    return github.authorize_redirect(redirect_uri)

# Github authorize route
@app.route('/login/github/authorize')
def github_authorize():
    conn=connect_to_db()
    cur=conn.cursor()
    try:
        github = oauth.create_client('github')
        token = github.authorize_access_token()
        session['github_token'] = token
        resp = github.get('user').json()
        print(f"\n{resp}\n")
        if resp['name']=='Rajat Malviya':
                cur.execute('select * from news')
                data=cur.fetchall()
        conn.close()
        return render_template("Searchhistory.html",lst=data)
    except:
        return render_template("News.html",dictmain={})

# Logout route for GitHub
@app.route('/logout/github')
def github_logout():
    session.pop('github_token', None)
    return redirect(url_for('portal'))       # here index is a function

if __name__=='__main__':
    app.run(debug=True)

    
# 1. Extract the news text and clean it.

# 2. Analyse the text for number of sentences, words, POS tags, and any other relevant information. Display this on the website in a nicely formatted manner after the URL is submitted.

# 3. Store the URL, news text, and a summary of your analysis in a PostgreSQL table.

# 4. There should be a button on the website to view history of URLs submitted and the associated analysis done. This should only be visible and accessible by the website admin.

# 5. Host this website and PostgreSQL database on www.render.com [free tier of 3 months]. Do not enter your bank information anywhere.

# 6. Create a detailed PDF report of the algorithm used and show output for a few test cases.
