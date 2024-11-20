import requests
from slack_sdk import WebClient
from requests.auth import HTTPBasicAuth
import json
from slack_helper import post_message, get_message_text
from parse_message import parsing_message


# JSON 파일에서 설정 불러오기
json_path = '/Users/yujuyoung/Desktop/BRANCHIFY_BOT/Fy_bot/applications_info.json'
with open(json_path, 'r') as file:
    data = json.load(file)

jira_email = data.get('jira_email')
jira_api_token = data.get('jira_api_token')
jira_url = data.get('jira_url')
jira_project_key = data.get('jira_project_key')

notion_db_id = data.get('notion_db_id')  # 노션 데이터베이스 ID
notion_token = data.get('notion_token')  # 노션 API 토큰

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


def handle_reaction_added_event(event_data, slack_client, notion_client):
    reaction = event_data['reaction']

    if reaction in ["ticket", "티켓"]:
        process_jira_ticket(event_data, slack_client)
    elif reaction in ["page_facing_up", "글씨가_쓰여진_페이지"]:
        process_notion_page(event_data, slack_client, notion_client)
    elif reaction == 'dizzy':
        process_slack_message(event_data, slack_client)

    else:
        print(f"Unsupported reaction: {reaction}")


def process_jira_ticket(event_data, slack_client):
    channel = event_data['item']['channel']
    message_ts = event_data['item']['ts']
    message_text = get_message_text(slack_client, channel, message_ts)
    if not message_text:
        print("메시지를 찾을 수 없습니다.")
        return
    issue_url = create_jira_issue(message_text)
    if issue_url:
        post_message(
            channel=channel,
            thread_ts=message_ts,
            text=f"Jira 티켓이 생성되었습니다: {issue_url}"
        )


def process_notion_page(event_data, slack_client, notion_client):
    channel = event_data['item']['channel']
    message_ts = event_data['item']['ts']
    message_text = get_message_text(slack_client, channel, message_ts)
    if not message_text:
        print("메시지를 찾을 수 없습니다.")
        return

    notion_page_url = create_notion_page(message_text)
    if notion_page_url:
        post_message(
            slack_client,
            channel=channel,
            thread_ts=message_ts,
            text=f"Notion 페이지가 생성되었습니다: {notion_page_url}"
        )


def create_notion_page(title):
    headers = {
        "Authorization": f"Bearer {notion_token}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    data = {
        "parent": {"database_id": notion_db_id},
        "properties": {
            "이름": {
                "title": [
                    {"text": {"content": title}}
                ]
            }
        }
    }
    response = requests.post("https://api.notion.com/v1/pages", headers=headers, data=json.dumps(data))
    if response.status_code == 200:
        return response.json().get("url")
    else:
        print("Failed to create page:", response.status_code, response.text)
        return None



def process_slack_message(event_data, slack_client):
    """
    Slack에서 받은 이모지 반응에 따라 메시지를 파싱하여 댓글로 포스트
    """
    reaction = event_data['reaction']
    channel_id = event_data['item']['channel']
    message_ts = event_data['item']['ts']

    # 'dizzy' 이모지에 대해 처리
    if reaction == "dizzy":
        print("디지 이모지 감지")
        # Slack에서 메시지 가져오기
        message_text = get_message_text(slack_client, channel_id, message_ts)
        if not message_text:
            print("메시지를 찾을 수 없습니다.")
            return
        
        # 메시지 파싱
        parsed_result = parsing_message(message_text)

        # 딕셔너리를 문자열(JSON 형식)로 변환
        formatted_result = json.dumps(parsed_result, ensure_ascii=False, indent=2)

        # 결과를 댓글로 포스트
        post_message(
            slack_client,
            channel=channel_id,
            thread_ts=message_ts,
            text= formatted_result
        )