# Medium-Scraper

### A small scraper program for the Medium website using the BeautifulSoup python library.

### How to use:

The requirements are in the requirements.txt file. This version is designed to work with the sqlite python library, which is really easy to use and get up and running for an in-memory DB or a DB directly created on the disk. For this implementation, this is only a prototyping and the sqlite can be later on replaced with a PostgreSQL or any other DB engine.

The main function "scrape.py" is taking a keyword and amount of articles to be scraped.

The keyword is basically something that the authoer tagged with its article and you can basically use almost everything that is valid in the Medium search. We are using the Medium archive structure and always starting from T-1, as there is not archive for the current day.

The data scraped is quite detailed and structured in 2 tables - for the articles and for the authors. For now there really isn't that much need to introduce an additional table for the articles, as there isn't any relationship expected in there - for example it is not expected to have 2 articles with the same URL, text, etc. and all the other details are bound to the articles directly. For the authors on the other hand, if the DB exapnds - you can have an author with a couple of articles, that is why there is a separate table for it.

Before running the script - one can decide to drop the current tables, if they exists, which would mean that the scraped data from the current/last run will be the only present one. This is in the init_db() function.

The functions were tested with a couple of words and a final DB was created and imported with 75 articles in total - for the "machine-learning" and "bitcoin" keywords. An example output can be retrieved from the "select_articles.py" with some basic SQL/Python knowledge. There is a file "example_db_output.txt" which is showing the current view of the DB with the results retrieved.

