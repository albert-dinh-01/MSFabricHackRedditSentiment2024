import json

import azure.functions as func
import praw
from azure.eventhub import EventData, EventHubProducerClient
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

from main import RedditEventHubFetcher

app = func.FunctionApp()


@app.function_name(name="HttpTrigger1")
@app.route(route="req")
def main(req: func.HttpRequest) -> func.HttpResponse:
    # Retrieve search terms from the HTTP request
    arg1 = req.params.get("arg1")
    arg2 = req.params.get("arg2")
    subreddits = req.params.get("subreddits")

    # If parameters are not in the query, attempt to read from the request body
    if not arg1 or not arg2 or not subreddits:
        try:
            req_body = req.get_json()
        except ValueError:
            return func.HttpResponse(
                "Please provide 'arg1', 'arg2', and 'subreddits' in the request query or body",
                status_code=400,
            )
        else:
            arg1 = req_body.get("arg1")
            arg2 = req_body.get("arg2")
            subreddits = req_body.get("subreddits")

    # Validate the presence of parameters
    if not arg1 or not arg2 or not subreddits:
        return func.HttpResponse(
            "Missing required parameters: 'arg1', 'arg2', and 'subreddits'",
            status_code=400,
        )

    # Ensure subreddits is a list (in case it comes as a comma-separated string)
    if isinstance(subreddits, str):
        subreddits = subreddits.split(",")

    # Initialize the RedditEventHubFetcher
    fetcher = RedditEventHubFetcher()

    # Fetch posts using arg1 and arg2 as individual search terms
    fetcher.fetch_detailed_posts(subreddits=subreddits, search_term=arg1)
    fetcher.fetch_detailed_posts(subreddits=subreddits, search_term=arg2)

    return func.HttpResponse(
        f"Fetch complete for '{arg1}' and '{arg2}' in subreddits: {', '.join(subreddits)}",
        status_code=200,
    )
