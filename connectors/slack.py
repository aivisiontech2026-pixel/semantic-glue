import os
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

load_dotenv()

app = App(token=os.environ["SLACK_BOT_TOKEN"])


@app.event("app_mention")
def handle_mention(event, say):
    user = event["user"]
    text = event["text"]

    say(f"Hello <@{user}>! You said:\n>{text}")


@app.event("message")
def handle_dm(event, say):
    if event.get("channel_type") == "im" and "bot_id" not in event:
        say(f"You said: {event['text']}")


def send_file(channel, file_path, title=None, initial_comment=None):
    return app.client.files_upload_v2(
        channel=channel,
        file=file_path,
        title=title,
        initial_comment=initial_comment,
    )


if __name__ == "__main__":
    SocketModeHandler(
        app,
        os.environ["SLACK_APP_TOKEN"]
    ).start()
