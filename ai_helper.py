import openai
from typing import Optional, Dict, List
from config import OPENAI_API_KEY, GPT_MODEL, MAX_TOKENS, TEMPERATURE

class AIHelper:
    def __init__(self):
        """AI 헬퍼 초기화"""
        if OPENAI_API_KEY:
            openai.api_key = OPENAI_API_KEY
            self.client = openai.OpenAI(api_key=OPENAI_API_KEY)
        else:
            self.client = None
            print("⚠️ OpenAI API 키가 설정되지 않았습니다.")
    
    def is_available(self) -> bool:
        """AI 기능 사용 가능 여부 확인"""
        return self.client is not None
    
    def get_reflection_feedback(self, reflection_content: str, reflection_type: str, user_context: str = "") -> str:
        """회고에 대한 AI 피드백 생성"""
        if not self.is_available():
            return "❌ AI 기능을 사용할 수 없습니다. OpenAI API 키를 설정해주세요."
        
        try:
            # 회고 타입별 프롬프트 설정
            type_context = {
                'daily': '일일 회고',
                'weekly': '주간 회고', 
                'monthly': '월간 회고'
            }.get(reflection_type, '회고')
            
            prompt = f"""
당신은 따뜻하고 지혜로운 멘토입니다. 사용자의 {type_context}를 읽고 다음과 같은 관점에서 피드백을 제공해주세요:

1. **긍정적 인정**: 사용자의 성취, 노력, 성장을 인정하고 격려
2. **통찰력 제공**: 회고 내용에서 발견할 수 있는 패턴이나 의미 분석
3. **실용적 조언**: 구체적이고 실현 가능한 개선 방향 제시
4. **감정적 지원**: 공감과 이해를 바탕으로 한 따뜻한 메시지

회고 내용:
{reflection_content}

사용자 컨텍스트: {user_context}

위 내용을 바탕으로 200-300자 내외의 따뜻하고 구체적인 피드백을 한국어로 제공해주세요.
"""
            
            response = self.client.chat.completions.create(
                model=GPT_MODEL,
                messages=[
                    {"role": "system", "content": "당신은 따뜻하고 지혜로운 멘토입니다. 사용자의 회고에 대해 공감적이고 실용적인 피드백을 제공합니다."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=MAX_TOKENS,
                temperature=TEMPERATURE
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"AI 피드백 생성 중 오류: {e}")
            return "❌ AI 피드백 생성 중 오류가 발생했습니다."
    
    def get_ai_reflection_guidance(self, user_input: str, conversation_history: List[Dict] = None) -> str:
        """AI와 함께하는 묵상 가이드"""
        if not self.is_available():
            return "❌ AI 기능을 사용할 수 없습니다. OpenAI API 키를 설정해주세요."
        
        try:
            # 대화 히스토리 구성
            messages = [
                {"role": "system", "content": """당신은 따뜻하고 지혜로운 묵상 동반자입니다. 
사용자의 이야기를 경청하고, 깊이 있는 질문을 통해 자기 성찰을 돕습니다.
항상 공감적이고 따뜻한 톤을 유지하며, 사용자가 자신의 생각과 감정을 더 깊이 탐색할 수 있도록 도와주세요.
답변은 200-300자 내외로 간결하면서도 의미있게 작성해주세요."""}
            ]
            
            # 대화 히스토리 추가
            if conversation_history:
                for msg in conversation_history[-6:]:  # 최근 6개 메시지만 사용
                    messages.append(msg)
            
            # 현재 사용자 입력 추가
            messages.append({"role": "user", "content": user_input})
            
            response = self.client.chat.completions.create(
                model=GPT_MODEL,
                messages=messages,
                max_tokens=MAX_TOKENS,
                temperature=TEMPERATURE
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"AI 묵상 가이드 생성 중 오류: {e}")
            return "❌ AI 묵상 가이드 생성 중 오류가 발생했습니다."
    
    def analyze_reflection_patterns(self, reflections: List[Dict]) -> str:
        """회고 패턴 분석 및 인사이트 제공"""
        if not self.is_available():
            return "❌ AI 기능을 사용할 수 없습니다. OpenAI API 키를 설정해주세요."
        
        if not reflections:
            return "분석할 회고가 없습니다."
        
        try:
            # 회고 데이터 정리
            reflection_texts = []
            for reflection in reflections[:10]:  # 최근 10개만 분석
                reflection_texts.append(f"[{reflection['date']}] {reflection['type']}: {reflection['content'][:200]}...")
            
            analysis_text = "\n".join(reflection_texts)
            
            prompt = f"""
사용자의 회고 기록을 분석하여 다음과 같은 인사이트를 제공해주세요:

1. **주요 패턴**: 자주 언급되는 주제나 감정 패턴
2. **성장 영역**: 발전하고 있는 부분이나 개선점
3. **일관성**: 회고의 일관성과 깊이
4. **추천사항**: 더 나은 회고를 위한 구체적 제안

회고 기록:
{analysis_text}

위 내용을 바탕으로 300-400자 내외의 분석 결과를 한국어로 제공해주세요.
"""
            
            response = self.client.chat.completions.create(
                model=GPT_MODEL,
                messages=[
                    {"role": "system", "content": "당신은 회고 분석 전문가입니다. 사용자의 회고 패턴을 분석하여 의미있는 인사이트를 제공합니다."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=MAX_TOKENS,
                temperature=TEMPERATURE
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"회고 패턴 분석 중 오류: {e}")
            return "❌ 회고 패턴 분석 중 오류가 발생했습니다."
    
    def get_motivational_message(self, user_context: str = "") -> str:
        """동기부여 메시지 생성"""
        if not self.is_available():
            return "❌ AI 기능을 사용할 수 없습니다. OpenAI API 키를 설정해주세요."
        
        try:
            prompt = f"""
사용자에게 따뜻하고 격려적인 동기부여 메시지를 작성해주세요.

컨텍스트: {user_context}

다음과 같은 요소를 포함해주세요:
- 긍정적이고 격려적인 톤
- 구체적이고 실용적인 조언
- 따뜻한 공감과 이해
- 희망과 가능성에 대한 메시지

100-150자 내외의 짧고 임팩트 있는 메시지로 작성해주세요.
"""
            
            response = self.client.chat.completions.create(
                model=GPT_MODEL,
                messages=[
                    {"role": "system", "content": "당신은 따뜻하고 격려적인 동기부여 전문가입니다."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.8
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"동기부여 메시지 생성 중 오류: {e}")
            return "❌ 동기부여 메시지 생성 중 오류가 발생했습니다." 