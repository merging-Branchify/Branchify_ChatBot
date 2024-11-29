import re
from soynlp.tokenizer import LTokenizer


def parsing_message(message):
    """
    Slack 메시지를 분석하여 제목, 날짜, 담당자, 내용을 추출합니다.
    
    Args:
        message (str): Slack 메시지 텍스트.
        
    Returns:
        dict: 메시지에서 추출된 정보를 담은 딕셔너리.
    """
    # Soynlp 토크나이저 초기화
    tokenizer = LTokenizer()

    # 담당자 추출 (정규 표현식 기반)
    person_pattern = r"@(\w+)"
    person_match = re.search(person_pattern, message)
    if person_match:
        person = person_match.group(1).replace("님", "")  # "님" 제거
    else:
        person = "담당자 미지정"
    
    # 날짜 추출
    date_pattern = r"(\d{1,2}월 \d{1,2}일)|(\d{1,2}/\d{1,2})|(\d{1,2}\.\d{1,2})"
    date_match = re.search(date_pattern, message)
    if date_match:
        date = date_match.group(0)
    else:
        date = "날짜 미지정"
    
    # 담당자와 날짜, "해주세요" 제거
    clean_message = re.sub(person_pattern, "", message)  # @이름 제거
    clean_message = re.sub(date_pattern, "", clean_message)  # 날짜 제거
    clean_message = re.sub(r"까지|님|,|\.|해주세요|\s{2,}", "", clean_message)  # "해주세요", "님", "까지" 등 제거
    
    # 제목을 메시지에서 남은 내용의 첫 부분을 제목으로 설정 (최대 3개 단어)
    title = ' '.join(clean_message.split()[:3])  # 첫 3개의 단어를 제목으로 설정
    
    # 내용 생성
    content = clean_message.strip() if clean_message else "내용 미지정"
    
    # 결과 정리
    result = {
        "제목": title,
        "담당자": person,
        "날짜": date,
        "내용": f"{date}까지 {content}"
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


message = " @영지님, 11월 27일까지 api 명세서 최종 점검하고 보고해주세요."

parsed_result = parsing_message(message)


# # 출력 결과
#print(parsed_result)