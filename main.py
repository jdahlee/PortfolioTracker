import os
import logging
import argparse
from dotenv import load_dotenv
from classes import BlueskyClient, AlphaVantageClient, OllamaClient, OutputWriter, Helpers

load_dotenv()

def main():
    parser = argparse.ArgumentParser(description='A script to provide a summary of relevant financial information from the last full day.')
    parser.add_argument("--log", action="store_true", help="Write output to log file in program's .logs directory instead of printing")
    args = parser.parse_args()
    if args.log:
        log_path = os.getenv("PROGRAM_LOGS_DIRECTORY", "") # EX: c:/Users/joe/Programs/PortfolioTracker/.logs (This directory has to be exist before logs can be written to it)
        log_date = Helpers.get_start_of_last_us_day()
        log_path += "/" + log_date.strftime("%m_%d_%Y") + ".log"
        logging.basicConfig(filename=log_path, level=logging.INFO)
        logging.getLogger("httpx").setLevel(logging.WARNING)
        output_writer = OutputWriter("log")
    else:
        output_writer = OutputWriter("print")
    
    
    output_writer.write_to_output("Starting to retrieve posts...")
    bluesky_client = BlueskyClient(output_writer)
    all_posts = bluesky_client.fetch_all_posts()
    output_writer.write_to_output(f"Finished retrieving {len(all_posts)} posts")

    output_writer.write_to_output("Starting to retrieve market data...")
    alpha_vantage_client = AlphaVantageClient(output_writer)
    all_market_data = alpha_vantage_client.fetch_all_market_data()
    output_writer.write_to_output(f"Finished retrieving market data")
    
    # TODO post cleaning to remove spam and useless ones
    output_writer.write_to_output("Creating summary...\n")
    post_text = [p.text for p in all_posts]
    ollama_client = OllamaClient(output_writer)
    ollama_summary = ollama_client.get_posts_summary_response(post_text, all_market_data)
    output_writer.write_to_output(ollama_summary)

if __name__ == '__main__':
    main()