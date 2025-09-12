from atproto import Client
from atproto_client import models
import os
from dotenv import load_dotenv
import threading
import requests
import json
from datetime import datetime, timedelta

load_dotenv()

class BlueskyClient:
    lock : threading.Lock
    all_posts: list
    client : Client
    per_post_retrieval_limit : int
    since_str : str

    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.all_posts = list()
        bluesky_username = os.getenv('BLUESKY_USERNAME')
        bluesky_password = os.getenv('BLUESKY_PASSWORD')
    
        self.client = Client()
        self.client.login(bluesky_username, bluesky_password)

        self.per_post_retrieval_limit = int(os.getenv('PER_POST_RETRIEVAL_LIMIT', '5'))
        self.since_str = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S.000Z") # Datetime format expected by Bluesky API
    
    def _retrieve_search_term_posts(self, search_term : str) -> None:
        search_term_params = models.AppBskyFeedSearchPosts.Params(
            q=search_term,
            limit=self.per_post_retrieval_limit,
            since=self.since_str,
            sort='top',
            lang='en'
        )
        self._retrieve_posts(search_term_params)

    def _retrieve_author_handle_posts(self, author_handle : str) -> None:
        search_term_params = models.AppBskyFeedSearchPosts.Params(
            q="*",
            limit=self.per_post_retrieval_limit,
            since=self.since_str,
            sort='top',
            lang='en',
            author=author_handle
        )
        self._retrieve_posts(search_term_params)

    def _retrieve_posts(self, params : models.AppBskyFeedSearchPosts.Params) -> None:
        result = self.client.app.bsky.feed.search_posts(params=params)

        with self.lock:
            for post in result.posts:
                self.all_posts.append(post.record)
    
    def retrieve_all_posts(self) -> list:
        threads = []

        # comma seperated list of terms to search for posts that contain term in body
        search_terms_str = str(os.getenv('SEARCH_TERMS'))
        if search_terms_str != None:
            search_terms = search_terms_str.split(",")
            for search_term in search_terms:
                t = threading.Thread(target=self._retrieve_search_term_posts, args=(search_term,))
                threads.append(t)

        # comma seperated list of author handles to search for posts of, don't include @ ex: joe.bsky.social
        author_handles_str = str(os.getenv('AUTHOR_HANDLES'))
        if author_handles_str != None:
            author_handles = author_handles_str.split(",")
            for author_handle in author_handles:
                t = threading.Thread(target=self._retrieve_author_handle_posts, args=(author_handle,))
                threads.append(t)


        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        return self.all_posts

class OllamaClient:
    url : str
    model : str

    def __init__(self) -> None:
        port = os.getenv('OLLAMA_PORT','11434')
        self.url = 'http://localhost:' + port + '/api/generate'
        self.model = os.getenv('OLLAMA_MODEL', 'llama3.2')

    def get_post_summary_response(self, posts : list[str]) -> str:
        prompt = "please summarize the following bluesky posts from the past 24 hours to give an update on the stock market:"
        prompt += "\n".join(posts)
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }

        request_response = requests.post(self.url, json = payload)
        json_response = json.loads(request_response.text)
        return json_response["response"]


def main():
    bluesky_client = BlueskyClient()
    all_posts = bluesky_client.retrieve_all_posts()

    # for p in all_posts:
    #     print("\n" + p.text + "\n")
    
    # TODO clean out posts that contain a link to a personal website
    post_text = [p.text for p in all_posts]
    ollama_client = OllamaClient()
    ollama_summary = ollama_client.get_post_summary_response(post_text)
    print(ollama_summary)

def test():
    pass

if __name__ == '__main__':
    main()
    # test()