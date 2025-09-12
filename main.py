from dotenv import load_dotenv
from classes import BlueskyClient, OllamaClient

load_dotenv()

def main():
    print("Starting to retrieve posts...")
    bluesky_client = BlueskyClient()
    all_posts = bluesky_client.retrieve_all_posts()
    print("Finished retrieving posts")
    
    # TODO post cleaning to remove spam and useless ones
    print("Creating summary...\n")
    post_text = [p.text for p in all_posts]
    ollama_client = OllamaClient()
    ollama_summary = ollama_client.get_posts_summary_response(post_text)
    print(ollama_summary)

if __name__ == '__main__':
    main()