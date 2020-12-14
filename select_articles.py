import sqlite3

conn = sqlite3.connect('medium_articles.db')

c = conn.cursor()

c.execute("SELECT DISTINCT article_title, author, date_created, read_time, article_claps, responses, article_url FROM articles")

for row in c.fetchall():
    print(row)

conn.close()