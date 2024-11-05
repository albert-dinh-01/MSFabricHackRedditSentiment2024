import datetime
import logging

import azure.functions as func

from main import RedditEventHubFetcher

app = func.FunctionApp()


# Define a timer trigger to run every 12 hours
@app.function_name(name="TimerTriggerFetch")
@app.timer_trigger(schedule="0 0 */12 * * *", arg_name="mytimer")  # Runs every 12 hours
def timer_trigger_function(mytimer: func.TimerRequest) -> None:
    utc_timestamp = (
        datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).isoformat()
    )

    if mytimer.past_due:
        logging.info("The timer is past due!")

    logging.info("Timer trigger function ran at %s", utc_timestamp)

    # Define the list of subreddits for Xbox and PlayStation
    subreddits = [
        "gaming",
        "xbox",
        "playstation",
        "games",
        "gamingnews",
        "gamingcirclejerk",
        "ps5",
        "xboxone",
        "gamernews",
        "xboxseriesx",
    ]

    # Initialize the RedditEventHubFetcher
    fetcher = RedditEventHubFetcher()

    # Fetch posts for Xbox
    fetcher.fetch_detailed_posts(subreddits=subreddits, arg="Xbox")
    logging.info("Data fetching for Xbox completed.")

    # Fetch posts for PlayStation
    fetcher.fetch_detailed_posts(subreddits=subreddits, arg="PlayStation")
    logging.info("Data fetching for PlayStation completed.")
