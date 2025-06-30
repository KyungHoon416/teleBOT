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

# 대화 상태
WAITING_SCHEDULE_TITLE, WAITING_SCHEDULE_DESC, WAITING_SCHEDULE_DATE, WAITING_SCHEDULE_TIME = range(4)
WAITING_DAILY_FACT, WAITING_DAILY_THINK, WAITING_DAILY_TODO = range(4, 7)
WAITING_WEEKLY_FACT, WAITING_WEEKLY_THINK, WAITING_WEEKLY_TODO, WAITING_WEEKLY_TODO_FINAL = range(7, 10, 10, 11)
WAITING_MONTHLY_FACT, WAITING_MONTHLY_THINK, WAITING_MONTHLY_TODO, WAITING_MONTHLY_TODO_FINAL = range(10, 13, 13, 14)
WAITING_FEEDBACK = range(14, 15)
WAITING_EDIT_TITLE, WAITING_EDIT_DESC, WAITING_EDIT_DATE, WAITING_EDIT_TIME = range(15, 19)
WAITING_AI_REFLECTION = range(19, 20)
WAITING_CHATGPT = range(20, 21)
WAITING_ROUTINE_TITLE, WAITING_ROUTINE_DESC, WAITING_ROUTINE_FREQ, WAITING_ROUTINE_DAYS, WAITING_ROUTINE_DATE, WAITING_ROUTINE_TIME = range(21, 27)
WAITING_VOICE_REFLECTION, WAITING_IMAGE_REFLECTION = range(27, 29)

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
        """도움말 명령어"""
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
    
    # ... (기존 함수들은 그대로 유지)
    
    # 음성/이미지 회고 지원 함수들
    async def voice_reflection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """음성 회고 시작"""
        user_id = update.effective_user.id
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        existing_reflections = self.db.get_reflections(user_id, 'voice', today)
        if existing_reflections:
            await update.message.reply_text("🎤 오늘 이미 음성 회고를 작성하셨습니다. 수정하시겠습니까?")
            return ConversationHandler.END
        
        context.user_data['voice_reflection'] = {}
        await update.message.reply_text("🎤 **음성 회고**\n\n음성 메시지를 보내주세요. AI가 음성을 텍스트로 변환하고 회고 내용을 분석해드립니다.")
        return WAITING_VOICE_REFLECTION
    
    async def handle_voice_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """음성 메시지 처리"""
        user_id = update.effective_user.id
        
        if not update.message.voice:
            await update.message.reply_text("❌ 음성 메시지가 아닙니다. 음성 메시지를 보내주세요.")
            return WAITING_VOICE_REFLECTION
        
        await update.message.reply_text("🎤 음성을 분석하고 있습니다...")
        
        try:
            # 음성 파일 다운로드
            voice_file = await context.bot.get_file(update.message.voice.file_id)
            voice_path = f"voice_{user_id}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.ogg"
            
            # 음성을 텍스트로 변환 (OpenAI Whisper 사용)
            if self.ai_helper.is_available():
                transcription = self.ai_helper.transcribe_voice(voice_file.file_path)
                if transcription:
                    # AI 분석 및 회고 생성
                    ai_analysis = self.ai_helper.analyze_voice_reflection(transcription)
                    
                    # 회고 저장
                    today = datetime.datetime.now().strftime('%Y-%m-%d')
                    content = f"[음성 변환] {transcription}\n\n[AI 분석] {ai_analysis}"
                    success = self.db.add_reflection(user_id, 'voice', content, today)
                    
                    if success:
                        message = f"✅ **음성 회고가 저장되었습니다!**\n\n🎤 **음성 내용**\n{transcription}\n\n🤖 **AI 분석**\n{ai_analysis}"
                        await update.message.reply_text(message)
                    else:
                        await update.message.reply_text("❌ 회고 저장 중 오류가 발생했습니다.")
                else:
                    await update.message.reply_text("❌ 음성 인식에 실패했습니다. 다시 시도해주세요.")
            else:
                await update.message.reply_text("❌ AI 기능을 사용할 수 없습니다. OpenAI API 키를 설정해주세요.")
            
            context.user_data['voice_reflection'] = {}
            return ConversationHandler.END
            
        except Exception as e:
            print(f"음성 처리 오류: {e}")
            await update.message.reply_text("❌ 음성 처리 중 오류가 발생했습니다. 다시 시도해주세요.")
            return WAITING_VOICE_REFLECTION
    
    async def image_reflection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """이미지 회고 시작"""
        user_id = update.effective_user.id
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        existing_reflections = self.db.get_reflections(user_id, 'image', today)
        if existing_reflections:
            await update.message.reply_text("🖼️ 오늘 이미 이미지 회고를 작성하셨습니다. 수정하시겠습니까?")
            return ConversationHandler.END
        
        context.user_data['image_reflection'] = {}
        await update.message.reply_text("🖼️ **이미지 회고**\n\n이미지를 보내주세요. AI가 이미지를 분석하고 회고 내용을 생성해드립니다.")
        return WAITING_IMAGE_REFLECTION
    
    async def handle_image_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """이미지 메시지 처리"""
        user_id = update.effective_user.id
        
        if not update.message.photo:
            await update.message.reply_text("❌ 이미지가 아닙니다. 이미지를 보내주세요.")
            return WAITING_IMAGE_REFLECTION
        
        await update.message.reply_text("🖼️ 이미지를 분석하고 있습니다...")
        
        try:
            # 이미지 파일 다운로드
            photo = update.message.photo[-1]  # 가장 큰 해상도 선택
            image_file = await context.bot.get_file(photo.file_id)
            
            # 이미지 분석 (OpenAI Vision 사용)
            if self.ai_helper.is_available():
                analysis = self.ai_helper.analyze_image_reflection(image_file.file_path)
                if analysis:
                    # 회고 저장
                    today = datetime.datetime.now().strftime('%Y-%m-%d')
                    content = f"[이미지 분석] {analysis}"
                    success = self.db.add_reflection(user_id, 'image', content, today)
                    
                    if success:
                        message = f"✅ **이미지 회고가 저장되었습니다!**\n\n🖼️ **AI 분석**\n{analysis}"
                        await update.message.reply_text(message)
                    else:
                        await update.message.reply_text("❌ 회고 저장 중 오류가 발생했습니다.")
                else:
                    await update.message.reply_text("❌ 이미지 분석에 실패했습니다. 다시 시도해주세요.")
            else:
                await update.message.reply_text("❌ AI 기능을 사용할 수 없습니다. OpenAI API 키를 설정해주세요.")
            
            context.user_data['image_reflection'] = {}
            return ConversationHandler.END
            
        except Exception as e:
            print(f"이미지 처리 오류: {e}")
            await update.message.reply_text("❌ 이미지 처리 중 오류가 발생했습니다. 다시 시도해주세요.")
            return WAITING_IMAGE_REFLECTION

    async def motivate(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        랜덤 명언/동기부여 메시지 전송
        """
        quote = random.choice(MOTIVATIONAL_QUOTES)
        await update.message.reply_text(f"💡 {quote}")
        if self.ai_helper.is_available():
            ai_msg = await self.ai_helper.get_motivational_message()
            await update.message.reply_text(f"🤖 AI 동기부여: {ai_msg}")

    async def ai_reflection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        AI와 함께 묵상/고민/자기성찰 대화 (GPT-4o-mini)
        """
        await update.message.reply_text(
            "🧘 <b>AI와 함께 묵상을 시작합니다!</b>\n\n자유롭게 오늘의 감정, 고민, 생각, 목표 등을 적어주세요.\nAI가 따뜻하게 코칭해드립니다.",
            parse_mode='HTML'
        )
        return WAITING_AI_REFLECTION

    async def ai_reflection_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_input = update.message.text
        if self.ai_helper.is_available():
            response = await self.ai_helper.get_ai_reflection_guidance(user_input)
        else:
            response = "AI 묵상 기능이 비활성화되어 있습니다."
        await update.message.reply_text(response, parse_mode='HTML')
        return ConversationHandler.END

    async def chatgpt(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        ChatGPT와 자유 대화 (질문/상담/잡담 등)
        """
        await update.message.reply_text(
            "💬 <b>ChatGPT와 대화를 시작합니다!</b>\n\n궁금한 점, 고민, 잡담 등 무엇이든 입력해보세요.",
            parse_mode='HTML'
        )
        return WAITING_CHATGPT

    async def chatgpt_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_message = update.message.text
        user_id = update.effective_user.id
        # 대화 히스토리 관리 (옵션)
        if user_id not in self.ai_conversations:
            self.ai_conversations[user_id] = []
        self.ai_conversations[user_id].append({"role": "user", "content": user_message})
        if self.ai_helper.is_available():
            response = await self.ai_helper.chat_with_gpt(user_message, self.ai_conversations[user_id])
        else:
            response = "AI 대화 기능이 비활성화되어 있습니다."
        self.ai_conversations[user_id].append({"role": "assistant", "content": response})
        await update.message.reply_text(response, parse_mode='HTML')
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
    application.add_handler(CommandHandler("voice_reflection", bot.voice_reflection))
    application.add_handler(CommandHandler("image_reflection", bot.image_reflection))
    application.add_handler(CommandHandler("motivate", bot.motivate))
    
    # 음성 회고 핸들러
    voice_reflection_handler = ConversationHandler(
        entry_points=[CommandHandler('voice_reflection', bot.voice_reflection)],
        states={
            WAITING_VOICE_REFLECTION: [MessageHandler(filters.VOICE, bot.handle_voice_message)],
        },
        fallbacks=[CommandHandler('cancel', bot.cancel)]
    )
    
    # 이미지 회고 핸들러
    image_reflection_handler = ConversationHandler(
        entry_points=[CommandHandler('image_reflection', bot.image_reflection)],
        states={
            WAITING_IMAGE_REFLECTION: [MessageHandler(filters.PHOTO, bot.handle_image_message)],
        },
        fallbacks=[CommandHandler('cancel', bot.cancel)]
    )
    
    application.add_handler(voice_reflection_handler)
    application.add_handler(image_reflection_handler)
    
    # 봇 시작
    print("🤖 텔레그램 봇이 시작되었습니다...")
    if bot.ai_helper.is_available():
        print("✅ AI 기능이 활성화되었습니다.")
    else:
        print("⚠️  AI 기능이 비활성화되었습니다. OpenAI API 키를 설정해주세요.")
    
    application.run_polling()

if __name__ == '__main__':
    main() 