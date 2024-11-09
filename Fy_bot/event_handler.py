import requests
from slack_sdk import WebClient
from requests.auth import HTTPBasicAuth
import json

# JSON 파일에서 Jira 설정 불러오기
json_path = '/Users/yujuyoung/Desktop/BRANCHIFY_BOT/Fy_bot/applications_info.json'
with open(json_path, 'r') as file:
    data = json.load(file)

jira_email = data.get('jira_email')
jira_api_token = data.get('jira_api_token')
jira_url = data.get('jira_url')
jira_project_key = data.get('jira_project_key')

def create_jira_issue(summary):
    headers = {
        "Content-Type": "application/json"
    }
    payload = json.dumps({
        "fields": {
            "project": {
                "key": jira_project_key
            },
            "summary": summary,
            "issuetype": {
                "name": "Task"
            }
        }
    })
    response = requests.post(
        f"{jira_url}/rest/api/2/issue",
        headers=headers,
        data=payload,
        auth=HTTPBasicAuth(jira_email, jira_api_token)
    )
    if response.status_code == 201:
        issue_key = response.json().get("key")
        return f"{jira_url}/browse/{issue_key}"
    else:
        print(f"Failed to create Jira issue: {response.status_code}, {response.text}")
        return None


def handle_reaction_added_event(event_data, slack_client: WebClient):
    if event_data['reaction'] in ["ticket", "티켓"]:
        channel = event_data['item']['channel']
        message_ts = event_data['item']['ts']

        # 메시지 내용 가져오기
        response = slack_client.conversations_history(channel=channel, latest=message_ts, limit=1, inclusive=True)
        if response["ok"] and response["messages"]:
            message_text = response["messages"][0]["text"]

            # Jira 티켓 생성
            issue_url = create_jira_issue(message_text)
            if issue_url:
                # 생성된 티켓 URL을 Slack 메시지로 회신
                slack_client.chat_postMessage(
                    channel=channel,
                    thread_ts=message_ts,
                    text=f"Jira 티켓이 생성되었습니다: {issue_url}"
                )
            else:
                print("Jira 티켓 생성에 실패했습니다.")