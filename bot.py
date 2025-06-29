import logging
import datetime
import sqlite3
import pytz
import random
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters, ConversationHandler
from database import Database
from ai_helper import AIHelper
from config import BOT_TOKEN, COMMANDS, DAILY_PROMPTS, WEEKLY_PROMPTS, MONTHLY_PROMPTS, AI_REFLECTION_PROMPTS, MOTIVATIONAL_QUOTES, COMPLETION_MESSAGES

# 로깅 설정
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

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
        if not update.effective_user or not update.message:
            return
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
/start - 봇 시작
/help - 모든 명령어 보기
/add_schedule - 첫 번째 일정 추가하기
/daily_reflection - 오늘 회고 작성하기

💡 **팁:** 일정을 추가/수정/삭제하면 자동으로 알림을 받을 수 있습니다!

무엇을 도와드릴까요? 😊
        """
        await update.message.reply_text(welcome_message)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """도움말 명령어"""
        if not update.message:
            return
        help_text = """
📋 **사용 가능한 명령어**

📅 **일정 관리**
/add_schedule - 새로운 일정 추가
/view_schedule - 일정 목록 보기
/edit_schedule - 일정 수정하기
/delete_schedule - 일정 삭제하기

🔄 **루틴 관리**
/add_routine - 새로운 루틴 추가
/view_routines - 루틴 목록 보기
/today_routines - 오늘의 루틴 보기

🔔 **알림 기능**
• 일정 추가/수정/삭제 시 자동 알림
• 매일 아침 8시 일정 알림
• 일정 완료 시 응원 메시지

📖 **회고 작성**
/daily_reflection - 오늘 하루 회고 (T형)
/weekly_reflection - 이번 주 회고 (T형)
/monthly_reflection - 이번 달 회고 (T형)
/voice_reflection - 음성 회고 (AI 음성 분석)
/image_reflection - 이미지 회고 (AI 이미지 분석)
/view_reflections - 작성한 회고 보기

💡 **피드백 & 분석**
/feedback - 회고에 대한 피드백 받기
/ai_feedback - AI 피드백 받기
/ai_pattern_analysis - AI 회고 패턴 분석
/ai_schedule_summary - AI 일정 요약/분석

🤖 **AI 기능**
/ai_reflection - AI와 함께 묵상하기
/chatgpt - ChatGPT와 자유로운 대화하기

📊 **통계 & 동기부여**
/stats - 주간/월간 일정/회고 통계
/motivate - 명언/동기부여 랜덤 전송

