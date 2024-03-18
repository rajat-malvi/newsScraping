from flask import Flask, render_template, url_for, redirect, session,request       # It make a flask environment using some function 
import psycopg2                                                                    # For postgres sql data base 
from nltk import *                                                                 # Hepl to analyse the text 
import nltk                                                                         
from nltk.sentiment.vader import SentimentIntensityAnalyzer                        # Sentiment analysis using vander class 
import json                                                                        # It help to manipulate json 
import requests                                                                    # Import the requests library for making HTTP requests
import re                                                                          # Regular expression operations
from bs4 import BeautifulSoup                                                      # It screpe news from website   
from authlib.integrations.flask_client import OAuth                                # OAuth integration for Flask
nltk.download('all')
# Here instence made  
app=Flask(__name__,static_folder='static')
# oAuth instence is create 
oauth = OAuth(app)

# github reqired pass key
app.config['SECRET_KEY'] = "Rajat"
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
    # using Postgress sql it create a table news
    cursor.execute("""
            create table if not exists news_data(
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
        
# ---------------------------------------------------------------------------------------------------------------------------------------

# bs4 code 
def getsoup(s):
    '''It provide soup(main metadata)'''
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
    '''It returns article by doing some cleanig on article '''
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
    '''The Hindu dict it return some important detail that extrect from the article '''
    soup=getsoup(l)
    string=soup.script.get_text().strip()
    dict1=json.loads(string[55:-2].replace('\n',"").replace('// when available',"").replace("'",'"'))
    dict2=dict1['pageDetails']
    return dict2

# TOI
def toi(s):
    '''It return a json in which contain all meta data of The Times of india'''
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
    '''this function return a dict in  '''
    # it tell about noun, verb,adjective etc.
    words=word_tokenize(s)
    lst = nltk.pos_tag(words,tagset='universal') # in this list we have tuple that indicate word is verb, noun or somthing else
    dict1={}
    for i in lst:
        if i[1] not in dict1:
            dict1[i[1]]=1   
        else:
            dict1[i[1]]+=1
    # here it convert dict to string format by using dumps class of json
    dict1=json.dumps(dict1)
    return dict1

# ----------------------------------------------------------------------------------------------------------------------------------

# other stuff
def classify_sentiment(text):
  """Analyzes the sentiment of a paragraph and returns True , False , or "neutral"."""
  # Use VADER sentiment analyzer 
  # Create a SentimentIntensityAnalyzer object for sentences analysis
  analyzer = SentimentIntensityAnalyzer()
  # scores is a dict in which the words are st
  # it return a dict like this {'neg': 0.003, 'neu': 0.899, 'pos': 0.098, 'compound': 0.9908}
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
    '''this function is return a list of words'''
    if '|' in s:
        lst=s.split('|') 
    elif ',' in s:
        lst=s.split(',')
    return lst

# text cleaner 
def textCleaner(s):
    '''It is the one of the most claning part for the news The Times of India it gives clean article by using Regular expression '''
    new=re.sub(r'[0-9]+',' ',s)     # Here substitue function replace the unknown numbers with a space 
    res = re.sub(r'([a-z])([A-Z])', r'\1 \2', new)      # Add a space between a lowercase letter followed by an uppercase letter
    res=re.sub(r'[^\w\s]','',res)   # It removes wide-space and alphnumeric words like '123abc' and replace with  
    res=re.sub(r'\s+',' ',res)      # It Replace multiple whide-space characters with a single space
    return res

# main portal 
@app.route("/",methods=('GET','POST'))
def portal():
    '''main function for webapp that render all information on the webpage'''
    # connection
    conn=connect_to_db()
    cur=conn.cursor()
    
    try:
        # here I decleare variable 
        link=''
        pera=''
        heading='Today Headline'
        articleTag=''
        istrue=''
        option=''
        name=''
        authename='Writer'
        dictmain={}
        
        if request.method=="POST":
            # get info from user login form 
            option=request.form.get('news') 
            name=request.form.get('user')   
            # It works when user select option The Hindu 
            if option=='The_Hindu':     
                link=request.form['link']   
                pera=thd(link)
                new_dict=thddict(link)
                articleTag=articleTags(new_dict['articleTags'])
                heading=new_dict['headline']
                authename=new_dict['authorName']
                dictmain['sentence']=sentence_func(pera)
                # store in data-base 
                cur.execute('insert into news_data(name,nowords,nosentence,nopostag,articlekey,pera,author,link) values(%s,%s,%s,%s,%s,%s,%s,%s)',(name,word_func(pera),sentence_func(pera),upos1(pera),articleTag,pera,new_dict['authorName'],link))
                conn.commit()
            
            # It works when user select The Times of India 
            elif option=='toi':
                link=request.form['link']
                new_dict=toi(link)
                pera=textCleaner(new_dict['articleBody'])
                heading=new_dict['headline']
                articleTag=articleTags(new_dict['keywords'])
                authename=new_dict['author']['name']
                dictmain['sentence']=sentence_func(new_dict['articleBody'])
                # store in data base
                cur.execute('insert into news_data(name,nowords,nosentence,nopostag,articlekey,pera,author,link) values(%s,%s,%s,%s,%s,%s,%s,%s)',(name,word_func(pera),sentence_func(pera),upos1(pera),new_dict['keywords'],pera,authename,link))
                conn.commit()

            # here it collect all the data in the json formate that render on the main portal. 
            # dictmain['sentence']=sentence_func(pera)
            dictmain['words']=word_func(pera)
            dictmain['upos']=upos1(pera)
            dictmain['istrue']=classify_sentiment(pera)
            dictmain['heading']=heading
            dictmain['articleTag']=articleTag
            dictmain['authername']=authename
            
            # backend coonection close
            conn.close()
            
        return render_template('News.html',dictmain=dictmain,pera=pera,name=name)   # using render templet it return all the data 
    except Exception as e:
        return render_template('News.html',dictmain=dictmain,name=name)


# Github login route
@app.route('/login/github')
def github_login():
    '''Route for initiating GitHub OAuth login'''
    github = oauth.create_client('github')  # Create a GitHub OAuth client
    redirect_uri = url_for('github_authorize', _external=True)  # It Generate the redirect URI for authorization
    return github.authorize_redirect(redirect_uri)  # Redirect the user to GitHub for authorization

# Github authorize route
@app.route('/login/github/authorize')
def github_authorize():
    '''Route for handling GitHub OAuth authorization'''
    # main function for github that check if the user is admin the it redirect to history page 
    # It take connection 
    conn = connect_to_db()  
    cur = conn.cursor()  
    
    try:
        github = oauth.create_client('github')  # Create a GitHub OAuth client
        token = github.authorize_access_token()  # Get the access token from the authorization response
        session['github_token'] = token  # Store the access token in the session
        resp = github.get('user').json()  # Get the user's information from GitHub
        # print(f"\n{resp}\n")
        logged_in_username = resp.get('login')  # Get the username from the user's information
        if logged_in_username in github_admin_usernames:  # Check if the username is in the list of admin usernames
            cur.execute('select * from news_data')  
            data = cur.fetchall()  # Fetch all rows from the 'news' table
            conn.close()  
            return render_template("Searchhistory.html", lst=data)
        else:
            return render_template("News.html", dictmain={})  
    except:
        return render_template("News.html", dictmain={}) 

# Logout route for GitHub
@app.route('/logout/github')
def github_logout():
    '''Route for logging out from GitHub OAuth'''
    session.pop('github_token', None)  # Remove the access token from the session
    return redirect(url_for('portal'))  # Redirect the user to the main page

if __name__=='__main__':
    create_table()  # here it call the create_table function 
    app.run(debug=True)
