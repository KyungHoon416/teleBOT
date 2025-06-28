import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Token
BOT_TOKEN = os.getenv('BOT_TOKEN')

# OpenAI API Key
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Database
DATABASE_PATH = 'schedule_bot.db'

# Bot Commands
COMMANDS = {
    'start': '봇 시작하기',
    'help': '도움말 보기',
    'add_schedule': '일정 추가하기',
    'view_schedule': '일정 보기',
    'edit_schedule': '일정 수정하기',
    'delete_schedule': '일정 삭제하기',
    'daily_reflection': '오늘 회고 작성하기',
    'weekly_reflection': '주간 회고 작성하기',
    'monthly_reflection': '월간 회고 작성하기',
    'view_reflections': '회고 보기',
    'feedback': '피드백 받기',
    'ai_reflection': 'AI와 함께 묵상하기',
    'ai_feedback': 'AI 피드백 받기'
}

# Reflection prompts
DAILY_PROMPTS = [
    "오늘 가장 기억에 남는 일은 무엇인가요?",
    "오늘 배운 것이 있다면 무엇인가요?",
    "내일은 무엇을 개선하고 싶나요?",
    "오늘 감사한 일이 있나요?"
]

WEEKLY_PROMPTS = [
    "이번 주 가장 성취감을 느낀 일은 무엇인가요?",
    "이번 주 어려웠던 일과 어떻게 극복했나요?",
    "다음 주 목표는 무엇인가요?",
    "이번 주 배운 교훈이 있다면 무엇인가요?"
]

MONTHLY_PROMPTS = [
    "이번 달 가장 큰 변화는 무엇이었나요?",
    "이번 달 목표 달성률은 어느 정도인가요?",
    "다음 달에 집중하고 싶은 영역은 무엇인가요?",
    "이번 달을 한 문장으로 요약한다면?"
]

# AI Reflection prompts
AI_REFLECTION_PROMPTS = [
    "오늘 하루에 대해 자유롭게 이야기해주세요. 어떤 일들이 있었나요?",
    "특별히 생각해보고 싶은 주제나 고민이 있나요?",
    "지금 마음속에 떠오르는 감정이나 생각이 있나요?",
    "오늘 하루를 돌아보며 느낀 점이나 깨달은 것이 있나요?"
]

# GPT-4o-mini 설정
GPT_MODEL = "gpt-4o-mini"
MAX_TOKENS = 1000
TEMPERATURE = 0.7 