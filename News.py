from flask import Flask, render_template, url_for, redirect, session,request       # It make a flask environment using some function 
import psycopg2                                                                    # For postgres sql data base 
from nltk import *                                                                 # Hepl to analyse the text 
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer                        # Sentiment analysis using vander class 
import json                                                                        # It help to manipulate json 
import requests              
import re 
import os
# Regular expression operations
from bs4 import BeautifulSoup                                                      # It screpe news from website   
from authlib.integrations.flask_client import OAuth                                # OAuth integration for Flask
nltk.download('all')

# Here instence made  
app=Flask(__name__,static_folder='data')
# DATABASE_URL="postgres://dhp2024_44yk_user:hYblUsnTd53xOGdkVu0d70jAP5LR1SBC@dpg-cnlhmc0l6cac73ef0vmg-a.oregon-postgres.render.com/dhp2024_44yk"
oauth = OAuth(app)
# DATABASE_URL = os.getenv('DATABASE_URL')

app.config['SECRET_KEY'] = "THIS SHOULD BE SECRET"
app.config['GITHUB_CLIENT_ID'] = "992ca9ab81fae0231b83"
app.config['GITHUB_CLIENT_SECRET'] = "a0c7e13b2dfdb91e32c700563eed8420f6594e2b"
github_admin_usernames = [ "atmabodha","rajat-malvi"]

#  regarding registration  
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
    ''' this function for data base connection'''
    conn=psycopg2.connect(
        host='dpg-cnm9kh8l6cac73fasqk0-a',  database='dhp2024_39d2', user='dhp2024_39d2_user', password='Lnd4PsesDWpC4BB7EocKkatKwX93BYAK')
    return conn

# It create a table if not exist  
def create_table():
    conn=connect_to_db()
    cursor = conn.cursor()
    
    cursor.execute("""
            create table if not exists news(
                name varchar(1000),
                nowords varchar(100),
                nosentence varchar(100),
                nopostag varchar(1000),
                articlekey varchar(10000),
                pera varchar(10000000),
                author varchar(500),
                link varchar(10000) not null
            )
        """)
    conn.commit()
    
create_table()    

# ---------------------------------------------------------------------------------------------------------------------------------------


# bs4 code 
def getsoup(s):
    '''it provide soup(main )'''
    URL=f'{s}'
    page=requests.get(URL)
    soup=BeautifulSoup(page.content,"html.parser")
    return soup

def reax(s):
    '''Regular expresion it clean the text in some spacific pattern'''
    raw_html=str(s)
    cleantext=re.sub(r'<.*?>','',raw_html)      # sub use to substitute the value with other
    return cleantext

# www.thehindu.com
def thd(s):
    soup=getsoup(s)
    # for purely pera
    artical = soup.find('div', class_='articlebodycontent') # hear crticle accese 
    lst = artical.find_all('p')     # list of all peragraph 

    cleaned_news = []
    # itrete all pere graph and clean all peregraph text by using some patterns 
    for tag in lst:
        if 'share' not in tag.get('class', []) and 'related-topics-list' not in tag.get('class', []) and 'comments' not in tag.get('class', []):
            cleaned_news.append(tag.get_text().strip())
    pera=''
    # again combain all peragraph and make a article.
    for news in cleaned_news:
        pera+=" " + news
    return pera.strip()


def thddict(l):
    '''The Hindu dict it return some important detail that extrect from the article  '''
    soup=getsoup(l)
    string=soup.script.get_text().strip()
    dict1=json.loads(string[55:-2].replace('\n',"").replace('// when available',"").replace("'",'"'))
    dict2=dict1['pageDetails']
    return dict2

# TOI
def toi(s):
    # It return a json in which contain all meta data
    soup=getsoup(s)
    scriptlist=soup.find_all('script')    
    dict1=json.loads(scriptlist[-2].get_text())
    return dict1


# ---------------------------------------------------------------------------------------------------------------------------------------
# NLTK 
def sentence_func(s):
    '''Using sent_tokenize function it return a list of sentence'''
    sentence= sent_tokenize(s) 
    return len(sentence)

def word_func(s):
    '''It use word_tokenize and return a list of word without using punctuation.'''
    lst=[',','.','?','!']
    word_list=word_tokenize(s)
    count=0
    for i in word_list:
        if i not in lst:
            count+=1   
    return count

def upos1(s):
    # it tell about noun, verb,adjective etc.
    '''this function return a dict in  '''
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
                # store in data base
                cur.execute('insert into news(name,nowords,nosentence,nopostag,articlekey,pera,author,link) values(%s,%s,%s,%s,%s,%s,%s,%s)',(name,word_func(pera),sentence_func(pera),upos1(pera),new_dict['articleTags'],pera,new_dict['authorName'],link))
                conn.commit()
                
            elif option=='toi':
                link=request.form['link']
                new_dict=toi(link)
                pera=textCleaner(new_dict['articleBody'])
                heading=new_dict['headline']
                articleTag=articleTags(new_dict['keywords'])
                authename=new_dict['author']['name']
                # store in data base
                cur.execute('insert into news(name,nowords,nosentence,nopostag,articlekey,pera,author,link) values(%s,%s,%s,%s,%s,%s,%s,%s)',(name,word_func(pera),sentence_func(pera),upos1(pera),new_dict['keywords'],pera,authename,link))
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
        logged_in_username = resp.get('login')
        if logged_in_username in github_admin_usernames:
            cur.execute('select * from news')
            data=cur.fetchall()
            conn.close()
            return render_template("Searchhistory.html",lst=data)
        else:
            return render_template("News.html",dictmain={})
    except:
        return render_template("News.html",dictmain={})

# Logout route for GitHub
@app.route('/logout/github')
def github_logout():
    session.pop('github_token', None)
    return redirect(url_for('portal'))       # here index is a function

if __name__=='__main__':
    app.run(debug=True)
