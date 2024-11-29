import requests
from slack_sdk import WebClient
from requests.auth import HTTPBasicAuth
import json
from slack_helper import post_message, get_message_text
from parse_message import parsing_message
from datetime import datetime

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
    """
    Slack 이벤트 데이터를 기반으로 Notion 페이지를 생성하고,
    성공 시 생성된 Notion 페이지 URL을 Slack 메시지의 쓰레드에 전송합니다.
    """
    channel = event_data['item']['channel']
    message_ts = event_data['item']['ts']
    
    # Slack에서 메시지 가져오기
    message_text = get_message_text(slack_client, channel, message_ts)
    if not message_text:
        print("메시지를 찾을 수 없습니다.")
        return

    # 메시지를 기반으로 Notion 페이지 생성
    notion_page_url = create_notion_page(message_text)
    if notion_page_url:
        # 생성된 Notion 페이지 URL을 Slack 메시지의 쓰레드에 답변으로 전송
        post_message(
            slack_client,
            channel=channel,
            thread_ts=message_ts,
            text=f"✅ Notion 페이지가 성공적으로 생성되었습니다: {notion_page_url}"
        )
    else:
        # 실패 시 에러 메시지를 쓰레드에 전송
        post_message(
            slack_client,
            channel=channel,
            thread_ts=message_ts,
            text="❌ Notion 페이지 생성에 실패했습니다. 관리자에게 문의하세요."
        )


def create_notion_page(title, date, content, person):
    # 날짜를 ISO 8601 형식으로 변환
    start_date = datetime.strptime(date, "%Y-%m-%d").isoformat()  # "YYYY-MM-DD" 형식으로 가정
    end_date = start_date  # 예시로 시작일과 종료일이 같다고 가정

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
            },
            "날짜": {
                "date": {
                    "start": start_date,
                    "end": end_date
                }
            },
            "담당": {
                "multi_select": [
                    {"name": person}  # 여기에서 'person'이 다중 선택 옵션으로 들어갑니다.
                ]
            }
        },
        "children": [
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": content  # 페이지 내용 추가
                            }
                        }
                    ]
                }
            }
        ]
    }

    response = requests.post("https://api.notion.com/v1/pages", headers=headers, data=json.dumps(data))

    if response.status_code == 200:
        return response.json().get("url")
    else:
        print("Failed to create page:", response.status_code, response.text)
        return None
    




def process_notion_page(event_data, slack_client, notion_client):
    """
    Slack 메시지를 기반으로 Notion 페이지를 생성합니다.
    """
    # Slack에서 메시지 가져오기
    reaction = event_data['reaction']
    channel_id = event_data['item']['channel']
    message_ts = event_data['item']['ts']
    message_text = get_message_text(slack_client, channel_id, message_ts)
    
    if not message_text:
        print("메시지를 찾을 수 없습니다.")
        return

    # 메시지 파싱
    parsed_result = parsing_message(message_text)
    # 제목, 날짜, 내용, 담당자 추출
    title = parsed_result.get('제목', '제목 미지정')
    date = parsed_result.get('날짜', datetime.now().strftime("%Y-%m-%d"))
    # 날짜 변환: '월 일' 형식 -> 'YYYY-MM-DD' 형식
    try:
        if date and date != "날짜 미지정":
            date_parts = date.split('월')
            if len(date_parts) == 2:  # '11월 26일' 형식일 경우
                date = f"2024-{date_parts[0].strip().zfill(2)}-{date_parts[1].replace('일', '').strip().zfill(2)}"
            else:
                raise ValueError("날짜 형식이 올바르지 않습니다.")
        else:
            # 기본값으로 오늘 날짜 설정
            date = datetime.now().strftime("%Y-%m-%d")
    except ValueError as e:
        print(f"날짜 형식 오류: {date} - {e}")
        date = datetime.now().strftime("%Y-%m-%d")

    content = parsed_result.get('내용', '내용 미지정')
    person = parsed_result.get('담당자', '담당자 미지정')

    # Notion 페이지 생성
    notion_page_url = create_notion_page(title, date, content, person)
    if notion_page_url:
        # 생성된 Notion 페이지 URL을 Slack 메시지의 쓰레드에 답변으로 전송
        post_message(
            slack_client,
            channel=channel_id,
            thread_ts=message_ts,
            text=f"✅ Notion 페이지가 성공적으로 생성되었습니다: {notion_page_url}"
        )
    else:
        # 실패 시 에러 메시지를 쓰레드에 전송
        post_message(
            slack_client,
            channel=channel_id,
            thread_ts=message_ts,
            text="❌ Notion 페이지 생성에 실패했습니다. 관리자에게 문의하세요."
        )




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

        # 날짜 처리: 날짜가 리스트인 경우 하나의 문자열로 합치기
        date_value = parsed_result.get('날짜', '날짜 미지정')
        if isinstance(date_value, list):
            date_value = ', '.join(date_value)  # 리스트일 경우 쉼표로 구분하여 합침
        
        # 딕셔너리를 문자열(JSON 형식)로 변환하고 백틱으로 감싸기
        formatted_result = (
            "```\n"  # 백틱 시작
            f"👀 제목: {parsed_result.get('제목', '제목 미지정')}\n"
            f"🤓 담당자: {parsed_result.get('담당자', '담당자 미지정')}\n"
            f"📅 날짜: {date_value}\n"  # 날짜 처리 수정
            f"📄 내용: {parsed_result.get('내용', '내용 미지정')}\n"
            "```"  # 백틱 종료
        )

        # 결과를 댓글로 포스트
        post_message(
            slack_client,
            channel=channel_id,
            thread_ts=message_ts,
            text=formatted_result
        )

 