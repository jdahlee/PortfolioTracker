import os
import json
import logging
import requests
import threading
from atproto import Client
from atproto_client import models
from zoneinfo import ZoneInfo
from datetime import datetime, timedelta


class BlueskyClient:
    lock : threading.Lock
    all_posts: list
    client : Client
    per_post_retrieval_limit : int
    since_str : str
    until_str : str

    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.all_posts = list()
        bluesky_username = os.getenv('BLUESKY_USERNAME')
        bluesky_password = os.getenv('BLUESKY_PASSWORD')
    
        self.client = Client()
        self.client.login(bluesky_username, bluesky_password)

        self.per_post_retrieval_limit = int(os.getenv('PER_POST_RETRIEVAL_LIMIT', '5'))

        since_local = Helpers.get_start_of_last_us_day()
        since_utc = Helpers.convert_to_utc(since_local)
        self.since_str = since_utc.strftime("%Y-%m-%dT%H:%M:%S.000Z") # Datetime format expected by Bluesky API
        until_utc = since_utc + timedelta(days=1)
        self.until_str = until_utc.strftime("%Y-%m-%dT%H:%M:%S.000Z") # Datetime format expected by Bluesky API
    
    def _fetch_search_term_posts(self, search_term : str) -> None:
        search_term_params = models.AppBskyFeedSearchPosts.Params(
            q=search_term,
            limit=self.per_post_retrieval_limit,
            since=self.since_str,
            until=self.until_str,
            sort='top',
            lang='en'
        )
        self._fetch_posts(search_term_params)

    def _fetch_author_handle_posts(self, author_handle : str) -> None:
        search_term_params = models.AppBskyFeedSearchPosts.Params(
            q="*",
            limit=self.per_post_retrieval_limit,
            since=self.since_str,
            until=self.until_str,
            sort='top',
            lang='en',
            author=author_handle
        )
        self._fetch_posts(search_term_params)

    def _fetch_posts(self, params : models.AppBskyFeedSearchPosts.Params) -> None:
        result = self.client.app.bsky.feed.search_posts(params=params)

        with self.lock:
            for post in result.posts:
                self.all_posts.append(post.record)
    
    def fetch_all_posts(self) -> list:
        threads = []

        # comma seperated list of terms to search for posts that contain term in body
        search_terms_str = str(os.getenv('SEARCH_TERMS'))
        if search_terms_str != None:
            search_terms = search_terms_str.split(",")
            for search_term in search_terms:
                t = threading.Thread(target=self._fetch_search_term_posts, args=(search_term,))
                threads.append(t)

        # comma seperated list of author handles to search for posts of, don't include @ ex: joe.bsky.social
        author_handles_str = str(os.getenv('AUTHOR_HANDLES'))
        if author_handles_str != None:
            author_handles = author_handles_str.split(",")
            for author_handle in author_handles:
                t = threading.Thread(target=self._fetch_author_handle_posts, args=(author_handle,))
                threads.append(t)

        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        return self.all_posts
    
