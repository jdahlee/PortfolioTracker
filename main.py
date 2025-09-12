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

    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.all_posts = list()
        bluesky_username = os.getenv('BLUESKY_USERNAME')
        bluesky_password = os.getenv('BLUESKY_PASSWORD')
    
        self.client = Client()
        self.client.login(bluesky_username, bluesky_password)
    
    def _retrieve_post(self, search_term : str) -> None:
        since_str = datetime.now() - timedelta(days=1)
        print(f'since: {since_str.strftime("%Y-%m-%dT%H:%M:%S.000Z")}')

        term_params = models.AppBskyFeedSearchPosts.Params(
            q=search_term,
            since=since_str.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            limit=5,
            sort='top',
            lang='en',
        )
        result = self.client.app.bsky.feed.search_posts(
            params=term_params
        )

        with self.lock:
            for post in result.posts:
                self.all_posts.append(post.record)
    
    def retrieve_all_posts(self) -> list:
        threads = []
        search_terms = str(os.getenv('SEARCH_TERMS')).split(',')
        for search_term in search_terms:
            t = threading.Thread(target=self._retrieve_post, args=(search_term,))
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