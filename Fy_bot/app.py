import json
import time
import traceback
from slack_sdk import WebClient
from slack_sdk.socket_mode import SocketModeClient
from slack_sdk.socket_mode.request import SocketModeRequest
from slack_sdk.socket_mode.response import SocketModeResponse
from event_handler import handle_reaction_added_event

json_path = '/Users/yujuyoung/Desktop/BRANCHIFY_BOT/Fy_bot/applications_info.json'  
with open(json_path, 'r') as file:
    data = json.load(file)

slack_bot_token = data.get('slack_bot_token')
slack_app_token = data.get('slack_app_token')


slack_client = WebClient(token=slack_bot_token)
socket_client = SocketModeClient(app_token=slack_app_token, web_client=slack_client)

def process_socket_mode_request(client: SocketModeClient, req: SocketModeRequest):
    try:
        # 이벤트 타입이 `reaction_added`인지 확인
        if req.type == "events_api" and req.payload["event"]["type"] == "reaction_added":
            
            handle_reaction_added_event(req.payload["event"], slack_client)
        
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

        # 무한루프
        while True:
            time.sleep(1)

    except Exception as e:
        print("An error occurred:", e)
        traceback.print_exc()