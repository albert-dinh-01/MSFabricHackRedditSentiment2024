import json
import os

import praw
from azure.eventhub import EventData, EventHubProducerClient
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

# Initialize Azure Key Vault client
key_vault_name = "redditaccount"
kv_uri = f"https://{key_vault_name}.vault.azure.net"
credential = DefaultAzureCredential()
client = SecretClient(vault_url=kv_uri, credential=credential)

# Event Hub setup
eventhub_connection_str = client.get_secret("EventHubConnectionString").value
eventhub_name = "reddit-data-stream"
producer = EventHubProducerClient.from_connection_string(
    conn_str=eventhub_connection_str, eventhub_name=eventhub_name
)

# Retrieve secrets from Azure Key Vault
client_id = client.get_secret("RedditClientId").value
client_secret = client.get_secret("RedditClientSecret").value
username = client.get_secret("RedditUsername").value
password = client.get_secret("RedditPassword").value

# Initialize Reddit client with PRAW
reddit = praw.Reddit(
    client_id=client_id,
    client_secret=client_secret,
    username=username,
    password=password,
    user_agent="production_app_agent",
)


# Function to send Reddit post data to Event Hub
def send_to_event_hub(post_data):
    event_data_batch = producer.create_batch()
    event_data = EventData(json.dumps(post_data))  # Convert post data to JSON format
    event_data_batch.add(event_data)
    producer.send_batch(event_data_batch)
    print(f"Sent post to Event Hub: {post_data['title']}")


# Function to fetch detailed Reddit posts and send to Event Hub
def fetch_detailed_posts(subreddits, search_term, limit=10):
    for subreddit_name in subreddits:
        print(f"\nSearching in subreddit: r/{subreddit_name}")
        subreddit = reddit.subreddit(subreddit_name)

        for submission in subreddit.search(search_term, limit=limit):
            post_data = {
                "title": submission.title,
                "score": submission.score,
                "comments": submission.num_comments,
                "post_id": submission.id,
                "text": submission.selftext,
                "author": str(submission.author),
                "subreddit": str(submission.subreddit),
                "subreddit_id": submission.subreddit_id,
            }

            # Print post details to console
            print("-" * 100)
            for key, value in post_data.items():
                print(f"{key.capitalize()}: {value}")

            # Send post data to Event Hub
            send_to_event_hub(post_data)


# Define the subreddits and search term
subreddits = ["politics", "worldnews"]
search_term = "kamala harris"

# Fetch posts and send to Event Hub
fetch_detailed_posts(subreddits, search_term)
