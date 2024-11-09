from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# Slack 클라이언트 설정 함수
def get_slack_client(token):
    return WebClient(token=token)

def post_message(slack_client: WebClient, channel, text, thread_ts=None):
    try:
        response = slack_client.chat_postMessage(channel=channel, text=text, thread_ts=thread_ts)
        return response
    except SlackApiError as e:
        print(f"Error posting message: {e.response['error']}")
        return None

def get_slack_user_email(slack_client: WebClient, user_id):
    try:
        response = slack_client.users_profile_get(user=user_id)
        if response["ok"]:
            return response["profile"]["email"]
        else:
            print("Failed to retrieve user profile")
            return None
    except SlackApiError as e:
        print(f"Error fetching user email: {e.response['error']}")
        return None

def get_message_text(slack_client: WebClient, channel, message_ts):
    try:
        response = slack_client.conversations_history(channel=channel, latest=message_ts, limit=1, inclusive=True)
        if response["ok"] and response["messages"]:
            return response["messages"][0]["text"]
        else:
            print("Failed to fetch message text")
            return None
    except SlackApiError as e:
        print(f"Error fetching message: {e.response['error']}")
        return None