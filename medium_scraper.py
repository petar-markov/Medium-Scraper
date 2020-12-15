from article import Article

import requests
from bs4 import BeautifulSoup
import sqlite3
import time
import datetime
from datetime import timedelta

# Will implement this to work with a given keyword / tag
# and amount of articles to be retrieved 

def init_db():
    conn = sqlite3.connect("medium_articles.db")
    c = conn.cursor()

    # Use this only if you want to empty the entire schema, which
    # at this case is only 1 table basically. Not sure if the commit is needed in here
    # but just in case it might be a problem it is done.
    # c.execute("""DROP TABLE IF EXISTS articles""")
    # c.execute("""DROP TABLE IF EXISTS medium_authors""")
    # conn.commit()

    #Table to store the users and their information only, 
    #the relationship will be through the user_id.
    #Ultimately it is possible for a large amount of articles,
    #to have 1 user linked to a couple of articles
    c.execute("""CREATE TABLE IF NOT EXISTS medium_authors (
        author_id INTEGER PRIMARY KEY AUTOINCREMENT,
        author TEXT,
        author_url TEXT,
        UNIQUE(author_id, author)
    )""")

    conn.commit()

    #Main table to store the articles information
    #For now there really isn't any benefit to create additoinal
    #table for the articles, as there is no one-to-many or many-to-many
    #relationship in here, so no need to include additional complexity
    #for querying afterwards
    c.execute("""CREATE TABLE IF NOT EXISTS articles (
        article_id INTEGER PRIMARY KEY AUTOINCREMENT,
        author_id INTEGER,
        article_title TEXT,
        article_subtitle TEXT,
        article_url TEXT,
        article_claps INTEGER,
        read_time INTEGER,
        responses INTEGER,
        date_created TEXT,
        sections_num INTEGER,
        section_titles TEXT,
        paragraphs_num INTEGER,
        paragraphs TEXT,
        UNIQUE(article_id, article_title),
        FOREIGN KEY (author_id) REFERENCES medium_authors(author_id)                
    )""")

    conn.commit()

    c.execute("""CREATE UNIQUE INDEX IF NOT EXISTS pk_article_id ON articles (article_id ASC)""")
    c.execute("""CREATE UNIQUE INDEX IF NOT EXISTS pk_author_id ON medium_authors (author_id ASC)""")
    conn.commit()

    return conn, c

def convert_num(str_num):
    """
    A function to put a "0" prefix if the returning day/month is single digit
    This is needed as the URL does not work with a single digit months/days
    """
    if len(str_num) < 2:
        str_num = '0' + str_num
    return str_num

def get_article_content(url):
    """
    Function to extract article content specific information with a given URL
    Returning 4 objects in total
    section_titles_num - section titles total number from the article 
    section_titles - actual section titles 
    paragraphs_num - paragraphs number 
    paragraphs - paragraphs - actual article content
    """
    article_page = requests.get(url, verify=False)
    article_page_soup = BeautifulSoup(article_page.text, 'html.parser')

    sections = article_page_soup.find_all('section')

    section_titles = []
    paragraphs = []

    for section in sections:
        all_paragraphs = section.find_all('p')
        for p in all_paragraphs:
            paragraphs.append(p.text)
        
        titles = section.find_all('h1')
        for title in titles:
            section_titles.append(title.text)
        
    paragraphs_num = len(paragraphs)
    section_titles_num = len(section_titles)

    return section_titles_num, section_titles, paragraphs_num, paragraphs

def substract_day(str_date):
    """
    Script to substract 1 day and return the current date, YYYY, MM, DD as strings.
    """
    yyyy = int(str_date[0:4])
    mm = str_date[5:7]
    if mm[0] == "0": 
        mm = mm[1]
    dd = str_date[8:]
    if dd[0] == "0":
        dd = dd[1]
    mm = int(mm)
    dd = int(dd)

    date = datetime.date(yyyy, mm, dd)

    date_substracted = date - timedelta(days=1)

    #This should always use 2 digits for the month and day, so no need to transform
    date_substracted = date_substracted.strftime("%Y-%m-%d")

    yyyy = date_substracted[0:4]
    mm = date_substracted[5:7]
    dd = date_substracted[8:]

    return date_substracted, yyyy, mm, dd

