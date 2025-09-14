Purpose: Leverage Bluesky's REST API to get daily posts on stocks in portfolio. Then, pass posts to locally hosted model to create a daily update from the posts.

Setup:
- Install Ollama (https://ollama.com/) and download at least 1 model locally
- Clone this respository locally
- (Optional) Create a virtual environment for repo
- Install required packages: pip install -r requirements.txt
- Create and fill out .env file in project directory

Env file:
- BLUESKY_USERNAME= Your Bluesky account's username EX: "joe.bsky.social"
- BLUESKY_PASSWORD= Your Bluesky account's password
- SEARCH_TERMS= Comma seperated list of terms to search for EX: "nasdaq,#stocks,US AND ECONOMY,$aapl"
- AUTHOR_HANDLES= Comma seperated list of authors handles whsoe posts you want to include EX: "joe.bsky.social"
- PER_POST_RETRIEVAL_LIMIT= (Optional) String number of posts to retrieve per search term / author handle (program default is 5)
- OLLAMA_PORT= (Optional) Local port that Ollama is accessible from (ollama default is 11434)
- OLLAMA_MODEL= (Optional) Ollama model to utilize for summary (program default is llama3.2)
- PROGRAM_LOGS_DIRECTORY= (Optional) Directory to place output logs instead of printing to terminal "c:/Users/joe/PortfolioTracker/.logs"

Execution:
- Ensure Ollama is running (Ollama serve)
- Run main.py file
- Optionally pass --log flag in command line to write output to a log file rather than the terminal




