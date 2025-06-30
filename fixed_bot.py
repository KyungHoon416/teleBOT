import logging
import datetime
import sqlite3
import pytz
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters, ConversationHandler
from database import Database
from ai_helper import AIHelper
from config import BOT_TOKEN, COMMANDS, DAILY_PROMPTS, WEEKLY_PROMPTS, MONTHLY_PROMPTS, AI_REFLECTION_PROMPTS, MOTIVATIONAL_QUOTES, COMPLETION_MESSAGES

# 대화 상태 - 올바른 range() 사용
WAITING_SCHEDULE_TITLE, WAITING_SCHEDULE_DESC, WAITING_SCHEDULE_DATE, WAITING_SCHEDULE_TIME = range(4)
WAITING_DAILY_FACT, WAITING_DAILY_THINK, WAITING_DAILY_TODO = range(4, 7)
WAITING_WEEKLY_FACT, WAITING_WEEKLY_THINK, WAITING_WEEKLY_TODO, WAITING_WEEKLY_TODO_FINAL = range(7, 11)
WAITING_MONTHLY_FACT, WAITING_MONTHLY_THINK, WAITING_MONTHLY_TODO, WAITING_MONTHLY_TODO_FINAL = range(11, 15)
WAITING_FEEDBACK = range(15, 16)
WAITING_EDIT_TITLE, WAITING_EDIT_DESC, WAITING_EDIT_DATE, WAITING_EDIT_TIME = range(16, 20)
WAITING_AI_REFLECTION = range(20, 21)
WAITING_CHATGPT = range(21, 22)
WAITING_ROUTINE_TITLE, WAITING_ROUTINE_DESC, WAITING_ROUTINE_FREQ, WAITING_ROUTINE_DAYS, WAITING_ROUTINE_DATE, WAITING_ROUTINE_TIME = range(22, 28)
WAITING_VOICE_REFLECTION, WAITING_IMAGE_REFLECTION = range(28, 30)

class ScheduleBot:
    def __init__(self):
        self.db = Database()
        self.ai_helper = AIHelper()
        self.user_states = {}  # 사용자별 상태 저장
        self.ai_conversations = {}  # AI 대화 히스토리 저장
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """봇 시작 명령어"""
        user = update.effective_user
        welcome_message = f"""
🎉 안녕하세요 {user.first_name}님! 환영합니다! 👋

📅 **일정관리 & 회고 봇**에 오신 것을 환영합니다!

✨ **주요 기능:**
• 📝 일정 추가/조회/수정/삭제
• 🔄 루틴(반복 일정) 관리
• 📖 당일/주간/월간 회고 작성
• 🎤 음성/이미지 회고 (AI 분석)
• 💡 회고에 대한 피드백 제공
• 🤖 AI와 함께하는 묵상 (GPT-4o-mini)
• 💬 ChatGPT와 자유로운 대화
• 🔔 아침 8시 자동 알림
• 📢 일정 변경 시 실시간 알림
• 📊 통계 및 동기부여

🚀 **시작하기:**
/help - 모든 명령어 보기
/add_schedule - 첫 번째 일정 추가하기
/daily_reflection - 오늘 회고 작성하기

💡 **팁:** 일정을 추가/수정/삭제하면 자동으로 알림을 받을 수 있습니다!

무엇을 도와드릴까요? 😊
        """
        await update.message.reply_text(welcome_message)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /help 명령어 안내문을 더욱 세련되고, 가독성 높으며, 초보자도 한눈에 이해할 수 있도록 UX/UI를 강화한 형태로 교체합니다.
        """
        help_text = """
━━━━━━━━━━━━━━━━━━━━━━
🤖 <b>텔레그램 일정/회고/루틴/AI 봇 사용 가이드</b>
━━━━━━━━━━━━━━━━━━━━━━

<b>1️⃣ 봇 시작하기</b>
└ <code>/start</code> : 봇을 시작하고 환영 메시지를 받아보세요.

