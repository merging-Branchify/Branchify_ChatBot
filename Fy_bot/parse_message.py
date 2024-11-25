import re
from soynlp.tokenizer import LTokenizer


def parsing_message(message):
    """
    Slack 메시지를 분석하여 날짜, 담당자, 내용을 추출합니다.
    
    Args:
        message (str): Slack 메시지 텍스트.
        
    Returns:
        dict: 메시지에서 추출된 정보를 담은 딕셔너리.
    """
    # 형태소 분석기 로드
    okt = LTokenizer()
    
    # 담당자 추출 (정규 표현식 기반)
    person_pattern = r"@(\w+)"
    person_match = re.search(person_pattern, message)
    if person_match:
        person = person_match.group(1).replace("님", "")  # "님" 제거
    else:
        person = "담당자 미지정"
    
    # 날짜 추출
    date_pattern = r"(\d+월 \d+일)|(\d+/\d+)|(\d+\.\d+)"
    dates = re.findall(date_pattern, message)
    dates = [date[0] for date in dates if date[0]]  # 매칭된 첫 번째 그룹만 추출
    
    # 텍스트에서 담당자와 날짜 제거
    clean_message = re.sub(person_pattern, "", message)  # @이름 제거
    clean_message = re.sub(date_pattern, "", clean_message)  # 날짜 제거
    clean_message = re.sub(r"까지", "", clean_message)  # 불필요한 문구 제거

    clean_message = clean_message.strip()

    # 내용 생성
    content = clean_message if clean_message else "내용 미지정"

    # 결과 정리
    result = {
        "제목": "제목 미지정",  # 제목은 사용자가 지정하도록 비워둠
        "담당자": person,
        "날짜": dates if dates else ["날짜 미지정"],
        "내용": content.strip()
    }
    
    return result


def dict_to_slack_table(data):
    """
    딕셔너리를 Slack 모노스페이스 텍스트 블록 내에서 테이블로 변환합니다.
    테이블의 각 모서리를 '+'로 감쌉니다.

    Args:
        data (dict): 표로 변환할 데이터 딕셔너리.

    Returns:
        str: Slack 마크다운 형식의 테이블 문자열.
    """
    # 열 너비 설정
    key_width = 10  # 항목 열의 너비
    value_width = 40  # 내용 열의 너비

    # 테이블 헤더
    border = f"+{'-' * key_width}+{'-' * value_width}+"
    header = f"|{'항목':^{key_width}}|{'내용':^{value_width}}|"
    
    # 테이블 내용
    rows = []
    for key, value in data.items():
        # 리스트나 여러 값일 경우 쉼표로 구분
        if isinstance(value, list):
            value = ", ".join(map(str, value))
        rows.append(f"|{key:<{key_width}}|{value:<{value_width}}|")

    # 최종 테이블 조합
    table = "```\n"  # Slack의 모노스페이스 텍스트 블록
    table += border + "\n"  # 상단 테두리
    table += header + "\n"  # 헤더
    table += border + "\n"  # 헤더 아래 테두리
    table += "\n".join(rows) + "\n"  # 내용
    table += border + "\n"  # 하단 테두리
    table += "```"

    return table


message = " @파이님, 랜딩페이지 QA와 수정 작업을 진행해 주세요. 마감 기한은 2024년 11월 22일 오후 6시까지입니다. 랜딩페이지의 모바일과 데스크탑 환경에서 디자인 오류나 기능 이상 여부를 확인한 후, 발견된 문제를 노션의 QA 데이터베이스에 정리해 공유해 주세요. 특히 주요 오류인 화면 깨짐이나 링크 비활성화 문제는 11월 21일까지 개발팀과 논의해 수정 완료해 주시기 바랍니다. 감사합니다!"

parsed_result = parsing_message(message)

# Slack 표 형식으로 변환
slack_table = dict_to_slack_table(parsed_result)

# # 출력 결과
# print(slack_table)