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
    # at this case is only 1 table basically.
    c.execute("""DROP TABLE articles""")
    conn.commit()

    c.execute("""CREATE TABLE IF NOT EXISTS articles (
        article_id INTEGER PRIMARY KEY AUTOINCREMENT,
        author TEXT,
        author_url TEXT,
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
        paragraphs TEXT                
    )""")

    conn.commit()

    c.execute("""CREATE UNIQUE INDEX IF NOT EXISTS pk_article_id ON articles (article_id ASC)""")

    conn.commit()

    return conn, c

    # Do not really need this for now, as it will be confusing to split all the paragraphs
    # of an article to have the relationship one to many. No need for additional complexity
    # for now so using only one table.

    # c.execute("""CREATE TABLE IF NOT EXISTS articles_content (
    #     content_id INTEGER PRIMARY KEY AUTOINCREMENT,
    #     article_id INTEGER,
    #     sections_num INTEGER,
    #     section_titles TEXT,
    #     paragraphs_num INTEGER,
    #     paragraphs TEXT,
    #     FOREIGN KEY (article_id) REFERENCES articles(article_id)
    # )""")

    #Close must be once we finish with importing data as well
    # conn.close()

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
    article_page = requests.get(url)
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
        
        response = requests.get(url)
        page = response.text
        soup = BeautifulSoup(page, 'html.parser')

        articles = soup.find_all("div", class_="postArticle postArticle--short js-postArticle js-trackPostPresentation js-trackPostScrolls")

        for article in articles:

            #Extracting all the needed information from the current article
            article_title = article.find("h3", class_="graf--title").text
            article_url = article.find_all("a")[3]['href'].split('?')[0]
            article_subtitle = article.find("h4", class_="graf--subtitle")
            if article_subtitle:
                article_subtitle = article_subtitle.text
            else:
                article_subtitle = ""
            
            author_url = article.find('div', class_='postMetaInline u-floatLeft u-sm-maxWidthFullWidth')
            author_url = author_url.find('a')['href']
            author = author_url.split("@")[-1]
            
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
                INSERT INTO articles (
                    author,
                    author_url,
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
                    ?,
                    ?
                )"""

            # We do a commit after every single insert, but
            # this might slow down the extraction / insertion phases,
            # so for significant amount of data being taken, a logic can be
            # put in place to do commit on batches per any count / number being selected.
            conn_cursor.execute(sql, (author, author_url, article_title, article_subtitle, article_url, claps, read_time, responses, current_date, titles_num, titles, paragraphs_num, paragraphs))
            
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

scrape('machine-learning', 15)