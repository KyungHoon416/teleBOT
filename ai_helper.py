import openai
import aiofiles
from typing import Optional, Dict, List, Any
from config import OPENAI_API_KEY, GPT_MODEL, MAX_TOKENS, TEMPERATURE
from openai.types.chat import ChatCompletionMessageParam
from telegram import Update
from telegram.ext import ContextTypes

class AIHelper:
    def __init__(self):
        """AI 헬퍼 초기화"""
        if OPENAI_API_KEY:
            self.client = openai.AsyncOpenAI(api_key=OPENAI_API_KEY)
        else:
            self.client = None
            print("⚠️ OpenAI API 키가 설정되지 않았습니다.")
    
    def is_available(self) -> bool:
        """AI 기능 사용 가능 여부 확인"""
        return self.client is not None
    
    async def get_reflection_feedback(self, content: str, reflection_type: str = "daily") -> str:
        """
        T형 회고를 F형(Feeling/Feedback/Forward) 회고로 변환해주는 AI 피드백 생성
        """
        if not self.is_available() or not self.client:
            return "❌ AI 피드백 기능을 사용할 수 없습니다. OpenAI API 키를 설정해주세요."
        try:
            prompt = f"""
아래는 사용자가 작성한 T형 회고입니다.

{content}

이 회고를 바탕으로, F형 회고(Feeling/Feedback/Forward) 구조로 아래와 같이 안내해줘.

1. [Feeling] 그 일에 대해 느낀 감정/마음/생각을 한 문장으로 요약해줘.
2. [Feedback] 오늘의 회고에서 얻을 수 있는 인사이트나 배울 점을 짧게 정리해줘.
3. [Forward] 실현 가능한 구체적 목표/실천 방안을 1~2가지 제안해줘.
4. 마지막으로, 현실적으로 실천할 수 있도록 따뜻한 동기부여와 실천 팁을 한 문장으로 마무리해줘.

아래 예시처럼 답변해줘:

[Feeling] ...
[Feedback] ...
[Forward] ...
[동기부여] ...
"""
            messages = [
                {"role": "system", "content": "당신은 따뜻하고 실용적인 자기성찰 코치입니다. 사용자의 회고를 F형 구조로 안내하고, 실현 가능한 목표와 동기부여를 제시합니다."},
                {"role": "user", "content": prompt}
            ]
            response = await self.client.chat.completions.create(
                model=GPT_MODEL,
                messages=messages,
                max_tokens=400,
                temperature=0.7
            )
            content = response.choices[0].message.content
            return content.strip() if content else ""
        except Exception as e:
            print(f"AI 회고 피드백 생성 오류: {e}")
            return "AI 회고 피드백 생성 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요."
    
    async def get_ai_reflection_guidance(self, user_input: str, conversation_history: Optional[List[Dict[str, Any]]] = None) -> str:
        """AI와 함께하는 묵상 가이드"""
        if not self.is_available() or not self.client:
            return "❌ AI 기능을 사용할 수 없습니다. OpenAI API 키를 설정해주세요."
        
        try:
            # 대화 히스토리 구성
            messages: List[ChatCompletionMessageParam] = [
                {"role": "system", "content": """당신은 따뜻하고 지혜로운 묵상 동반자입니다. 
사용자의 이야기를 경청하고, 깊이 있는 질문을 통해 자기 성찰을 돕습니다.
항상 공감적이고 따뜻한 톤을 유지하며, 사용자가 자신의 생각과 감정을 더 깊이 탐색할 수 있도록 도와주세요.
답변은 200-300자 내외로 간결하면서도 의미있게 작성해주세요."""}
            ]
            
            # 대화 히스토리 추가
            if conversation_history:
                for msg in conversation_history[-6:]:  # 최근 6개 메시지만 사용
                    if isinstance(msg, dict) and "role" in msg and "content" in msg:
                        messages.append({"role": msg["role"], "content": msg["content"]})
            
            # 현재 사용자 입력 추가
            messages.append({"role": "user", "content": user_input})
            
            response = await self.client.chat.completions.create(
                model=GPT_MODEL,
                messages=messages,
                max_tokens=MAX_TOKENS,
                temperature=TEMPERATURE
            )
            
            content = response.choices[0].message.content
            return content.strip() if content else ""
            
        except Exception as e:
            print(f"AI 묵상 가이드 생성 중 오류: {e}")
            if "billing_not_active" in str(e):
                return "💡 AI 묵상을 사용하려면 OpenAI 계정의 결제 정보를 설정해주세요.\n\n📝 대신 기본 묵상 가이드를 제공해드릴게요:\n\n당신의 이야기를 들려주셔서 감사합니다. 자기 성찰은 정말 중요한 시간이에요. 더 깊이 있는 대화를 원하시면 OpenAI 계정 설정 후 다시 시도해보세요! 🙏"
            else:
                return "💡 AI 묵상 생성 중 일시적인 오류가 발생했습니다.\n\n📝 대신 기본 묵상 가이드를 제공해드릴게요:\n\n당신의 이야기를 들려주셔서 감사합니다. 자기 성찰은 정말 중요한 시간이에요. 잠시 후 다시 시도해보시거나, 다른 방법으로 자기 성찰을 이어가보세요! 🙏"
    
    async def analyze_reflection_patterns(self, reflections: List[Dict]) -> str:
        """회고 패턴 분석 및 인사이트 제공"""
        if not self.is_available() or not self.client:
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
            
            messages: List[ChatCompletionMessageParam] = [
                {"role": "system", "content": "당신은 회고 분석 전문가입니다. 사용자의 회고 패턴을 분석하여 의미있는 인사이트를 제공합니다."},
                {"role": "user", "content": prompt}
            ]
            
            response = await self.client.chat.completions.create(
                model=GPT_MODEL,
                messages=messages,
                max_tokens=MAX_TOKENS,
                temperature=TEMPERATURE
            )
            
            content = response.choices[0].message.content
            return content.strip() if content else ""
            
        except Exception as e:
            print(f"회고 패턴 분석 중 오류: {e}")
            if "billing_not_active" in str(e):
                return "💡 회고 패턴 분석을 사용하려면 OpenAI 계정의 결제 정보를 설정해주세요.\n\n📝 대신 기본 분석을 제공해드릴게요:\n\n회고를 꾸준히 작성하고 계시는 모습이 정말 인상적입니다! 패턴 분석을 원하시면 OpenAI 계정 설정 후 다시 시도해보세요. 지금도 충분히 의미있는 회고를 작성하고 계세요! 📊"
            else:
                return "💡 회고 패턴 분석 중 일시적인 오류가 발생했습니다.\n\n📝 대신 기본 분석을 제공해드릴게요:\n\n회고를 꾸준히 작성하고 계시는 모습이 정말 인상적입니다! 잠시 후 다시 시도해보시거나, 지금도 충분히 의미있는 회고를 작성하고 계세요! 📊"
    
    async def get_motivational_message(self, user_context: str = "") -> str:
        """동기부여 메시지 생성"""
        if not self.is_available() or not self.client:
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
            
            messages: List[ChatCompletionMessageParam] = [
                {"role": "system", "content": "당신은 따뜻하고 격려적인 동기부여 전문가입니다."},
                {"role": "user", "content": prompt}
            ]
            
            response = await self.client.chat.completions.create(
                model=GPT_MODEL,
                messages=messages,
                max_tokens=300,
                temperature=0.8
            )
            
            content = response.choices[0].message.content
            return content.strip() if content else ""
            
        except Exception as e:
            print(f"동기부여 메시지 생성 중 오류: {e}")
            if "billing_not_active" in str(e):
                return "💡 AI 동기부여 메시지를 사용하려면 OpenAI 계정의 결제 정보를 설정해주세요.\n\n📝 대신 기본 메시지를 제공해드릴게요:\n\n당신은 정말 대단한 사람입니다! 매일 조금씩이라도 성장하려는 모습이 정말 멋져요. 오늘도 힘내세요! 💪✨"
            else:
                return "💡 AI 동기부여 메시지 생성 중 일시적인 오류가 발생했습니다.\n\n📝 대신 기본 메시지를 제공해드릴게요:\n\n당신은 정말 대단한 사람입니다! 매일 조금씩이라도 성장하려는 모습이 정말 멋져요. 오늘도 힘내세요! 💪✨"
    
    async def chat_with_gpt(self, user_message: str, conversation_history: Optional[List[Dict[str, Any]]] = None) -> str:
        """ChatGPT와 일반 대화"""
        if not self.is_available() or not self.client:
            return "❌ AI 기능을 사용할 수 없습니다. OpenAI API 키를 설정해주세요."
        
        try:
            # 대화 히스토리 구성
            messages: List[ChatCompletionMessageParam] = [
                {"role": "system", "content": """당신은 친근하고 도움이 되는 AI 어시스턴트입니다.
사용자의 질문이나 대화에 대해 정확하고 유용한 답변을 제공합니다.
한국어로 대화하며, 필요시 영어로도 답변할 수 있습니다.
답변은 명확하고 이해하기 쉽게 작성해주세요."""}
            ]
            
            # 대화 히스토리 추가 (최근 10개 메시지만 사용)
            if conversation_history:
                for msg in conversation_history[-10:]:
                    if isinstance(msg, dict) and "role" in msg and "content" in msg:
                        messages.append({"role": msg["role"], "content": msg["content"]})
            
            # 현재 사용자 메시지 추가
            messages.append({"role": "user", "content": user_message})
            
            response = await self.client.chat.completions.create(
                model=GPT_MODEL,
                messages=messages,
                max_tokens=MAX_TOKENS,
                temperature=TEMPERATURE
            )
            
            content = response.choices[0].message.content
            return content.strip() if content else ""
            
        except Exception as e:
            print(f"ChatGPT 대화 중 오류: {e}")
            if "billing_not_active" in str(e):
                return "💡 ChatGPT와 대화하려면 OpenAI 계정의 결제 정보를 설정해주세요.\n\n📝 대신 기본 응답을 제공해드릴게요:\n\n안녕하세요! ChatGPT와 대화를 원하시는군요. OpenAI 계정 설정 후 다시 시도해보세요! 🤖"
            else:
                return "💡 ChatGPT 대화 중 일시적인 오류가 발생했습니다.\n\n📝 잠시 후 다시 시도해보시거나, 다른 기능을 이용해보세요! 🤖"
    
    async def get_completion_motivation(self, schedule_title: str) -> str:
        """일정 완료 시 AI 동기부여 메시지 생성"""
        if not self.is_available() or not self.client:
            return ""
        
        try:
            prompt = f"""
사용자가 "{schedule_title}" 일정을 완료했습니다. 
따뜻하고 격려적인 동기부여 메시지를 50-80자 내외로 한국어로 작성해주세요.

메시지는:
- 성취를 축하하는 톤
- 구체적이고 개인화된 내용
- 미래에 대한 긍정적 격려
- 따뜻하고 공감적인 어조

를 포함해야 합니다.
"""
            
            messages: List[ChatCompletionMessageParam] = [
                {"role": "system", "content": "당신은 따뜻하고 격려적인 멘토입니다. 사용자의 성취를 축하하고 동기부여를 제공합니다."},
                {"role": "user", "content": prompt}
            ]
            
            response = await self.client.chat.completions.create(
                model=GPT_MODEL,
                messages=messages,
                max_tokens=100,
                temperature=0.8
            )
            
            content = response.choices[0].message.content
            return content.strip() if content else ""
        
        except Exception as e:
            print(f"AI 완료 동기부여 생성 오류: {e}")
            return ""
    
    async def get_schedule_summary(self, schedules: List[Dict]) -> str:
        """일정 데이터 기반 AI 요약/분석"""
        if not self.is_available() or not self.client:
            return "❌ AI 기능을 사용할 수 없습니다. OpenAI API 키를 설정해주세요."
        
        if not schedules:
            return "분석할 일정이 없습니다."
        
        try:
            # 일정 데이터 정리
            schedule_texts = []
            for schedule in schedules[:20]:  # 최근 20개만 분석
                status = "✅ 완료" if schedule.get('is_done') else "⏳ 진행중"
                schedule_texts.append(f"[{schedule['date']}] {schedule['title']} - {status}")
            
            analysis_text = "\n".join(schedule_texts)
            
            prompt = f"""
사용자의 일정 기록을 분석하여 다음과 같은 인사이트를 제공해주세요:

1. **일정 패턴**: 자주 등록하는 일정 유형이나 시간대
2. **완료율 분석**: 전체적인 일정 완료율과 개선점
3. **생산성 인사이트**: 가장 생산적인 시간대나 일정 유형
4. **개선 제안**: 더 나은 일정 관리를 위한 구체적 제안

일정 기록:
{analysis_text}

위 내용을 바탕으로 300-400자 내외의 분석 결과를 한국어로 제공해주세요.
"""
            
            messages: List[ChatCompletionMessageParam] = [
                {"role": "system", "content": "당신은 일정 관리 전문가입니다. 사용자의 일정 패턴을 분석하여 의미있는 인사이트를 제공합니다."},
                {"role": "user", "content": prompt}
            ]
            
            response = await self.client.chat.completions.create(
                model=GPT_MODEL,
                messages=messages,
                max_tokens=MAX_TOKENS,
                temperature=TEMPERATURE
            )
            
            content = response.choices[0].message.content
            return content.strip() if content else ""
        
        except Exception as e:
            print(f"AI 일정 요약 분석 오류: {e}")
            return "❌ AI 분석 중 오류가 발생했습니다."
    
    async def transcribe_voice(self, voice_file_path: str) -> str:
        """음성을 텍스트로 변환 (OpenAI Whisper)"""
        if not self.is_available() or not self.client:
            return ""
        
        try:
            async with aiofiles.open(voice_file_path, "rb") as audio_file:
                audio_bytes = await audio_file.read()
            import io
            audio_stream = io.BytesIO(audio_bytes)
            if hasattr(self.client, "audio") and hasattr(self.client.audio, "transcriptions"):
                transcript = await self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_stream
                )
                return transcript.text if transcript and hasattr(transcript, 'text') else ""
            else:
                return ""
        except Exception as e:
            print(f"음성 변환 오류: {e}")
            return ""
    
    async def analyze_voice_reflection(self, transcription: str) -> str:
        """음성 회고 분석"""
        if not self.is_available() or not self.client:
            return "❌ AI 기능을 사용할 수 없습니다. OpenAI API 키를 설정해주세요."
        
        try:
            prompt = f"""
사용자의 음성 회고를 분석하여 다음과 같은 내용을 제공해주세요:

1. **주요 내용 요약**: 음성에서 언급된 주요 사건이나 감정
2. **감정 분석**: 사용자의 감정 상태와 톤 분석
3. **인사이트**: 음성 내용에서 발견할 수 있는 패턴이나 의미
4. **제안사항**: 개선점이나 다음 단계에 대한 제안

음성 내용:
{transcription}

위 내용을 바탕으로 200-300자 내외의 분석 결과를 한국어로 제공해주세요.
"""
            
            messages: List[ChatCompletionMessageParam] = [
                {"role": "system", "content": "당신은 음성 회고 분석 전문가입니다. 사용자의 음성 내용을 분석하여 의미있는 인사이트를 제공합니다."},
                {"role": "user", "content": prompt}
            ]
            
            response = await self.client.chat.completions.create(
                model=GPT_MODEL,
                messages=messages,
                max_tokens=MAX_TOKENS,
                temperature=TEMPERATURE
            )
            
            content = response.choices[0].message.content
            return content.strip() if content else ""
        
        except Exception as e:
            print(f"음성 회고 분석 오류: {e}")
            return "❌ 음성 분석 중 오류가 발생했습니다."
    
    async def analyze_image_reflection(self, image_file_path: str) -> str:
        """이미지 회고 분석 (OpenAI Vision)"""
        if not self.is_available() or not self.client:
            return "❌ AI 기능을 사용할 수 없습니다. OpenAI API 키를 설정해주세요."
        
        try:
            import base64
            
            # 이미지 파일을 base64로 인코딩
            async with aiofiles.open(image_file_path, "rb") as image_file:
                image_bytes = await image_file.read()
            base64_image = base64.b64encode(image_bytes).decode('utf-8')
            
            prompt = """
이 이미지를 회고 관점에서 분석해주세요:

1. **이미지 내용**: 이미지에 무엇이 보이는지
2. **감정적 의미**: 이 이미지가 전달하는 감정이나 분위기
3. **회고적 관점**: 이 이미지가 사용자의 하루나 삶에서 어떤 의미를 가지는지
4. **인사이트**: 이미지를 통해 발견할 수 있는 패턴이나 깨달음

회고적이고 성찰적인 관점에서 분석해주세요.
"""
            
            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=MAX_TOKENS,
                temperature=TEMPERATURE
            )
            
            return response.choices[0].message.content.strip()
        
        except Exception as e:
            print(f"이미지 분석 오류: {e}")
            return "❌ 이미지 분석 중 오류가 발생했습니다."
    
    async def feedback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """최근 회고에 대한 AI 피드백 제공"""
        user_id = update.effective_user.id
        # 최근 회고 가져오기
        reflections = self.db.get_reflections(user_id)
        if not reflections:
            await update.message.reply_text("최근 회고가 없습니다. 먼저 회고를 작성해 주세요.")
            return
        last_reflection = reflections[0]
        content = last_reflection['content']
        reflection_type = last_reflection.get('type', 'daily')
        # AI 피드백 생성
        if self.ai_helper.is_available():
            feedback_text = await self.ai_helper.get_reflection_feedback(content, reflection_type)
        else:
            feedback_text = "AI 피드백 기능이 비활성화되어 있습니다."
        await update.message.reply_text(f"📝 최근 회고:\n{content}\n\n💡 AI 피드백:\n{feedback_text}") 