<b>2️⃣ 일정 관리</b>
└ <code>/add_schedule</code> : 새 일정 추가 (대화형 입력)
└ <code>/view_schedule</code> : 오늘의 일정 확인
└ <code>/edit_schedule</code> : 일정 수정 (목록에서 선택)
└ <code>/delete_schedule</code> : 일정 삭제 (목록에서 선택)
└ <code>/complete_schedule</code> : 일정 완료 체크 & 응원 메시지

<b>3️⃣ 루틴 관리</b>
└ <code>/add_routine</code> : 반복 루틴 등록 (예: 매주 운동)
└ <code>/view_routines</code> : 내 모든 루틴 보기
└ <code>/today_routines</code> : 오늘 해야 할 루틴만 보기

<b>4️⃣ 회고/피드백/AI</b>
└ <code>/daily_reflection</code> : 오늘 하루 회고 작성
└ <code>/feedback</code> : 회고에 대한 피드백 받기
└ <code>/ai_feedback</code> : AI가 회고를 분석해줍니다
└ <code>/routine_analysis</code> : AI가 내 루틴 패턴을 분석해줍니다

<b>5️⃣ 기타/동기부여</b>
└ <code>/motivate</code> : 랜덤 명언/동기부여 메시지
└ <code>/help</code> : 이 도움말 다시 보기

━━━━━━━━━━━━━━━━━━━━━━
<b>💡 사용 꿀팁</b>
━━━━━━━━━━━━━━━━━━━━━━
• <b>모든 명령어는 대화형 안내로 초보자도 쉽게 사용!</b><br>• 날짜는 <b>YYYY-MM-DD</b>, 시간은 <b>HH:MM</b> 형식으로 입력하세요.<br>• 잘 모르겠으면 언제든 <code>/help</code>를 입력하세요.

━━━━━━━━━━━━━━━━━━━━━━
<b>🔎 실전 예시</b>
━━━━━━━━━━━━━━━━━━━━━━
<code>/add_schedule</code> 입력 → 챗봇이 "제목을 입력하세요" 등 단계별 안내<br><code>/add_routine</code> 입력 → "루틴 제목/빈도/요일/시작일..." 순서로 안내

━━━━━━━━━━━━━━━━━━━━━━
<b>❓ 궁금한 점/문제 발생 시</b>
━━━━━━━━━━━━━━━━━━━━━━
• 언제든 <code>/help</code> 또는 <code>/start</code>로 다시 시작하세요!<br>• 입력 실수/오류 시 <code>/cancel</code>로 대화 취소 후 재시도하세요.

━━━━━━━━━━━━━━━━━━━━━━
<b>🚨 주의사항</b>
━━━━━━━━━━━━━━━━━━━━━━
• <b>개인정보/민감정보는 입력하지 마세요.</b><br>• <b>AI 기능은 OpenAI API를 사용합니다.</b>

━━━━━━━━━━━━━━━━━━━━━━
<b>🙋 무엇을 도와드릴까요?</b>
━━━━━━━━━━━━━━━━━━━━━━
"""
        await update.message.reply_text(help_text, parse_mode="HTML")
    
    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """대화 취소"""
        await update.message.reply_text("❌ 작업이 취소되었습니다.")
        return ConversationHandler.END

def main():
    """메인 함수"""
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN이 설정되지 않았습니다. .env 파일을 확인해주세요.")
        return
    
    bot = ScheduleBot()
    
    # Application 생성
    application = Application.builder().token(BOT_TOKEN).build()
    
    # 핸들러 등록
    application.add_handler(CommandHandler("start", bot.start))
    application.add_handler(CommandHandler("help", bot.help_command))
    
    # 봇 시작
    print("🤖 텔레그램 봇이 시작되었습니다...")
    if bot.ai_helper.is_available():
        print("✅ AI 기능이 활성화되었습니다.")
    else:
        print("⚠️  AI 기능이 비활성화되었습니다. OpenAI API 키를 설정해주세요.")
    
    application.run_polling()

if __name__ == '__main__':
    main() 