import json
import pandas as pd
from datetime import datetime, timedelta
from slack_helper import post_message

json_path = '/Users/yujuyoung/Desktop/BRANCHIFY_BOT/Fy_bot/applications_info.json'  
with open(json_path, 'r') as file:
    data = json.load(file)
channel  = data.get('slack_channel_id')

def summarize_data_to_mrkdwn(file_path):
    data = pd.read_csv(file_path)

    data['created_time'] = pd.to_datetime(data['created_time'], errors='coerce')
    data['last_edited_time'] = pd.to_datetime(data['last_edited_time'], errors='coerce')
    data['properties.날짜.start'] = pd.to_datetime(data['properties.날짜.start'], errors='coerce')
    data['properties.날짜.end'] = pd.to_datetime(data['properties.날짜.end'], errors='coerce')

    today = datetime(2024, 11, 22).date()
    yesterday = today - timedelta(days=1)
    
    created_pages = data[data['created_time'].dt.date == yesterday]
    edited_pages = data[data['last_edited_time'].dt.date > yesterday]

    # Define relevant_date column
    def get_relevant_date(row):
        if pd.notna(row['properties.날짜.end']):
            return row['properties.날짜.end']
        return row['properties.날짜.start']

    data['relevant_date'] = data.apply(get_relevant_date, axis=1)
    data['relevant_date'] = pd.to_datetime(data['relevant_date'], errors='coerce')

    d_day = data[data['relevant_date'].dt.date == today]
    d_minus_1 = data[data['relevant_date'].dt.date == today + timedelta(days=1)]
    d_minus_2 = data[data['relevant_date'].dt.date == today + timedelta(days=2)]

    # Helper function to format tasks into HTML list items
    def format_tasks(group_data):
        tasks = []
        for _, row in group_data.iterrows():
            part = f"[{', '.join(eval(row['properties.Part']))}]" if row['properties.Part'] != '[]' else "[기타]"
            title = row['properties.이름'].strip()
            url = row['url']
            # Slack 링크 포맷 적용
            tasks.append(f"{part} <{url}|{title}>\n\n")
        return "".join(tasks)


    markdown_content = f"""
*안녕하세요 파이예요!   Notion 변경사항을 가져왔어요🤓*\n
*📅 {today.strftime('%Y-%m-%d')}*\n
*`🆕 생성된 페이지`*\n
{format_tasks(created_pages)}

*`🔧 수정된 페이지`*\n
{format_tasks(edited_pages)}

*마감기한이 다가오고 있어요🔥*\n
*`🚀 D-DAY`*\n
{format_tasks(d_day)}

*`⏳ D-1`*\n
{format_tasks(d_minus_1)}

*`⏰ D-2`*\n
{format_tasks(d_minus_2)}
"""
    return markdown_content


file_path = '/Users/yujuyoung/Desktop/BRANCHIFY_BOT/branchify_data/database_content.csv'

def send_summary(file_path, slack_client, channel):
   
    markdown_content = summarize_data_to_mrkdwn(file_path)

    response = post_message(slack_client=slack_client, channel=channel, text=markdown_content)
    if response:
        print(f"Message sent successfully: {response['ts']}")
    else:
        print("Failed to send the message.")

 