def scrape(keyword, amount):
    #init
    conn, conn_cursor = init_db()

    #A set to store all the unique authors obtained as it
    #will be faster to check in here and it is by defauly only
    #for unique ones.
    # unique_authors = set()

    cnt = 0
    #We initialize the search from the current day and going backwards
    #as we start from this point later on we ensure that we take T-1
    # when we continue to scrape
    year = str(time.localtime()[0])

    month = str(time.localtime()[1])
    month = convert_num(month)

    #We start from T-1 at the beginning, because we use archives
    # from the Medium articles and it really doesn't make sense
    # to keep archive as of the current day. In fact if we use it
    # that way it will substract the day and give us results for the year/month only
    day = str(time.localtime()[2] - 1)
    day = convert_num(day)

    current_date = f'{year}-{month}-{day}'

    #A while loop will work for us to take that much articles info
    # to match the specified amount in the beginning
    # URL is being build in this loop and the dates taking T-1 is at the end of it.
    while True:

        url = f'https://medium.com/tag/{keyword}/archive/{year}/{month}/{day}'
        
        response = requests.get(url, verify=False)
        page = response.text
        soup = BeautifulSoup(page, 'html.parser')

        articles = soup.find_all("div", class_="postArticle postArticle--short js-postArticle js-trackPostPresentation js-trackPostScrolls")

        for article in articles:

            #Extracting all the needed information from the current article
            article_title = article.find("h3", class_="graf--title")
            if article_title:
                article_title = article_title.text

            article_url = article.find_all("a")[3]['href'].split('?')[0]
            article_subtitle = article.find("h4", class_="graf--subtitle")
            if article_subtitle:
                article_subtitle = article_subtitle.text
            else:
                article_subtitle = ""
            
            author_url = article.find('div', class_='postMetaInline u-floatLeft u-sm-maxWidthFullWidth')
            author_url = author_url.find('a')['href']
            author = author_url.split("@")[-1]

            #We store our unique autors in a set
            # unique_authors.add(author)

            claps = article.find('button', class_='button button--chromeless u-baseColor--buttonNormal js-multirecommendCountButton u-disablePointerEvents')
            if claps:
                #We make sure that we take the int and not something like 3.7K
                claps = int("".join([x for x in claps.text if x.isdigit()]))
            else:
                claps = 0
            
            try:
                read_time = article.find("span", class_="readingTime")['title']
                read_time = int(read_time.split()[0])
            except:
                read_time = -1
            
            responses = article.find('a', class_='button button--chromeless u-baseColor--buttonNormal')
            if responses:
                responses = int(responses.text.split()[0])
            else:
                responses = 0

            titles_num, titles, paragraphs_num, paragraphs = get_article_content(article_url)
            titles = ", ".join(titles)
            paragraphs = ", ".join(paragraphs)

            #First insert the current author in the authors table
            
            conn_cursor.execute("""INSERT OR IGNORE INTO medium_authors (author, author_url)
                                    VALUES (?, ?)""", (author, author_url))
            conn.commit()

            #Get the current author unique ID from the DB
            conn_cursor.execute("SELECT author_id FROM medium_authors WHERE author = ?", (author,))
            author_id = int(conn_cursor.fetchone()[0])


            # This worth to be used only if the logic is being extended
            # As of now there isn't really any value added if we init this object, 
            # also the object itself is having quite simple build and nothing to
            # give us any serious benefits.
            # If the logic is being enhanced and maybe some properties to be applied
            # this can definetely take in place

            # current_article = Article(author, 
            #                         author_url, 
            #                         article_title, 
            #                         article_subtitle, 
            #                         article_url, 
            #                         claps, 
            #                         read_time, 
            #                         responses, 
            #                         current_date, 
            #                         titles_num, 
            #                         titles, 
            #                         paragraphs_num, 
            #                         paragraphs)

            sql = """
                INSERT OR IGNORE INTO articles (
                    author_id,
                    article_title,
                    article_subtitle,
                    article_url,
                    article_claps,
                    read_time,
                    responses,
                    date_created,
                    sections_num,
                    section_titles,
                    paragraphs_num,
                    paragraphs         
                )
                VALUES (
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?
                )"""

            # We do a commit after every single insert, but
            # this might slow down the extraction / insertion phases,
            # so for significant amount of data being taken, a logic can be
            # put in place to do commit on batches per any count / number being selected.
            conn_cursor.execute(sql, (author_id, article_title, article_subtitle, article_url, claps, read_time, responses, current_date, titles_num, titles, paragraphs_num, paragraphs))
            
            conn.commit()  

            cnt += 1
            print('added one')
            print(cnt)

            if cnt == amount:
                break
        
        if cnt == amount:
            break
        
        #Substract 1 day from the date and continue to scrape data
        # until the amount is reached.
        current_date, year, month, day = substract_day(current_date)
    
    #Once everything is ready we better close the db connection
    # and thats all folks.
    conn.close()

scrape('bitcoin', 50)