❓ **기타**
/help - 이 도움말 보기
        """
        await update.message.reply_text(help_text)
    
    async def add_schedule(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """일정 추가 시작"""
        if not update.message:
            return ConversationHandler.END
        await update.message.reply_text("📝 일정의 제목을 입력해주세요:")
        return WAITING_SCHEDULE_TITLE
    
    async def schedule_title(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """일정 제목 입력 처리"""
        if not update.effective_user or not update.message:
            return ConversationHandler.END
        user_id = update.effective_user.id
        title = update.message.text
        
        self.user_states[user_id] = {'title': title}
        await update.message.reply_text("📄 일정에 대한 설명을 입력해주세요 (선택사항):")
        return WAITING_SCHEDULE_DESC
    
    async def schedule_description(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """일정 설명 입력 처리"""
        if not update.effective_user or not update.message:
            return ConversationHandler.END
        user_id = update.effective_user.id
        description = update.message.text
        
        self.user_states[user_id]['description'] = description
        await update.message.reply_text("📅 일정 날짜를 입력해주세요 (YYYY-MM-DD 형식):")
        return WAITING_SCHEDULE_DATE
    
    async def schedule_date(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """일정 날짜 입력 처리"""
        if not update.effective_user or not update.message:
            return ConversationHandler.END
        user_id = update.effective_user.id
        date_text = update.message.text
        
        try:
            # 날짜 형식 검증
            datetime.datetime.strptime(date_text, '%Y-%m-%d')
            self.user_states[user_id]['date'] = date_text
            await update.message.reply_text("⏰ 일정 시간을 입력해주세요 (HH:MM 형식, 선택사항):")
            return WAITING_SCHEDULE_TIME
        except ValueError:
            await update.message.reply_text("❌ 잘못된 날짜 형식입니다. YYYY-MM-DD 형식으로 입력해주세요.")
            return WAITING_SCHEDULE_DATE
    
    async def schedule_time(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """일정 시간 입력 처리 및 저장"""
        if not update.effective_user or not update.message:
            return ConversationHandler.END
        user_id = update.effective_user.id
        time_text = update.message.text
        try:
            if time_text.strip():
                # 시간 형식 검증
                datetime.datetime.strptime(time_text, '%H:%M')
                time = time_text
            else:
                time = None
            # 일정 저장
            state = self.user_states[user_id]
            success = self.db.add_schedule(
                user_id=user_id,
                title=state['title'],
                description=state['description'],
                date=state['date'],
                time=time
            )
            if success:
                await update.message.reply_text("✅ 일정이 성공적으로 추가되었습니다!")
            else:
                await update.message.reply_text("❌ 일정 추가 중 오류가 발생했습니다.")
            # 상태 초기화
            if user_id in self.user_states:
                del self.user_states[user_id]
            return ConversationHandler.END
        except ValueError:
            await update.message.reply_text("❌ 잘못된 시간 형식입니다. HH:MM 형식으로 입력해주세요.")
            return WAITING_SCHEDULE_TIME
    
    async def view_schedule(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """일정 조회"""
        if not update.effective_user or not update.message:
            return
        user_id = update.effective_user.id
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        today_schedules = self.db.get_schedules(user_id, today)
        if not today_schedules:
            await update.message.reply_text("📅 오늘 등록된 일정이 없습니다.")
            return
        for schedule in today_schedules:
            time_str = f"⏰ {schedule['time']} " if schedule['time'] else ""
            desc_str = f"\n  📄 {schedule['description']}" if schedule['description'] else ""
            msg = f"• {time_str}{schedule['title']}{desc_str}"
            await update.message.reply_text(msg)
    
    async def daily_reflection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """일일 회고(T형) 시작"""
        if not update.effective_user or not update.message:
            return ConversationHandler.END
        user_id = update.effective_user.id
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        existing_reflections = self.db.get_reflections(user_id, 'daily', today)
        if existing_reflections:
            await update.message.reply_text("📖 오늘 이미 회고를 작성하셨습니다. 수정하시겠습니까?")
            return ConversationHandler.END
        context.user_data['reflection'] = {}
        await update.message.reply_text("1️⃣ 오늘 있었던 일(사실)을 적어주세요!")
        return WAITING_DAILY_FACT

    async def daily_fact(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message:
            return ConversationHandler.END
        context.user_data['reflection']['fact'] = update.message.text
        await update.message.reply_text("2️⃣ 그 일에 대해 어떻게 생각하셨나요?")
        return WAITING_DAILY_THINK

    async def daily_think(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message:
            return ConversationHandler.END
        context.user_data['reflection']['think'] = update.message.text
        await update.message.reply_text("3️⃣ 내일은 무엇을 실천하고 싶으신가요?")
        return WAITING_DAILY_TODO

    async def daily_todo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.effective_user or not update.message:
            return ConversationHandler.END
        user_id = update.effective_user.id
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        context.user_data['reflection']['todo'] = update.message.text
        r = context.user_data['reflection']
        content = f"[사실] {r['fact']}\n[생각] {r['think']}\n[실천] {r['todo']}"
        success = self.db.add_reflection(user_id, 'daily', content, today)
        if success:
            await update.message.reply_text("✅ 오늘의 T형 회고가 저장되었습니다!")
        else:
            await update.message.reply_text("❌ 회고 저장 중 오류가 발생했습니다.")
        context.user_data['reflection'] = {}
        return ConversationHandler.END
    
    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """대화 취소"""
        user_id = update.effective_user.id
        if user_id in self.user_states:
            del self.user_states[user_id]
        if user_id in self.ai_conversations:
            del self.ai_conversations[user_id]
        
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
    
    # 일정 추가 대화 핸들러
    schedule_handler = ConversationHandler(
        entry_points=[CommandHandler('add_schedule', bot.add_schedule)],
        states={
            WAITING_SCHEDULE_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.schedule_title)],
            WAITING_SCHEDULE_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.schedule_description)],
            WAITING_SCHEDULE_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.schedule_date)],
            WAITING_SCHEDULE_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.schedule_time)],
        },
        fallbacks=[CommandHandler('cancel', bot.cancel)]
    )
    
    # 회고 작성 대화 핸들러
    reflection_handler = ConversationHandler(
        entry_points=[CommandHandler('daily_reflection', bot.daily_reflection)],
        states={
            WAITING_DAILY_FACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.daily_fact)],
            WAITING_DAILY_THINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.daily_think)],
            WAITING_DAILY_TODO: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.daily_todo)],
        },
        fallbacks=[CommandHandler('cancel', bot.cancel)]
    )
    
    # 핸들러 등록
    application.add_handler(CommandHandler("start", bot.start))
    application.add_handler(CommandHandler("help", bot.help_command))
    application.add_handler(schedule_handler)
    application.add_handler(reflection_handler)
    application.add_handler(CommandHandler("view_schedule", bot.view_schedule))
    
    # 봇 시작
    print("🤖 텔레그램 봇이 시작되었습니다...")
    if bot.ai_helper.is_available():
        print("✅ AI 기능이 활성화되었습니다.")
    else:
        print("⚠️  AI 기능이 비활성화되었습니다. OpenAI API 키를 설정해주세요.")
    
    # Render 환경에서는 webhook 사용, 로컬에서는 polling 사용
    if os.getenv('RENDER'):
        # Render 환경에서 webhook 사용
        port = int(os.environ.get('PORT', 8080))
        application.run_webhook(
            listen="0.0.0.0",
            port=port,
            url_path=BOT_TOKEN,
            webhook_url=f"https://telegram-bot.onrender.com/{BOT_TOKEN}"
        )
    else:
        # 로컬 환경에서 polling 사용
        application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main() 