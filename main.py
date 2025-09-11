from atproto import Client
from atproto_client import models
import os
from dotenv import load_dotenv
import threading

load_dotenv()

class PostRetriever:
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
        term_params = models.AppBskyFeedSearchPosts.Params(
            q=search_term,
            limit=1,
            sort='top',
            lang='en'
        )
        result = self.client.app.bsky.feed.search_posts(
            params=term_params
        )

        with self.lock:
            for post in result.posts:
                self.all_posts.append(post.record)
    
    def retrieve_all_posts(self) -> None:
        threads = []
        search_terms = str(os.getenv('SEARCH_TERMS')).split(',')
        for search_term in search_terms:
            t = threading.Thread(target=self._retrieve_post, args=(search_term,))
            threads.append(t)

        for t in threads:
            t.start()
        for t in threads:
            t.join()


def main():
    post_retriever = PostRetriever()
    post_retriever.retrieve_all_posts()

    for p in post_retriever.all_posts:
        print("\n" + p.text + "\n")

def test():
    # bluesky_username = os.getenv('BLUESKY_USERNAME')
    # bluesky_password = os.getenv('BLUESKY_PASSWORD')
    
    # client = Client()
    # client.login(bluesky_username, bluesky_password)

    # all_posts = []
    # search_terms = str(os.getenv('SEARCH_TERMS')).split(',')

    # for term in search_terms:
    #     term_params = models.AppBskyFeedSearchPosts.Params(
    #         q=term,
    #         limit=2,
    #         sort='top',
    #         lang='en-US'
    #     )
    #     result = client.app.bsky.feed.search_posts(
    #         params=term_params
    #     )
    #     for post in result.posts:
    #         all_posts.append(post.record)
    pass

if __name__ == '__main__':
    main()