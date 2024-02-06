# imports important for Airflow
import pendulum
from airflow.decorators import dag, task
import logging
import time
from newsapi import NewsApiClient
from airflow.providers.mongo.hooks.mongo import MongoHook
from datetime import datetime, timedelta
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
@dag(
    schedule_interval=None,
    start_date=pendulum.datetime(2024, 1, 1, tz="UTC"),
    catchup=False,
    tags=[f'Loading raw sport ford data into Airflow'],
)

def el_electric_ford_data_into_mongodb():
    @task
    def extract_from_newsapi(q, from_param, to, language, pages):

        newsapi = NewsApiClient(api_key='4e5ef1ac63bc437eafaad4a91430b725')
        all_articles = []
        for page in range(pages, pages + 5):
            response = newsapi.get_everything(q=q,
                                              from_param=from_param,
                                              to=to,
                                              language=language,
                                              page=page)
            articles = response['articles']
            logging.info(f"Successfully fetched articles for page {page}")
            all_articles.append(articles)
            if page < pages + 4:
                logging.info("Waiting 3 seconds before fetching the next page...")
                time.sleep(3)
        return all_articles

    @task
    def load_raw_data(all_articles: list):
        try:
            hook = MongoHook(mongo_conn_id="mongo_default")
            client = hook.get_conn()
            db = client.trending_data
            collection = db.raw_sport
            logging.info(f"Connected to MongoDB - {client.server_info()}")
            for article in all_articles:
                collection.insert_many(article)
                logging.info("Articles successfully inserted into MongoDB")
        except Exception as e:
            logging.error(f"Error connecting to or inserting into MongoDB: {e}")


    all_articles = extract_from_newsapi("Ford Mustang Mach-E", datetime.today().date() - timedelta(days=1), datetime.today().date(),
                                        "en", 1)
    load_raw_data(all_articles)

el_electric_ford_data_into_mongodb()