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
WAITING_EDIT_SELECT, WAITING_EDIT_FIELD, WAITING_EDIT_VALUE = range(30, 33)
WAITING_DELETE_SELECT, WAITING_DELETE_CONFIRM = range(33, 35)
WAITING_COMPLETE_SELECT = 35

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
        try:
            if not update.message:
                return ConversationHandler.END
            await update.message.reply_text("📝 일정의 제목을 입력해주세요:")
            return WAITING_SCHEDULE_TITLE
        except Exception as e:
            await update.message.reply_text(f"[오류] 일정 추가 중 에러 발생: {e}")
            print(f"add_schedule error: {e}")
            return ConversationHandler.END
    
    async def schedule_title(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            if not update.effective_user or not update.message:
                return ConversationHandler.END
            user_id = update.effective_user.id
            title = update.message.text
            self.user_states[user_id] = {'title': title}
            await update.message.reply_text("📄 일정에 대한 설명을 입력해주세요 (선택사항):")
            return WAITING_SCHEDULE_DESC
        except Exception as e:
            await update.message.reply_text(f"[오류] 일정 제목 처리 중 에러 발생: {e}")
            print(f"schedule_title error: {e}")
            return ConversationHandler.END
    
    async def schedule_description(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            if not update.effective_user or not update.message:
                return ConversationHandler.END
            user_id = update.effective_user.id
            description = update.message.text
            self.user_states[user_id]['description'] = description
            await update.message.reply_text("📅 일정 날짜를 입력해주세요 (YYYY-MM-DD 형식):")
            return WAITING_SCHEDULE_DATE
        except Exception as e:
            await update.message.reply_text(f"[오류] 일정 설명 처리 중 에러 발생: {e}")
            print(f"schedule_description error: {e}")
            return ConversationHandler.END
    
    async def schedule_date(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            if not update.effective_user or not update.message:
                return ConversationHandler.END
            user_id = update.effective_user.id
            date_text = update.message.text
            try:
                datetime.datetime.strptime(date_text, '%Y-%m-%d')
                self.user_states[user_id]['date'] = date_text
                await update.message.reply_text("⏰ 일정 시간을 입력해주세요 (HH:MM 형식, 선택사항):")
                return WAITING_SCHEDULE_TIME
            except ValueError:
                await update.message.reply_text("❌ 잘못된 날짜 형식입니다. YYYY-MM-DD 형식으로 입력해주세요.")
                return WAITING_SCHEDULE_DATE
        except Exception as e:
            await update.message.reply_text(f"[오류] 일정 날짜 처리 중 에러 발생: {e}")
            print(f"schedule_date error: {e}")
            return ConversationHandler.END
    
    async def schedule_time(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            if not update.effective_user or not update.message:
                return ConversationHandler.END
            user_id = update.effective_user.id
            time_text = update.message.text
            try:
                if time_text.strip():
                    datetime.datetime.strptime(time_text, '%H:%M')
                    time = time_text
                else:
                    time = None
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
                if user_id in self.user_states:
                    del self.user_states[user_id]
                return ConversationHandler.END
            except ValueError:
                await update.message.reply_text("❌ 잘못된 시간 형식입니다. HH:MM 형식으로 입력해주세요.")
                return WAITING_SCHEDULE_TIME
        except Exception as e:
            await update.message.reply_text(f"[오류] 일정 시간 처리 중 에러 발생: {e}")
            print(f"schedule_time error: {e}")
            return ConversationHandler.END
    
    async def view_schedule(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
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
        except Exception as e:
            await update.message.reply_text(f"[오류] 일정 조회 중 에러 발생: {e}")
            print(f"view_schedule error: {e}")
    
    async def daily_reflection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
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
        except Exception as e:
            await update.message.reply_text(f"[오류] 일일 회고 시작 중 에러 발생: {e}")
            print(f"daily_reflection error: {e}")
            return ConversationHandler.END

    async def daily_fact(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            if not update.message:
                return ConversationHandler.END
            context.user_data['reflection']['fact'] = update.message.text
            await update.message.reply_text("2️⃣ 그 일에 대해 어떻게 생각하셨나요?")
            return WAITING_DAILY_THINK
        except Exception as e:
            await update.message.reply_text(f"[오류] 일일 회고(사실) 처리 중 에러 발생: {e}")
            print(f"daily_fact error: {e}")
            return ConversationHandler.END

    async def daily_think(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            if not update.message:
                return ConversationHandler.END
            context.user_data['reflection']['think'] = update.message.text
            await update.message.reply_text("3️⃣ 내일은 무엇을 실천하고 싶으신가요?")
            return WAITING_DAILY_TODO
        except Exception as e:
            await update.message.reply_text(f"[오류] 일일 회고(생각) 처리 중 에러 발생: {e}")
            print(f"daily_think error: {e}")
            return ConversationHandler.END

    async def daily_todo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
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
        except Exception as e:
            await update.message.reply_text(f"[오류] 일일 회고(실천) 처리 중 에러 발생: {e}")
            print(f"daily_todo error: {e}")
            return ConversationHandler.END
    
    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            user_id = update.effective_user.id
            if user_id in self.user_states:
                del self.user_states[user_id]
            if user_id in self.ai_conversations:
                del self.ai_conversations[user_id]
            await update.message.reply_text("❌ 작업이 취소되었습니다.")
            return ConversationHandler.END
        except Exception as e:
            await update.message.reply_text(f"[오류] 취소 처리 중 에러 발생: {e}")
            print(f"cancel error: {e}")
            return ConversationHandler.END

    # 일정 수정 대화 흐름
    async def edit_schedule(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        schedules = self.db.get_schedules(user_id, today)
        if not schedules:
            await update.message.reply_text("오늘 수정할 일정이 없습니다.")
            return ConversationHandler.END
        msg = "수정할 일정을 선택하세요:\n"
        for idx, s in enumerate(schedules, 1):
            msg += f"{idx}. {s['title']} ({s['date']} {s['time'] or ''})\n"
        context.user_data['edit_schedules'] = schedules
        await update.message.reply_text(msg)
        return WAITING_EDIT_SELECT

    async def edit_select(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            idx = int(update.message.text.strip()) - 1
            schedules = context.user_data['edit_schedules']
            if idx < 0 or idx >= len(schedules):
                await update.message.reply_text("잘못된 번호입니다. 다시 입력하세요.")
                return WAITING_EDIT_SELECT
            context.user_data['edit_selected'] = schedules[idx]
            await update.message.reply_text("수정할 항목을 선택하세요 (title/description/date/time):")
            return WAITING_EDIT_FIELD
        except Exception:
            await update.message.reply_text("숫자로 입력해주세요.")
            return WAITING_EDIT_SELECT

    async def edit_field(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        field = update.message.text.strip().lower()
        if field not in ['title', 'description', 'date', 'time']:
            await update.message.reply_text("title/description/date/time 중 하나를 입력하세요.")
            return WAITING_EDIT_FIELD
        context.user_data['edit_field'] = field
        await update.message.reply_text(f"새로운 {field} 값을 입력하세요:")
        return WAITING_EDIT_VALUE

    async def edit_value(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        value = update.message.text.strip()
        selected = context.user_data['edit_selected']
        field = context.user_data['edit_field']
        new_title = selected['title']
        new_desc = selected['description']
        new_date = selected['date']
        new_time = selected['time']
        if field == 'title':
            new_title = value
        elif field == 'description':
            new_desc = value
        elif field == 'date':
            new_date = value
        elif field == 'time':
            new_time = value
        success = self.db.update_schedule(selected['id'], selected['user_id'], new_title, new_desc, new_date, new_time)
        if success:
            await update.message.reply_text("✅ 일정이 성공적으로 수정되었습니다!")
            await update.message.reply_text(f"🔔 '{new_title}' 일정이 수정되었습니다.")
        else:
            await update.message.reply_text("❌ 일정 수정 중 오류가 발생했습니다.")
        context.user_data.pop('edit_schedules', None)
        context.user_data.pop('edit_selected', None)
        context.user_data.pop('edit_field', None)
        return ConversationHandler.END

    # 일정 삭제 대화 흐름
    async def delete_schedule(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        schedules = self.db.get_schedules(user_id, today)
        if not schedules:
            await update.message.reply_text("오늘 삭제할 일정이 없습니다.")
            return ConversationHandler.END
        msg = "삭제할 일정을 선택하세요:\n"
        for idx, s in enumerate(schedules, 1):
            msg += f"{idx}. {s['title']} ({s['date']} {s['time'] or ''})\n"
        context.user_data['delete_schedules'] = schedules
        await update.message.reply_text(msg)
        return WAITING_DELETE_SELECT

    async def delete_select(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            idx = int(update.message.text.strip()) - 1
            schedules = context.user_data['delete_schedules']
            if idx < 0 or idx >= len(schedules):
                await update.message.reply_text("잘못된 번호입니다. 다시 입력하세요.")
                return WAITING_DELETE_SELECT
            context.user_data['delete_selected'] = schedules[idx]
            await update.message.reply_text(f"정말로 삭제하시겠습니까? (yes/no)\n{schedules[idx]['title']} ({schedules[idx]['date']} {schedules[idx]['time'] or ''})")
            return WAITING_DELETE_CONFIRM
        except Exception:
            await update.message.reply_text("숫자로 입력해주세요.")
            return WAITING_DELETE_SELECT

    async def delete_confirm(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        answer = update.message.text.strip().lower()
        selected = context.user_data['delete_selected']
        if answer == 'yes':
            success = self.db.delete_schedule(selected['id'], selected['user_id'])
            if success:
                await update.message.reply_text("✅ 일정이 성공적으로 삭제되었습니다!")
                await update.message.reply_text(f"🔔 '{selected['title']}' 일정이 삭제되었습니다.")
            else:
                await update.message.reply_text("❌ 일정 삭제 중 오류가 발생했습니다.")
        else:
            await update.message.reply_text("삭제가 취소되었습니다.")
        context.user_data.pop('delete_schedules', None)
        context.user_data.pop('delete_selected', None)
        return ConversationHandler.END

    # 일정 완료 대화 흐름
    async def complete_schedule(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        schedules = self.db.get_schedules(user_id, today)
        incomplete = [s for s in schedules if not s.get('is_done')]
        if not incomplete:
            await update.message.reply_text("오늘 완료할 일정이 없습니다.")
            return ConversationHandler.END
        msg = "완료할 일정을 선택하세요:\n"
        for idx, s in enumerate(incomplete, 1):
            msg += f"{idx}. {s['title']} ({s['date']} {s['time'] or ''})\n"
        context.user_data['complete_schedules'] = incomplete
        await update.message.reply_text(msg)
        return WAITING_COMPLETE_SELECT

    async def complete_select(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            idx = int(update.message.text.strip()) - 1
            schedules = context.user_data['complete_schedules']
            if idx < 0 or idx >= len(schedules):
                await update.message.reply_text("잘못된 번호입니다. 다시 입력하세요.")
                return WAITING_COMPLETE_SELECT
            selected = schedules[idx]
            success = self.db.update_schedule_done(selected['id'], selected['user_id'])
            if success:
                # AI 응원 메시지
                if self.ai_helper.is_available():
                    msg = await self.ai_helper.get_completion_motivation(selected['title'])
                else:
                    msg = f"🎉 '{selected['title']}' 일정 완료! 정말 수고하셨어요! 💪"
                await update.message.reply_text(msg)
                # 알림 메시지
                await update.message.reply_text(f"🔔 '{selected['title']}' 일정이 완료 처리되었습니다.")
            else:
                await update.message.reply_text("❌ 일정 완료 처리 중 오류가 발생했습니다.")
            context.user_data.pop('complete_schedules', None)
            return ConversationHandler.END
        except Exception:
            await update.message.reply_text("숫자로 입력해주세요.")
            return WAITING_COMPLETE_SELECT

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
    
    # 일정 수정 대화 핸들러
    edit_handler = ConversationHandler(
        entry_points=[CommandHandler('edit_schedule', bot.edit_schedule)],
        states={
            WAITING_EDIT_SELECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.edit_select)],
            WAITING_EDIT_FIELD: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.edit_field)],
            WAITING_EDIT_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.edit_value)],
        },
        fallbacks=[CommandHandler('cancel', bot.cancel)]
    )
    # 일정 삭제 대화 핸들러
    delete_handler = ConversationHandler(
        entry_points=[CommandHandler('delete_schedule', bot.delete_schedule)],
        states={
            WAITING_DELETE_SELECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.delete_select)],
            WAITING_DELETE_CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.delete_confirm)],
        },
        fallbacks=[CommandHandler('cancel', bot.cancel)]
    )
    
    # 일정 완료 대화 핸들러
    complete_handler = ConversationHandler(
        entry_points=[CommandHandler('complete_schedule', bot.complete_schedule)],
        states={
            WAITING_COMPLETE_SELECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.complete_select)],
        },
        fallbacks=[CommandHandler('cancel', bot.cancel)]
    )
    
    # 핸들러 등록
    application.add_handler(CommandHandler("start", bot.start))
    application.add_handler(CommandHandler("help", bot.help_command))
    application.add_handler(schedule_handler)
    application.add_handler(reflection_handler)
    application.add_handler(CommandHandler("view_schedule", bot.view_schedule))
    # 일정 수정/삭제 명령어 핸들러 등록
    application.add_handler(edit_handler)
    application.add_handler(delete_handler)
    application.add_handler(complete_handler)
    
    # 봇 시작
    print("🤖 텔레그램 봇이 시작되었습니다...")
    if bot.ai_helper.is_available():
        print("✅ AI 기능이 활성화되었습니다.")
    else:
        print("⚠️  AI 기능이 비활성화되었습니다. OpenAI API 키를 설정해주세요.")
    
    # Render 환경에서는 webhook 사용, 로컬에서는 polling 사용
    if os.getenv('RENDER'):
        port = int(os.environ.get('PORT', 8080))
        webhook_url = "https://telebot-svrq.onrender.com/" + BOT_TOKEN
        print(f"🌐 Webhook 모드로 시작합니다. Port: {port}, Webhook URL: {webhook_url}")
        application.run_webhook(
            listen="0.0.0.0",
            port=port,
            url_path=BOT_TOKEN,
            webhook_url=webhook_url
        )
    else:
        # 로컬 환경에서 polling 사용
        print("🔄 Polling 모드로 시작합니다...")
        try:
            application.run_polling(drop_pending_updates=True)
        except Exception as e:
            print(f"❌ 봇 실행 중 오류 발생: {e}")
            print("🔄 기본 설정으로 재시작합니다...")
            application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main() 