import json

import praw
from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential
from azure.eventhub import EventData, EventHubProducerClient
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient


class RedditEventHubFetcher:
    def __init__(
        self, key_vault_name="redditaccount", eventhub_name="reddit-data-stream"
    ):
        # Initialize Key Vault client
        kv_uri = f"https://{key_vault_name}.vault.azure.net"
        credential = DefaultAzureCredential()
        self.client = SecretClient(vault_url=kv_uri, credential=credential)

        # Initialize Event Hub producer
        eventhub_connection_str = self.client.get_secret(
            "EventHubConnectionString"
        ).value
        self.producer = EventHubProducerClient.from_connection_string(
            conn_str=eventhub_connection_str, eventhub_name=eventhub_name
        )

        # Initialize Reddit client with PRAW
        self.reddit = praw.Reddit(
            client_id=self.client.get_secret("RedditClientId").value,
            client_secret=self.client.get_secret("RedditClientSecret").value,
            username=self.client.get_secret("RedditUsername").value,
            password=self.client.get_secret("RedditPassword").value,
            user_agent="production_app_agent",
        )
        text_analytics_endpoint = self.client.get_secret(
            "AzureCognitiveServicesEndpoint"
        ).value
        self.text_analytics_key = self.client.get_secret(
            "AzureCognitiveServicesKeyA"
        ).value
        self.text_analytics_client = TextAnalyticsClient(
            text_analytics_endpoint,
            credential=AzureKeyCredential(self.text_analytics_key),
        )

    def analyze_sentiment(self, text):
        """Analyze sentiment of a given text using Azure Text Analytics."""
        if not text:  # Check if text is empty
            print("Text is empty, skipping sentiment analysis.")
            return 0.5  # You could choose a neutral default score, like 0.5

        try:
            response = self.text_analytics_client.analyze_sentiment(documents=[text])[0]
            sentiment_score = response.confidence_scores.positive
            print(f"Sentiment Score: {sentiment_score}")
            return sentiment_score
        except Exception as e:
            print(f"Error during sentiment analysis: {e}")
            return 0.5  # Return a neutral sentiment score if there's an error

    def send_to_event_hub(self, post_data):
        """Send post data to Event Hub in JSON format."""
        event_data_batch = self.producer.create_batch()
        event_data = EventData(json.dumps(post_data))
        event_data_batch.add(event_data)
        self.producer.send_batch(event_data_batch)
        print(f"Sent post to Event Hub: {post_data['title']}")

    def fetch_detailed_posts(self, subreddits, search_term, limit=10):
        """Fetch detailed posts from Reddit, analyze sentiment, and send them to Event Hub."""
        for subreddit_name in subreddits:
            print(f"\nSearching in subreddit: r/{subreddit_name}")
            subreddit = self.reddit.subreddit(subreddit_name)

            for submission in subreddit.search(search_term, limit=limit):
                # Analyze sentiment of the post text
                sentiment_score = self.analyze_sentiment(submission.selftext)

                post_data = {
                    "title": submission.title,
                    "score": submission.score,
                    "comments": submission.num_comments,
                    "post_id": submission.id,
                    "text": submission.selftext,
                    "author": str(submission.author),
                    "subreddit": str(submission.subreddit),
                    "subreddit_id": submission.subreddit_id,
                    "sentiment_score": sentiment_score,
                }

                # Print post details to console
                print("-" * 100)
                for key, value in post_data.items():
                    print(f"{key.capitalize()}: {value}")

                # Send post data to Event Hub
                self.send_to_event_hub(post_data)


if __name__ == "__main__":
    fetcher = RedditEventHubFetcher()
    fetcher.fetch_detailed_posts(subreddits=["learnpython"], search_term="Azure")
