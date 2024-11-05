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

    def analyze_sentiment_with_chunking(self, text, chunk_size=5120):
        """Analyze sentiment by breaking down text into chunks if needed."""
        if not text:
            print("Text is empty, skipping sentiment analysis.")
            return {
                "overall_sentiment": "neutral",
                "sentiment_score": 0.5,
                "opinions": [],
            }

        chunks = [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]
        overall_sentiment_score = 0
        opinions = []

        for chunk in chunks:
            try:
                response = self.text_analytics_client.analyze_sentiment(
                    documents=[chunk], show_opinion_mining=True
                )[0]

                overall_sentiment_score += response.confidence_scores.positive

                for sentence in response.sentences:
                    if sentence.mined_opinions:
                        for mined_opinion in sentence.mined_opinions:
                            target = mined_opinion.target
                            assessments = [
                                {
                                    "text": assessment.text,
                                    "sentiment": assessment.sentiment,
                                }
                                for assessment in mined_opinion.assessments
                            ]
                            opinions.append(
                                {
                                    "target": target.text,
                                    "target_sentiment": target.sentiment,
                                    "assessments": assessments,
                                }
                            )

            except Exception as e:
                print(f"Error during sentiment analysis for a chunk: {e}")
                continue  # Skip this chunk if an error occurs

        # Calculate average sentiment score
        average_sentiment_score = overall_sentiment_score / len(chunks)
        overall_sentiment = "positive" if average_sentiment_score > 0.5 else "negative"

        return {
            "overall_sentiment": overall_sentiment,
            "sentiment_score": average_sentiment_score,
            "opinions": opinions,
        }

    def fetch_comments_as_blob(self, submission):
        """Aggregate all comments of a submission into a single text blob."""
        all_comments_text = " ".join(
            [
                comment.body
                for comment in submission.comments
                if isinstance(comment, praw.models.Comment)
            ]
        )
        return all_comments_text

    def send_to_event_hub(self, post_data):
        """Send post data to Event Hub in JSON format."""
        event_data_batch = self.producer.create_batch()
        event_data = EventData(json.dumps(post_data))
        event_data_batch.add(event_data)
        self.producer.send_batch(event_data_batch)
        print(f"Sent post to Event Hub: {post_data['title']}")

    def fetch_detailed_posts(self, subreddits, arg, limit=20):
        """Fetch posts, analyze sentiment (with opinion mining), and send to Event Hub."""
        for subreddit_name in subreddits:
            print(f"\nSearching in subreddit: r/{subreddit_name} for term: {arg}")
            subreddit = self.reddit.subreddit(subreddit_name)

            for submission in subreddit.search(
                arg, syntax="plain", time_filter="day", limit=limit
            ):
                comments_text_blob = self.fetch_comments_as_blob(submission)
                combined_text = f"{submission.selftext} {comments_text_blob}"

                # Analyze sentiment with chunking
                sentiment_result = self.analyze_sentiment_with_chunking(combined_text)

                post_data = {
                    "arg": arg,
                    "title": submission.title,
                    "score": submission.score,
                    "comments": submission.num_comments,
                    "post_id": submission.id,
                    "text": combined_text,
                    "author": str(submission.author),
                    "subreddit": str(submission.subreddit),
                    "subreddit_id": submission.subreddit_id,
                    "created_utc": submission.created_utc,
                    "overall_sentiment": sentiment_result["overall_sentiment"],
                    "sentiment_score": sentiment_result["sentiment_score"],
                    "opinions": sentiment_result["opinions"],
                }

                print("--" * 20)
                print("Overall Sentiment:", post_data["overall_sentiment"])
                print("Sentiment Score:", post_data["sentiment_score"])
                print("Opinions:", post_data["opinions"])

                # Send post data to Event Hub
                self.send_to_event_hub(post_data)
                print("--" * 20)


if __name__ == "__main__":
    fetcher = RedditEventHubFetcher()
    fetcher.fetch_detailed_posts(
        subreddits=[
            "gaming",
            "games",
            "xboxone",
            "PS4",
            "PlayStation",
            "xbox",
            "gamingnews",
            "pcgaming",
            "GameDeals",
            "videogames",
        ],
        arg="Xbox",
    )

    fetcher.fetch_detailed_posts(
        subreddits=[
            "gaming",
            "games",
            "xboxone",
            "PS4",
            "PlayStation",
            "xbox",
            "gamingnews",
            "pcgaming",
            "GameDeals",
            "videogames",
        ],
        arg="PlayStation",
    )
