import json
import time
import traceback
from slack_sdk import WebClient
from slack_sdk.socket_mode import SocketModeClient
from slack_sdk.socket_mode.request import SocketModeRequest
from slack_sdk.socket_mode.response import SocketModeResponse
from event_handler import handle_reaction_added_event
from summarize import send_summary

file_path = '/Users/yujuyoung/Desktop/BRANCHIFY_BOT/branchify_data/database_content.csv'


json_path = '/Users/yujuyoung/Desktop/BRANCHIFY_BOT/Fy_bot/applications_info.json'  
with open(json_path, 'r') as file:
    data = json.load(file)

slack_bot_token = data.get('slack_bot_token')
slack_app_token = data.get('slack_app_token')
slack_channel = data.get('slack_channel_id')

#슬랙 클라이언트
slack_client = WebClient(token=slack_bot_token)
socket_client = SocketModeClient(app_token=slack_app_token, web_client=slack_client)

# 노션 클라이언트
notion_api_token = data.get('notion_token')
notion_client = {
    "base_url": "https://api.notion.com/v1",
    "token": notion_api_token,
    "headers": {
        "Authorization": f"Bearer {notion_api_token}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
}

def process_socket_mode_request(client: SocketModeClient, req: SocketModeRequest):
    try:
        # 이벤트 타입이 `reaction_added`인지 확인
        if req.type == "events_api" and req.payload["event"]["type"] == "reaction_added":
            # slack과 notion 처리
            handle_reaction_added_event(req.payload["event"], slack_client, notion_client)
        
        # 슬랙 이벤트 수신 
        client.send_socket_mode_response(SocketModeResponse(envelope_id=req.envelope_id))
    
    except Exception as e:
        print(f"Error processing request: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    try:
        print("Connecting to Slack...")
        socket_client.socket_mode_request_listeners.append(process_socket_mode_request)
        socket_client.connect()
        print("Connected to Slack")
        #send_summary(file_path, slack_client, slack_channel)

        # 무한루프
        while True:
            time.sleep(1)

    except Exception as e:
        print("An error occurred:", e)
        traceback.print_exc()