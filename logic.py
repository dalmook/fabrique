    json_path = 'D:\Workspace\output.json'
    try:
        # info.txt 파일 읽기
        with open(json_path, 'r', encoding='utf-8') as file:
            knowledge_list = json.load(file)
        # 모든 문자열에서 '\xa0' 제거
        def clean_data(data):
            if isinstance(data, str):
                return data.replace('\xa0', ' ')
            elif isinstance(data, list):
                return [clean_data(item) for item in data]
            elif isinstance(data, dict):
                return {key: clean_data(value) for key, value in data.items()}
            return data            
            
        knowledge_list = clean_data(knowledge_list)
        # 검색어가 포함된 term 목록 필터링
        scored_results = []
        for item in knowledge_list:
            term = item["title"]
            similarity = self.calculate_similarity(query, term)
            if query.lower() in term.lower():
                subject = item["subject"]
                explanation = item["content"]
                link = item["link"]
                scored_results.append((similarity, subject, term, explanation, link))                    
                    
        # 완전 일치 항목과 유사도 기반 항목 분리
        exact_matches = [result for result in scored_results if result[2] == query]
        similar_matches = [result for result in scored_results if result[2] != query]
        
        
        # 유사도 순으로 정렬 후 상위 10개 선택
        similar_matches = sorted(similar_matches, key=lambda x: x[0], reverse=True)[:15]
        
        # 유사도 제거하고 최종 결과 구성
        results = [(subject, term, explanation, link) for _, subject, term, explanation, link in exact_matches + similar_matches]
       
        if results:
            # 검색된 term 목록을 Adaptive Card로 출력
            self.gocwordfindresult = self.generate_adaptive_card_for_subjects(results)          
            return self.generate_adaptive_card_for_subjects(results)
        else:
            chatBot.chatRequest('169006360833360896', f'조회자 [ {search_subjects} ] [ {query} ] <-- 없는 단어입니다.')           
            chatBot.chatRequest('169658552700961792', f'[ {search_subjects} ] [ {query} ] <-- 없는 단어입니다.')
            self.gocwordfindresult = {
    "type": "AdaptiveCard",
    "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
    "version": "1.3",
    "body": [
        {
            "type": "TextBlock",
            "text": f"[ {query} ]에 대한 검색결과가 없습니다.\n\n담당자에게 전송 후 반영하도록 하겠습니다.",
            "wrap": True
        },
        {
            "type": "ColumnSet",
            "columns": [
                {
                    "type": "Column",
                    "width": "stretch",
                    "items": [
                        {
                            "type": "Input.Text",
                            "placeholder": "아래 내용 입력 후 전송 눌러주세요!",
                            "id": "gocwordidonknow01"
                        }
                    ]
                }
            ]
        },
        {
            "type": "ColumnSet",
            "columns": [
                {
                    "type": "Column",
                    "width": "stretch",
                    "items": [
                        {
                            "type": "ActionSet",
                            "actions": [
                                {
                                    "type": "Action.Submit",
                                    "title": "전송",
                                    "style": "positive",
                                    "data": {
                                        "action": "goc용어사전모르는단어",
                                        "findword" : f"{query}"
                                    }
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    ]
}
            return "검색 결과가 없습니다."
        
    except FileNotFoundError:
        return "파일을 찾을 수 없습니다."
    except Exception as e:
        return f"오류가 발생했습니다: {e}"
