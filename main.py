import os
import logging
import argparse
from dotenv import load_dotenv
from classes import BlueskyClient, OllamaClient, Helpers

load_dotenv()

def main():
    parser = argparse.ArgumentParser(description='A script to provide a summary of relevant financial information from the last full day.')
    parser.add_argument("--log", action="store_true", help="Write output to log file in program's .logs directory instead of printing")
    args = parser.parse_args()
    output_type = "print"
    if args.log:
        output_type = "log"
        log_path = os.getenv("PROGRAM_LOGS_DIRECTORY", "") # EX: c:/Users/joe/Programs/PortfolioTracker/.logs (This directory has to be exist before logs can be written to it)
        log_date = Helpers.get_start_of_last_us_day()
        log_path += "/" + log_date.strftime("%m_%d_%Y") + ".log"
        logging.basicConfig(filename=log_path, level=logging.INFO)
        logging.getLogger("httpx").setLevel(logging.WARNING)
        print("Writing output to file: " + log_path)
    
    Helpers.write_to_output("Starting to retrieve posts...", output_type)
    bluesky_client = BlueskyClient()
    all_posts = bluesky_client.retrieve_all_posts()
    Helpers.write_to_output(f"Finished retrieving {len(all_posts)} posts", output_type)
    
    # TODO post cleaning to remove spam and useless ones
    Helpers.write_to_output("Creating summary...\n", output_type)
    post_text = [p.text for p in all_posts]
    ollama_client = OllamaClient()
    ollama_summary = ollama_client.get_posts_summary_response(post_text)
    Helpers.write_to_output(ollama_summary, output_type)

if __name__ == '__main__':
    main()