class AlphaVantageClient:
    api_key: str
    api_url_base: str
    lock: threading.Lock
    all_market_data: dict

    def __init__(self) -> None:
        self.api_key = os.getenv('ALPHA_VANTAGE_API_KEY', '')
        self.api_url_base = 'https://www.alphavantage.co/query?'
        self.lock = threading.Lock()
        self.all_market_data = dict()

    def _fetch_daily_data(self, symbol : str) -> None:
        function_title = 'TIME_SERIES_DAILY'
        url = self._generate_api_url(function_title, symbol=symbol)
        request_response = requests.get(url)
        json_response = json.loads(request_response.text)
        
        daily_data = json_response["Time Series (Daily)"] # the last 100 days of data automatically included
        recent_days = list(daily_data.keys())[:5]
        symbol_data = dict()
        for date in recent_days:
            date_data = daily_data[date]
            symbol_data[date] = {"open": date_data["1. open"], "close": date_data['4. close'], "volume": date_data['5. volume']}
        
        with self.lock:
            self.all_market_data[symbol] = symbol_data
    
    def _fetch_top_movement_data(self) -> None:
        function_title = 'TOP_GAINERS_LOSERS'
        url = self._generate_api_url(function_title)
        request_response = requests.get(url)
        json_response = json.loads(request_response.text)

        update_string = json_response["last_updated"]

        top_gainers = json_response["top_gainers"]
        filtered_gainers = [stock for stock in top_gainers if (float(stock["change_amount"]) > 1 and int(stock["volume"]) > 1000000)]

        top_losers = json_response["top_losers"]
        filtered_losers = [stock for stock in top_losers if (float(stock["change_amount"]) < -1 and int(stock["volume"]) > 1000000)]

        most_actively_traded = json_response["most_actively_traded"]
        filtered_most_active = [stock for stock in most_actively_traded if (float(stock["change_amount"]) < -1 or float(stock["change_amount"]) > 1)]

        with self.lock:
            self.all_market_data["filtered top gainers as of " + update_string] = filtered_gainers
            self.all_market_data["filtered top losers as of " + update_string] = filtered_losers
            self.all_market_data["filtered most traded as of" + update_string] = filtered_most_active

    def fetch_all_market_data(self) -> dict:
        threads = [] # NOTE Alpha Vantage has limit of 25 requests per day

        # comma seperated list of terms to symbols for stocks in portfolio / of interest
        symbols_str = str(os.getenv('ALPHA_VANTAGE_DAILY_SYMBOLS'))
        if symbols_str != None:
            symbols = symbols_str.split(",")
            for symbol in symbols:
                t = threading.Thread(target=self._fetch_daily_data, args=(symbol,))
                threads.append(t)
        
        top_movement_thread = threading.Thread(target=self._fetch_top_movement_data)
        threads.append(top_movement_thread)

        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        return self.all_market_data

    def _generate_api_url(self, function : str, symbol : str | None = None) -> str:
        url = self.api_url_base
        url += 'function=' + function
        if symbol:
            url += '&symbol=' + symbol
        url += '&apikey=' + self.api_key
        return url
    
class OllamaClient:
    url : str
    model : str

    def __init__(self) -> None:
        port = os.getenv('OLLAMA_PORT','11434')
        self.url = 'http://localhost:' + port + '/api/generate'
        self.model = os.getenv('OLLAMA_MODEL', 'llama3.2')

    def get_posts_summary_response(self, posts : list[str], market_data : dict) -> str:
        day = Helpers.get_start_of_last_us_day()
        default_prompt = f'You are a finance expert. You will be provided a series of posts from Bluesky gathered from the past day ({day.date()})'
        default_prompt += " and some market data including stocks that had significant movement or that are relevant to my portfolio."
        default_prompt += " Your job is to summarize the most important points from the data and provide them as a bulleted list in a report."
        default_prompt += " Discard pieces of information that don't seem relevant to the US finanacial market / economy or of significance."
        default_prompt += " Avoid using raw market data unless it connects to a Bluesky post or has significant ramifications for the overall market."
        default_prompt += " You should also provide a concise market outlook statement at the end of the report bassed on your analysis of the information provided."
        default_prompt += " Please make sure to add explanations to any technical terms or acronyms used in your report or outlook statement."
        default_prompt += " Please also include the date the report is for at the top of it."
        prompt = os.getenv('OLLAMA_POST_SUMMARY_PROMPT', default_prompt)
        prompt += "\nHere are the Bluesky posts:"
        prompt += "\n".join(posts)
        prompt += "\nHere is the market data:"
        prompt += str(market_data)
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }

        request_response = requests.post(self.url, json = payload)
        json_response = json.loads(request_response.text)
        return json_response["response"]
    
class Helpers:
    @staticmethod
    def get_start_of_last_us_day() -> datetime:
        us_eastern_tz = ZoneInfo('America/New_York')
        last_completed_day = datetime.now(us_eastern_tz) - timedelta(days=1)
        midnight_last_completed_day = last_completed_day.replace(hour=0, minute=0, microsecond=0)
        return midnight_last_completed_day
    
    @staticmethod
    def convert_to_utc(datetime : datetime) -> datetime:
        utc_tz = ZoneInfo("UTC")
        return datetime.astimezone(utc_tz)
    
    @staticmethod
    def write_to_output(body, output_type : str) -> None:
        if (output_type != "print" and output_type != "log"):
            raise ValueError(f'Invalid output_type: {output_type}, must be either print or log')
        
        if output_type == "print":
            print(body)
        else:
            logging.info(body)
