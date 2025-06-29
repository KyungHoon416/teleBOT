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

# 로깅 설정
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

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
• 📖 당일/주간/월간 회고 작성
• 💡 회고에 대한 피드백 제공
• 🤖 AI와 함께하는 묵상 (GPT-4o-mini)
• 💬 ChatGPT와 자유로운 대화
• 🔔 아침 8시 자동 알림
• 📢 일정 변경 시 실시간 알림

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
        await update.message.reply_text("📝 일정의 제목을 입력해주세요:")
        return WAITING_SCHEDULE_TITLE
    
    async def schedule_title(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """일정 제목 입력 처리"""
        user_id = update.effective_user.id
        title = update.message.text
        
        self.user_states[user_id] = {'title': title}
        await update.message.reply_text("📄 일정에 대한 설명을 입력해주세요 (선택사항):")
        return WAITING_SCHEDULE_DESC
    
    async def schedule_description(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """일정 설명 입력 처리"""
        user_id = update.effective_user.id
        description = update.message.text
        
        self.user_states[user_id]['description'] = description
        await update.message.reply_text("📅 일정 날짜를 입력해주세요 (YYYY-MM-DD 형식):")
        return WAITING_SCHEDULE_DATE
    
    async def schedule_date(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """일정 날짜 입력 처리"""
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
        """일정 시간 입력 처리 및 알림 예약/종료 알림 추가"""
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
                # 아침 8시 알림 자동 설정 (기존)
                schedule_id = self.db.get_last_schedule_id(user_id)
                if schedule_id:
                    notification_message = f"🌅 좋은 아침입니다!\n\n📅 오늘의 일정: {state['title']}"
                    if state['description']:
                        notification_message += f"\n📄 {state['description']}"
                    self.db.add_notification(
                        user_id=user_id,
                        schedule_id=schedule_id,
                        notification_type='morning',
                        notification_time='08:00',
                        message=notification_message
                    )
                # 일정 종료 알림 자동 등록
                if time:
                    # 종료 알림 시간(예: 일정 시간 + 1분, 실제 종료시간 컬럼이 있다면 그 시간)
                    end_time = time  # 여기서는 입력한 시간에 바로 알림
                    end_msg = "오늘 하루 고생 많으셨습니다! 👏\n일정을 잘 마무리하셨네요. 스스로를 칭찬해 주세요!"
                    self.db.add_notification(
                        user_id=user_id,
                        schedule_id=schedule_id,
                        notification_type='end',
                        notification_time=end_time,
                        message=end_msg
                    )
                # 일정 추가 알림 전송
                await self.send_schedule_change_notification(
                    context, user_id, 
                    f"✅ 새 일정이 추가되었습니다!\n\n📅 {state['title']}\n📆 {state['date']}"
                    + (f"\n⏰ {time}" if time else "")
                )
                await update.message.reply_text("✅ 일정이 성공적으로 추가되었습니다!\n\n🔔 아침 8시에 알림이 설정되었습니다.")
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
        """일정 조회 (완료 버튼 포함)"""
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
            # 인라인 버튼: 완료/완료됨
            if schedule.get('is_done', 0):
                keyboard = [[InlineKeyboardButton("✅ 완료됨", callback_data="done_disabled", disabled=True)]]
            else:
                keyboard = [[InlineKeyboardButton("✅ 완료", callback_data=f"done_{schedule['id']}")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(msg, reply_markup=reply_markup)
    
    async def edit_schedule(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """일정 수정 시작"""
        user_id = update.effective_user.id
        
        # 사용자의 일정 목록 가져오기
        schedules = self.db.get_schedules(user_id)
        
        if not schedules:
            await update.message.reply_text("📅 수정할 일정이 없습니다.")
            return ConversationHandler.END
        
        # 일정 선택을 위한 키보드 생성
        keyboard = []
        for schedule in schedules[:10]:  # 최근 10개만 표시
            time_str = f" {schedule['time']}" if schedule['time'] else ""
            keyboard.append([InlineKeyboardButton(
                f"{schedule['date']}{time_str} - {schedule['title']}", 
                callback_data=f"edit_{schedule['id']}"
            )])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("📝 수정할 일정을 선택해주세요:", reply_markup=reply_markup)
        return WAITING_EDIT_TITLE
    
    async def edit_schedule_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """일정 수정 콜백 처리"""
        query = update.callback_query
        await query.answer()
        
        schedule_id = int(query.data.split('_')[1])
        user_id = query.from_user.id
        
        # 선택된 일정 정보 저장
        self.user_states[user_id] = {'edit_id': schedule_id}
        
        await query.edit_message_text("📝 새로운 제목을 입력해주세요:")
        return WAITING_EDIT_TITLE
    
    async def edit_title(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """수정할 제목 입력 처리"""
        user_id = update.effective_user.id
        title = update.message.text
        
        self.user_states[user_id]['title'] = title
        await update.message.reply_text("📄 새로운 설명을 입력해주세요:")
        return WAITING_EDIT_DESC
    
    async def edit_description(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """수정할 설명 입력 처리"""
        user_id = update.effective_user.id
        description = update.message.text
        
        self.user_states[user_id]['description'] = description
        await update.message.reply_text("📅 새로운 날짜를 입력해주세요 (YYYY-MM-DD 형식):")
        return WAITING_EDIT_DATE
    
    async def edit_date(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """수정할 날짜 입력 처리"""
        user_id = update.effective_user.id
        date_text = update.message.text
        
        try:
            datetime.datetime.strptime(date_text, '%Y-%m-%d')
            self.user_states[user_id]['date'] = date_text
            await update.message.reply_text("⏰ 새로운 시간을 입력해주세요 (HH:MM 형식, 선택사항):")
            return WAITING_EDIT_TIME
        except ValueError:
            await update.message.reply_text("❌ 잘못된 날짜 형식입니다. YYYY-MM-DD 형식으로 입력해주세요.")
            return WAITING_EDIT_DATE
    
    async def edit_time(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """수정할 시간 입력 처리"""
        user_id = update.effective_user.id
        time_text = update.message.text
        
        try:
            if time_text.strip():
                datetime.datetime.strptime(time_text, '%H:%M')
                time = time_text
            else:
                time = None
            
            # 일정 수정
            state = self.user_states[user_id]
            success = self.db.update_schedule(
                schedule_id=state['edit_id'],
                user_id=user_id,
                title=state['title'],
                description=state['description'],
                date=state['date'],
                time=time
            )
            
            if success:
                # 일정 수정 알림 전송
                await self.send_schedule_change_notification(
                    context, user_id, 
                    f"✏️ 일정이 수정되었습니다!\n\n📅 {state['title']}\n📆 {state['date']}"
                    + (f"\n⏰ {time}" if time else "")
                )
                
                await update.message.reply_text("✅ 일정이 성공적으로 수정되었습니다!")
            else:
                await update.message.reply_text("❌ 일정 수정 중 오류가 발생했습니다.")
            
            # 상태 초기화
            if user_id in self.user_states:
                del self.user_states[user_id]
            
            return ConversationHandler.END
            
        except ValueError:
            await update.message.reply_text("❌ 잘못된 시간 형식입니다. HH:MM 형식으로 입력해주세요.")
            return WAITING_EDIT_TIME
    
    async def delete_schedule(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """일정 삭제"""
        user_id = update.effective_user.id
        
        # 사용자의 일정 목록 가져오기
        schedules = self.db.get_schedules(user_id)
        
        if not schedules:
            await update.message.reply_text("📅 삭제할 일정이 없습니다.")
            return ConversationHandler.END
        
        # 일정 선택을 위한 키보드 생성
        keyboard = []
        for schedule in schedules[:10]:  # 최근 10개만 표시
            time_str = f" {schedule['time']}" if schedule['time'] else ""
            keyboard.append([InlineKeyboardButton(
                f"{schedule['date']}{time_str} - {schedule['title']}", 
                callback_data=f"delete_{schedule['id']}"
            )])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("🗑️ 삭제할 일정을 선택해주세요:", reply_markup=reply_markup)
        return ConversationHandler.END
    
    async def delete_schedule_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """일정 삭제 콜백 처리"""
        query = update.callback_query
        await query.answer()
        
        schedule_id = int(query.data.split('_')[1])
        user_id = query.from_user.id
        
        # 삭제 전 일정 정보 가져오기
        schedules = self.db.get_schedules(user_id)
        schedule_to_delete = None
        for schedule in schedules:
            if schedule['id'] == schedule_id:
                schedule_to_delete = schedule
                break
        
        # 일정 삭제
        success = self.db.delete_schedule(schedule_id, user_id)
        
        if success:
            # 일정 삭제 알림 전송
            if schedule_to_delete:
                await self.send_schedule_change_notification(
                    context, user_id, 
                    f"🗑️ 일정이 삭제되었습니다!\n\n📅 {schedule_to_delete['title']}\n📆 {schedule_to_delete['date']}"
                    + (f"\n⏰ {schedule_to_delete['time']}" if schedule_to_delete['time'] else "")
                )
            
            await query.edit_message_text("✅ 일정이 성공적으로 삭제되었습니다!")
        else:
            await query.edit_message_text("❌ 일정 삭제 중 오류가 발생했습니다.")
    
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

    async def weekly_reflection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.effective_user or not update.message:
            return ConversationHandler.END
        user_id = update.effective_user.id
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        existing_reflections = self.db.get_reflections(user_id, 'weekly', today)
        if existing_reflections:
            await update.message.reply_text("📖 이번 주 이미 회고를 작성하셨습니다. 수정하시겠습니까?")
            return ConversationHandler.END
        context.user_data['reflection'] = {}
        await update.message.reply_text("📝 이번 주를 한 줄로 요약하거나, 키워드(회고라인)를 적어주세요!")
        return WAITING_WEEKLY_FACT

    async def weekly_fact(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message:
            return ConversationHandler.END
        context.user_data['reflection']['line'] = update.message.text
        await update.message.reply_text("1️⃣ 이번 주 있었던 일(사실)을 적어주세요!")
        return WAITING_WEEKLY_THINK

    async def weekly_think(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message:
            return ConversationHandler.END
        context.user_data['reflection']['fact'] = update.message.text
        await update.message.reply_text("2️⃣ 그 일에 대해 어떻게 생각하셨나요?")
        return WAITING_WEEKLY_TODO

    async def weekly_todo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message:
            return ConversationHandler.END
        context.user_data['reflection']['think'] = update.message.text
        await update.message.reply_text("3️⃣ 다음 주에는 무엇을 실천하고 싶으신가요?")
        return WAITING_WEEKLY_TODO_FINAL

    async def weekly_todo_final(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.effective_user or not update.message:
            return ConversationHandler.END
        user_id = update.effective_user.id
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        context.user_data['reflection']['todo'] = update.message.text
        r = context.user_data['reflection']
        content = f"[회고라인] {r['line']}\n[사실] {r['fact']}\n[생각] {r['think']}\n[실천] {r['todo']}"
        success = self.db.add_reflection(user_id, 'weekly', content, today)
        if success:
            await update.message.reply_text("✅ 이번 주의 T형 회고가 저장되었습니다!")
        else:
            await update.message.reply_text("❌ 회고 저장 중 오류가 발생했습니다.")
        context.user_data['reflection'] = {}
        return ConversationHandler.END

    async def monthly_reflection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.effective_user or not update.message:
            return ConversationHandler.END
        user_id = update.effective_user.id
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        existing_reflections = self.db.get_reflections(user_id, 'monthly', today)
        if existing_reflections:
            await update.message.reply_text("📖 이번 달 이미 회고를 작성하셨습니다. 수정하시겠습니까?")
            return ConversationHandler.END
        context.user_data['reflection'] = {}
        await update.message.reply_text("📝 이번 달을 한 줄로 요약하거나, 키워드(회고라인)를 적어주세요!")
        return WAITING_MONTHLY_FACT

    async def monthly_fact(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message:
            return ConversationHandler.END
        context.user_data['reflection']['line'] = update.message.text
        await update.message.reply_text("1️⃣ 이번 달 있었던 일(사실)을 적어주세요!")
        return WAITING_MONTHLY_THINK

    async def monthly_think(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message:
            return ConversationHandler.END
        context.user_data['reflection']['fact'] = update.message.text
        await update.message.reply_text("2️⃣ 그 일에 대해 어떻게 생각하셨나요?")
        return WAITING_MONTHLY_TODO

    async def monthly_todo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message:
            return ConversationHandler.END
        context.user_data['reflection']['think'] = update.message.text
        await update.message.reply_text("3️⃣ 다음 달에는 무엇을 실천하고 싶으신가요?")
        return WAITING_MONTHLY_TODO_FINAL

    async def monthly_todo_final(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.effective_user or not update.message:
            return ConversationHandler.END
        user_id = update.effective_user.id
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        context.user_data['reflection']['todo'] = update.message.text
        r = context.user_data['reflection']
        content = f"[회고라인] {r['line']}\n[사실] {r['fact']}\n[생각] {r['think']}\n[실천] {r['todo']}"
        success = self.db.add_reflection(user_id, 'monthly', content, today)
        if success:
            await update.message.reply_text("✅ 이번 달의 T형 회고가 저장되었습니다!")
        else:
            await update.message.reply_text("❌ 회고 저장 중 오류가 발생했습니다.")
        context.user_data['reflection'] = {}
        return ConversationHandler.END
    
    async def view_reflections(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """회고 조회"""
        user_id = update.effective_user.id
        reflections = self.db.get_reflections(user_id)
        
        if not reflections:
            await update.message.reply_text("📖 작성된 회고가 없습니다.")
            return
        
        message = "📖 **작성한 회고 목록**\n\n"
        for reflection in reflections[:10]:  # 최근 10개만 표시
            type_emoji = {"daily": "📅", "weekly": "📆", "monthly": "📊"}
            emoji = type_emoji.get(reflection['type'], "📖")
            message += f"{emoji} {reflection['date']} ({reflection['type']})\n"
            message += f"📄 {reflection['content'][:100]}...\n\n"
        
        await update.message.reply_text(message)
    
    async def ai_reflection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """AI와 함께하는 묵상 시작"""
        user_id = update.effective_user.id
        
        if not self.ai_helper.is_available():
            await update.message.reply_text("❌ AI 기능을 사용할 수 없습니다. OpenAI API 키를 설정해주세요.")
            return ConversationHandler.END
        
        # AI 대화 히스토리 초기화
        self.ai_conversations[user_id] = []
        
        prompt = "🤖 **AI와 함께하는 묵상**\n\n"
        prompt += "자유롭게 이야기해주세요. AI가 당신의 생각과 감정을 경청하고, 깊이 있는 질문을 통해 자기 성찰을 도와드릴게요.\n\n"
        prompt += "예시 주제:\n"
        for i, prompt_text in enumerate(AI_REFLECTION_PROMPTS, 1):
            prompt += f"• {prompt_text}\n"
        prompt += "\n무엇이든 편하게 말씀해주세요! 💭"
        
        await update.message.reply_text(prompt)
        return WAITING_AI_REFLECTION
    
    async def ai_reflection_response(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """AI 묵상 응답 처리"""
        user_id = update.effective_user.id
        user_input = update.message.text
        
        # 사용자 입력을 대화 히스토리에 추가
        self.ai_conversations[user_id].append({"role": "user", "content": user_input})
        
        # AI 응답 생성
        ai_response = self.ai_helper.get_ai_reflection_guidance(
            user_input, 
            self.ai_conversations[user_id]
        )
        
        # AI 응답을 대화 히스토리에 추가
        self.ai_conversations[user_id].append({"role": "assistant", "content": ai_response})
        
        # 응답 전송
        await update.message.reply_text(f"🤖 **AI의 응답**\n\n{ai_response}")
        
        # 계속 대화할지 묻기
        keyboard = [
            [InlineKeyboardButton("계속 대화하기", callback_data="continue_ai")],
            [InlineKeyboardButton("묵상 종료", callback_data="end_ai")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text("계속 대화하시겠습니까?", reply_markup=reply_markup)
        return WAITING_AI_REFLECTION
    
    async def ai_reflection_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """AI 묵상 콜백 처리"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "continue_ai":
            await query.edit_message_text("계속해서 이야기해주세요! 💭")
            return WAITING_AI_REFLECTION
        elif query.data == "end_ai":
            user_id = query.from_user.id
            
            # 대화 히스토리 정리
            if user_id in self.ai_conversations:
                del self.ai_conversations[user_id]
            
            await query.edit_message_text("🤖 오늘의 묵상이 끝났습니다. 감사합니다! 🙏")
            return ConversationHandler.END
    
    async def ai_feedback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """AI 피드백 제공"""
        user_id = update.effective_user.id
        reflections = self.db.get_reflections(user_id)
        
        if not reflections:
            await update.message.reply_text("📖 먼저 회고를 작성해주세요!")
            return
        
        if not self.ai_helper.is_available():
            await update.message.reply_text("❌ AI 기능을 사용할 수 없습니다. OpenAI API 키를 설정해주세요.")
            return
        
        # 최근 회고에 대한 AI 피드백 제공
        latest_reflection = reflections[0]
        
        await update.message.reply_text("🤖 AI가 회고를 분석하고 있습니다...")
        
        ai_feedback = self.ai_helper.get_reflection_feedback(
            latest_reflection['content'],
            latest_reflection['type']
        )
        
        message = f"🤖 **AI 피드백**\n\n"
        message += f"📅 {latest_reflection['date']} ({latest_reflection['type']})\n\n"
        message += f"📄 **회고 내용**\n{latest_reflection['content'][:200]}...\n\n"
        message += f"💭 **AI 피드백**\n{ai_feedback}"
        
        await update.message.reply_text(message)
    
    async def ai_pattern_analysis(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """AI 회고 패턴 분석"""
        user_id = update.effective_user.id
        reflections = self.db.get_reflections(user_id)
        
        if not reflections:
            await update.message.reply_text("📖 분석할 회고가 없습니다.")
            return
        
        if not self.ai_helper.is_available():
            await update.message.reply_text("❌ AI 기능을 사용할 수 없습니다. OpenAI API 키를 설정해주세요.")
            return
        
        await update.message.reply_text("🤖 회고 패턴을 분석하고 있습니다...")
        
        analysis = self.ai_helper.analyze_reflection_patterns(reflections)
        
        message = f"🤖 **회고 패턴 분석**\n\n{analysis}"
        
        await update.message.reply_text(message)
    
    async def feedback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """기본 피드백 제공 (AI 사용 가능시 AI 피드백, 아니면 기본 피드백)"""
        user_id = update.effective_user.id
        reflections = self.db.get_reflections(user_id)
        
        if not reflections:
            await update.message.reply_text("📖 먼저 회고를 작성해주세요!")
            return
        
        # AI 사용 가능시 AI 피드백, 아니면 기본 피드백
        if self.ai_helper.is_available():
            await self.ai_feedback(update, context)
        else:
            # 기존 기본 피드백 로직
            latest_reflection = reflections[0]
            feedback_text = self.generate_feedback(latest_reflection)
            
            message = f"💡 **회고 피드백**\n\n"
            message += f"📅 {latest_reflection['date']} ({latest_reflection['type']})\n\n"
            message += f"📄 **회고 내용**\n{latest_reflection['content'][:200]}...\n\n"
            message += f"💭 **피드백**\n{feedback_text}"
            
            await update.message.reply_text(message)
    
    def generate_feedback(self, reflection: dict) -> str:
        """기본 피드백 생성 (AI 사용 불가시)"""
        content = reflection['content'].lower()
        reflection_type = reflection['type']
        
        feedback = ""
        
        if reflection_type == 'daily':
            if any(word in content for word in ['성취', '완료', '달성']):
                feedback += "🎉 오늘 목표를 달성하셨네요! 정말 대단합니다.\n"
            if any(word in content for word in ['배움', '학습', '새로운']):
                feedback += "📚 새로운 것을 배우는 하루였군요. 지속적인 성장을 응원합니다!\n"
            if any(word in content for word in ['감사', '고마워', '행복']):
                feedback += "🙏 감사한 마음을 가진 당신이 정말 멋집니다.\n"
        
        elif reflection_type == 'weekly':
            if any(word in content for word in ['성취', '완료', '목표']):
                feedback += "🏆 이번 주 목표 달성률이 높으시네요! 체계적인 계획이 돋보입니다.\n"
            if any(word in content for word in ['어려움', '도전', '극복']):
                feedback += "💪 어려움을 극복하는 과정에서 더욱 성장하셨을 것 같습니다.\n"
        
        elif reflection_type == 'monthly':
            if any(word in content for word in ['변화', '성장', '발전']):
                feedback += "🚀 한 달 동안 큰 변화와 성장을 이루셨네요!\n"
            if any(word in content for word in ['목표', '계획', '다음']):
                feedback += "🎯 다음 달 목표가 명확하시군요. 차근차근 달성해보세요!\n"
        
        if not feedback:
            feedback = "📝 정성스럽게 작성해주신 회고가 인상적입니다. 꾸준한 기록이 큰 힘이 될 거예요!"
        
        return feedback
    
    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """대화 취소"""
        user_id = update.effective_user.id
        if user_id in self.user_states:
            del self.user_states[user_id]
        if user_id in self.ai_conversations:
            del self.ai_conversations[user_id]
        
        await update.message.reply_text("❌ 작업이 취소되었습니다.")
        return ConversationHandler.END
    
    async def chatgpt(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """ChatGPT 대화 시작"""
        user_id = update.effective_user.id
        
        if not self.ai_helper.is_available():
            await update.message.reply_text("❌ ChatGPT 기능을 사용할 수 없습니다. OpenAI API 키를 설정해주세요.")
            return ConversationHandler.END
        
        # 대화 히스토리 초기화
        if user_id not in self.ai_conversations:
            self.ai_conversations[user_id] = []
        
        await update.message.reply_text("🤖 ChatGPT와 대화를 시작합니다!\n\n💬 무엇이든 물어보세요. 대화를 종료하려면 /cancel을 입력하세요.")
        return WAITING_CHATGPT
    
    async def chatgpt_response(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """ChatGPT 응답 처리"""
        user_id = update.effective_user.id
        user_message = update.message.text
        
        if not self.ai_conversations.get(user_id):
            self.ai_conversations[user_id] = []
        
        # 사용자 메시지를 대화 히스토리에 추가
        self.ai_conversations[user_id].append({"role": "user", "content": user_message})
        
        # ChatGPT 응답 생성
        response = self.ai_helper.chat_with_gpt(user_message, self.ai_conversations[user_id])
        
        # AI 응답을 대화 히스토리에 추가
        self.ai_conversations[user_id].append({"role": "assistant", "content": response})
        
        # 대화 히스토리가 너무 길어지면 최근 10개만 유지
        if len(self.ai_conversations[user_id]) > 20:
            self.ai_conversations[user_id] = self.ai_conversations[user_id][-20:]
        
        await update.message.reply_text(response)
        return WAITING_CHATGPT
    
    async def send_morning_notifications(self, context: ContextTypes.DEFAULT_TYPE):
        """아침 알림 전송 (오늘 일정 개수에 따라 메시지 다르게)"""
        try:
            # 모든 사용자 ID 조회
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT DISTINCT user_id FROM schedules')
                user_ids = [row[0] for row in cursor.fetchall()]

            today = datetime.datetime.now(pytz.timezone('Asia/Seoul')).strftime('%Y-%m-%d')

            for user_id in user_ids:
                today_schedules = self.db.get_schedules(user_id, today)
                if not today_schedules:
                    msg = "오늘은 일정이 없습니다. 여유로운 하루 보내세요!"
                elif len(today_schedules) == 1:
                    sch = today_schedules[0]
                    msg = f"오늘의 일정: {sch['title']}\n"
                    if sch['description']:
                        msg += f"{sch['description']}\n"
                    msg += "오늘도 힘내세요!"
                else:
                    msg = f"오늘 일정이 {len(today_schedules)}개나 있네요! 바쁘시겠지만 화이팅입니다! 💪\n"
                    for sch in today_schedules:
                        time_str = f"⏰ {sch['time']} " if sch['time'] else ""
                        msg += f"• {time_str}{sch['title']}\n"
                    msg += "\n오늘도 응원하겠습니다!"
                try:
                    await context.bot.send_message(chat_id=user_id, text=msg)
                except Exception as e:
                    print(f"❌ 아침 알림 전송 실패 (사용자 {user_id}): {e}")
        except Exception as e:
            print(f"❌ 아침 알림 전송 중 오류: {e}")
    
    async def send_end_notifications(self, context: ContextTypes.DEFAULT_TYPE):
        """일정 종료 알림 전송"""
        try:
            now = datetime.datetime.now(pytz.timezone('Asia/Seoul')).strftime('%H:%M')
            today = datetime.datetime.now(pytz.timezone('Asia/Seoul')).strftime('%Y-%m-%d')
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT n.user_id, n.message FROM notifications n
                    JOIN schedules s ON n.schedule_id = s.id
                    WHERE n.notification_type = 'end' AND n.is_active = 1
                    AND n.notification_time = ? AND s.date = ?
                ''', (now, today))
                notifications = cursor.fetchall()
                for user_id, message in notifications:
                    try:
                        await context.bot.send_message(chat_id=user_id, text=message)
                    except Exception as e:
                        print(f"❌ 종료 알림 전송 실패 (사용자 {user_id}): {e}")
        except Exception as e:
            print(f"❌ 종료 알림 전송 중 오류: {e}")
    
    async def send_schedule_change_notification(self, context: ContextTypes.DEFAULT_TYPE, user_id: int, message: str):
        """일정 변경 알림 전송"""
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=message
            )
            print(f"📢 일정 변경 알림 전송 완료: 사용자 {user_id}")
        except Exception as e:
            print(f"❌ 일정 변경 알림 전송 실패 (사용자 {user_id}): {e}")

    async def schedule_done_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """일정 완료 버튼 콜백 처리"""
        query = update.callback_query
        await query.answer()
        user_id = query.from_user.id
        data = query.data
        if data == "done_disabled":
            await query.answer("이미 완료된 일정입니다.", show_alert=True)
            return
        if data.startswith("done_"):
            schedule_id = int(data.split("_")[1])
            # DB에서 완료 처리
            success = self.db.update_schedule_done(schedule_id, user_id)
            if success:
                # 일정 정보 가져오기
                schedule = self.db.get_schedule(schedule_id)
                
                # 완료 메시지 생성
                completion_msg = self.get_random_completion_message()
                
                # AI 동기부여 메시지 추가 (AI 사용 가능시)
                ai_motivation = ""
                if self.ai_helper.is_available() and schedule:
                    ai_motivation = self.ai_helper.get_completion_motivation(schedule['title'])
                
                # 메시지 조합
                final_message = f"{query.message.text}\n\n{completion_msg}"
                if ai_motivation:
                    final_message += f"\n\n🤖 **AI의 응원**\n{ai_motivation}"
                
                await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ 완료됨", callback_data="done_disabled", disabled=True)]]))
                await query.edit_message_text(final_message)
            else:
                await query.answer("일정 완료 처리에 실패했습니다.", show_alert=True)

    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """/stats 명령어: 주간/월간 일정/회고 통계"""
        user_id = update.effective_user.id
        week_s = self.db.get_schedule_stats(user_id, 'week')
        month_s = self.db.get_schedule_stats(user_id, 'month')
        week_r = self.db.get_reflection_stats(user_id, 'week')
        month_r = self.db.get_reflection_stats(user_id, 'month')
        msg = (
            f"📊 <b>이번 주 통계</b>\n"
            f"- 완료한 일정: {week_s['done']}개\n"
            f"- 미완료 일정: {week_s['not_done']}개\n"
            f"- 회고 작성률: {week_r['rate']:.0f}% ({week_r['written']}/{week_r['total']})\n\n"
            f"📅 <b>이번 달 통계</b>\n"
            f"- 완료한 일정: {month_s['done']}개\n"
            f"- 미완료 일정: {month_s['not_done']}개\n"
            f"- 회고 작성률: {month_r['rate']:.0f}% ({month_r['written']}/{month_r['total']})"
        )
        await update.message.reply_text(msg, parse_mode="HTML")

    async def motivate_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """명언/동기부여 랜덤 전송"""
        quote = random.choice(MOTIVATIONAL_QUOTES)
        message = f"💫 **오늘의 동기부여**\n\n{quote}\n\n✨ 당신은 충분히 대단한 사람입니다!"
        await update.message.reply_text(message)
    
    async def ai_schedule_summary(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """AI 일정 요약/분석"""
        user_id = update.effective_user.id
        schedules = self.db.get_schedules(user_id)
        
        if not schedules:
            await update.message.reply_text("📅 분석할 일정이 없습니다. 먼저 일정을 추가해보세요!")
            return
        
        if not self.ai_helper.is_available():
            await update.message.reply_text("❌ AI 기능을 사용할 수 없습니다. OpenAI API 키를 설정해주세요.")
            return
        
        await update.message.reply_text("🤖 일정을 분석하고 있습니다...")
        
        analysis = self.ai_helper.get_schedule_summary(schedules)
        
        message = f"🤖 **AI 일정 분석**\n\n{analysis}"
        
        await update.message.reply_text(message)
    
    def get_random_completion_message(self) -> str:
        """완료 시 랜덤 응원 메시지 반환"""
        return random.choice(COMPLETION_MESSAGES)

    # 루틴(반복 일정) 관리 함수들
    async def add_routine(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """루틴 추가 시작"""
        await update.message.reply_text("🔄 루틴의 제목을 입력해주세요:")
        return WAITING_ROUTINE_TITLE
    
    async def routine_title(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """루틴 제목 입력 처리"""
        user_id = update.effective_user.id
        title = update.message.text
        
        self.user_states[user_id] = {'title': title}
        await update.message.reply_text("📄 루틴에 대한 설명을 입력해주세요 (선택사항):")
        return WAITING_ROUTINE_DESC
    
    async def routine_description(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """루틴 설명 입력 처리"""
        user_id = update.effective_user.id
        description = update.message.text
        
        self.user_states[user_id]['description'] = description
        await update.message.reply_text("🔄 반복 주기를 선택해주세요:\n\n1️⃣ 매일\n2️⃣ 매주\n3️⃣ 매월")
        return WAITING_ROUTINE_FREQ
    
    async def routine_frequency(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """루틴 반복 주기 입력 처리"""
        user_id = update.effective_user.id
        freq_text = update.message.text
        
        freq_map = {'1': 'daily', '2': 'weekly', '3': 'monthly', '매일': 'daily', '매주': 'weekly', '매월': 'monthly'}
        frequency = freq_map.get(freq_text.strip())
        
        if not frequency:
            await update.message.reply_text("❌ 잘못된 선택입니다. 1, 2, 3 중에서 선택해주세요.")
            return WAITING_ROUTINE_FREQ
        
        self.user_states[user_id]['frequency'] = frequency
        
        if frequency == 'weekly':
            await update.message.reply_text("📅 반복할 요일을 선택해주세요 (쉼표로 구분):\n\n1=월, 2=화, 3=수, 4=목, 5=금, 6=토, 7=일\n\n예: 1,3,5 (월,수,금)")
            return WAITING_ROUTINE_DAYS
        else:
            await update.message.reply_text("📅 시작 날짜를 입력해주세요 (YYYY-MM-DD 형식):")
            return WAITING_ROUTINE_DATE
    
    async def routine_days(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """루틴 요일 입력 처리"""
        user_id = update.effective_user.id
        days_text = update.message.text
        
        try:
            # 요일 번호 검증
            days = [int(d.strip()) for d in days_text.split(',')]
            if not all(1 <= d <= 7 for d in days):
                raise ValueError("잘못된 요일 번호")
            
            self.user_states[user_id]['days_of_week'] = ','.join(map(str, days))
            await update.message.reply_text("📅 시작 날짜를 입력해주세요 (YYYY-MM-DD 형식):")
            return WAITING_ROUTINE_DATE
        except ValueError:
            await update.message.reply_text("❌ 잘못된 요일 형식입니다. 1-7 사이의 숫자를 쉼표로 구분해서 입력해주세요.")
            return WAITING_ROUTINE_DAYS
    
    async def routine_date(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """루틴 시작 날짜 입력 처리"""
        user_id = update.effective_user.id
        date_text = update.message.text
        
        try:
            # 날짜 형식 검증
            datetime.datetime.strptime(date_text, '%Y-%m-%d')
            self.user_states[user_id]['start_date'] = date_text
            await update.message.reply_text("⏰ 루틴 시간을 입력해주세요 (HH:MM 형식, 선택사항):")
            return WAITING_ROUTINE_TIME
        except ValueError:
            await update.message.reply_text("❌ 잘못된 날짜 형식입니다. YYYY-MM-DD 형식으로 입력해주세요.")
            return WAITING_ROUTINE_DATE
    
    async def routine_time(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """루틴 시간 입력 처리 및 저장"""
        user_id = update.effective_user.id
        time_text = update.message.text
        
        try:
            if time_text.strip():
                # 시간 형식 검증
                datetime.datetime.strptime(time_text, '%H:%M')
                time = time_text
            else:
                time = None
            
            # 루틴 저장
            state = self.user_states[user_id]
            success = self.db.add_routine(
                user_id=user_id,
                title=state['title'],
                description=state['description'],
                frequency=state['frequency'],
                start_date=state['start_date'],
                end_date=None,
                time=time,
                days_of_week=state.get('days_of_week')
            )
            
            if success:
                freq_text = {'daily': '매일', 'weekly': '매주', 'monthly': '매월'}[state['frequency']]
                message = f"✅ 루틴이 성공적으로 추가되었습니다!\n\n🔄 {state['title']}\n📅 {freq_text} 반복\n📆 시작: {state['start_date']}"
                if time:
                    message += f"\n⏰ {time}"
                if state.get('days_of_week'):
                    day_names = ['월', '화', '수', '목', '금', '토', '일']
                    days = [day_names[int(d)-1] for d in state['days_of_week'].split(',')]
                    message += f"\n📅 {', '.join(days)}요일"
                
                await update.message.reply_text(message)
            else:
                await update.message.reply_text("❌ 루틴 추가 중 오류가 발생했습니다.")
            
            # 상태 초기화
            if user_id in self.user_states:
                del self.user_states[user_id]
            return ConversationHandler.END
            
        except ValueError:
            await update.message.reply_text("❌ 잘못된 시간 형식입니다. HH:MM 형식으로 입력해주세요.")
            return WAITING_ROUTINE_TIME
    
    async def view_routines(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """루틴 조회"""
        user_id = update.effective_user.id
        routines = self.db.get_routines(user_id)
        
        if not routines:
            await update.message.reply_text("🔄 등록된 루틴이 없습니다.")
            return
        
        message = "🔄 **등록된 루틴 목록**\n\n"
        for routine in routines:
            freq_text = {'daily': '매일', 'weekly': '매주', 'monthly': '매월'}[routine['frequency']]
            time_str = f" ⏰ {routine['time']}" if routine['time'] else ""
            desc_str = f"\n  📄 {routine['description']}" if routine['description'] else ""
            
            message += f"• {routine['title']}{time_str}\n"
            message += f"  📅 {freq_text} 반복{desc_str}\n"
            if routine['days_of_week']:
                day_names = ['월', '화', '수', '목', '금', '토', '일']
                days = [day_names[int(d)-1] for d in routine['days_of_week'].split(',')]
                message += f"  📅 {', '.join(days)}요일\n"
            message += "\n"
        
        await update.message.reply_text(message)
    
    async def view_today_routines(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """오늘의 루틴 조회"""
        user_id = update.effective_user.id
        today_routines = self.db.get_today_routines(user_id)
        
        if not today_routines:
            await update.message.reply_text("🔄 오늘의 루틴이 없습니다.")
            return
        
        message = "🔄 **오늘의 루틴**\n\n"
        for routine in today_routines:
            time_str = f"⏰ {routine['time']} " if routine['time'] else ""
            desc_str = f"\n  📄 {routine['description']}" if routine['description'] else ""
            status = "✅ 완료" if routine.get('is_done') else "⏳ 진행중"
            
            message += f"• {time_str}{routine['title']} - {status}{desc_str}\n"
            
            # 완료 버튼 추가
            if not routine.get('is_done'):
                keyboard = [[InlineKeyboardButton("✅ 완료", callback_data=f"routine_done_{routine['id']}")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text(message, reply_markup=reply_markup)
                message = ""
            else:
                message += "\n"
        
        if message:
            await update.message.reply_text(message)
    
    async def routine_done_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """루틴 완료 버튼 콜백 처리"""
        query = update.callback_query
        await query.answer()
        user_id = query.from_user.id
        data = query.data
        
        if data.startswith("routine_done_"):
            routine_id = int(data.split("_")[2])
            today = datetime.datetime.now().strftime('%Y-%m-%d')
            
            # DB에서 완료 처리
            success = self.db.update_routine_completion(routine_id, today, True)
            if success:
                await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ 완료됨", callback_data="routine_done_disabled", disabled=True)]]))
                await query.edit_message_text(f"{query.message.text}\n\n🎉 루틴을 완료하셨습니다!")
            else:
                await query.answer("루틴 완료 처리에 실패했습니다.", show_alert=True)

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

def main():
    """메인 함수"""
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN이 설정되지 않았습니다. .env 파일을 확인해주세요.")
        return
    
    bot = ScheduleBot()
    
    # APScheduler 문제를 피하기 위해 더 간단한 방식으로 Application 생성
    try:
        application = Application.builder().token(BOT_TOKEN).build()
    except Exception as e:
        print(f"⚠️  Application 생성 중 오류: {e}")
        print("🔧 대체 방법으로 봇을 시작합니다...")
        # 더 간단한 방식으로 시도
        from telegram.ext import Updater
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
    
    # 일정 수정 대화 핸들러
    edit_handler = ConversationHandler(
        entry_points=[CommandHandler('edit_schedule', bot.edit_schedule)],
        states={
            WAITING_EDIT_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.edit_title)],
            WAITING_EDIT_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.edit_description)],
            WAITING_EDIT_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.edit_date)],
            WAITING_EDIT_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.edit_time)],
        },
        fallbacks=[CommandHandler('cancel', bot.cancel)]
    )
    
    # 회고 작성 대화 핸들러
    reflection_handler = ConversationHandler(
        entry_points=[
            CommandHandler('daily_reflection', bot.daily_reflection),
            CommandHandler('weekly_reflection', bot.weekly_reflection),
            CommandHandler('monthly_reflection', bot.monthly_reflection)
        ],
        states={
            WAITING_DAILY_FACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.daily_fact)],
            WAITING_DAILY_THINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.daily_think)],
            WAITING_DAILY_TODO: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.daily_todo)],
            WAITING_WEEKLY_FACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.weekly_fact)],
            WAITING_WEEKLY_THINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.weekly_think)],
            WAITING_WEEKLY_TODO: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.weekly_todo)],
            WAITING_WEEKLY_TODO_FINAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.weekly_todo_final)],
            WAITING_MONTHLY_FACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.monthly_fact)],
            WAITING_MONTHLY_THINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.monthly_think)],
            WAITING_MONTHLY_TODO: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.monthly_todo)],
            WAITING_MONTHLY_TODO_FINAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.monthly_todo_final)],
        },
        fallbacks=[CommandHandler('cancel', bot.cancel)]
    )
    
    # AI 묵상 대화 핸들러
    ai_reflection_handler = ConversationHandler(
        entry_points=[CommandHandler('ai_reflection', bot.ai_reflection)],
        states={
            WAITING_AI_REFLECTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, bot.ai_reflection_response),
                CallbackQueryHandler(bot.ai_reflection_callback)
            ],
        },
        fallbacks=[CommandHandler('cancel', bot.cancel)]
    )
    
    # ChatGPT 대화 핸들러
    chatgpt_handler = ConversationHandler(
        entry_points=[CommandHandler('chatgpt', bot.chatgpt)],
        states={
            WAITING_CHATGPT: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.chatgpt_response)],
        },
        fallbacks=[CommandHandler('cancel', bot.cancel)]
    )
    
    # 루틴 추가 대화 핸들러
    routine_handler = ConversationHandler(
        entry_points=[CommandHandler('add_routine', bot.add_routine)],
        states={
            WAITING_ROUTINE_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.routine_title)],
            WAITING_ROUTINE_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.routine_description)],
            WAITING_ROUTINE_FREQ: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.routine_frequency)],
            WAITING_ROUTINE_DAYS: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.routine_days)],
            WAITING_ROUTINE_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.routine_date)],
            WAITING_ROUTINE_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.routine_time)],
        },
        fallbacks=[CommandHandler('cancel', bot.cancel)]
    )
    
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
    
    # 핸들러 등록
    application.add_handler(CommandHandler("start", bot.start))
    application.add_handler(CommandHandler("help", bot.help_command))
    application.add_handler(schedule_handler)
    application.add_handler(edit_handler)
    application.add_handler(reflection_handler)
    application.add_handler(ai_reflection_handler)
    application.add_handler(chatgpt_handler)
    application.add_handler(routine_handler)
    application.add_handler(voice_reflection_handler)
    application.add_handler(image_reflection_handler)
    application.add_handler(CommandHandler("view_schedule", bot.view_schedule))
    application.add_handler(CommandHandler("delete_schedule", bot.delete_schedule))
    application.add_handler(CommandHandler("view_routines", bot.view_routines))
    application.add_handler(CommandHandler("today_routines", bot.view_today_routines))
    application.add_handler(CommandHandler("view_reflections", bot.view_reflections))
    application.add_handler(CommandHandler("feedback", bot.feedback))
    application.add_handler(CommandHandler("ai_feedback", bot.ai_feedback))
    application.add_handler(CommandHandler("ai_pattern_analysis", bot.ai_pattern_analysis))
    application.add_handler(CommandHandler("ai_schedule_summary", bot.ai_schedule_summary))
    application.add_handler(CommandHandler("stats", bot.stats_command))
    application.add_handler(CommandHandler("motivate", bot.motivate_command))
    
    # 콜백 핸들러
    application.add_handler(CallbackQueryHandler(bot.edit_schedule_callback, pattern="^edit_"))
    application.add_handler(CallbackQueryHandler(bot.delete_schedule_callback, pattern="^delete_"))
    application.add_handler(CallbackQueryHandler(bot.schedule_done_callback, pattern="^done_"))
    application.add_handler(CallbackQueryHandler(bot.schedule_done_callback, pattern="^done_disabled$"))
    application.add_handler(CallbackQueryHandler(bot.routine_done_callback, pattern="^routine_done_"))
    application.add_handler(CallbackQueryHandler(bot.routine_done_callback, pattern="^routine_done_disabled$"))
    
    # 봇 시작
    print("🤖 텔레그램 봇이 시작되었습니다...")
    if bot.ai_helper.is_available():
        print("✅ AI 기능이 활성화되었습니다.")
    else:
        print("⚠️  AI 기능이 비활성화되었습니다. OpenAI API 키를 설정해주세요.")
    
    # 알림 스케줄링 설정
    try:
        if hasattr(application, 'job_queue') and application.job_queue:
            application.job_queue.run_daily(
                bot.send_morning_notifications,
                time=datetime.time(hour=8, minute=0),
                days=(0, 1, 2, 3, 4, 5, 6)
            )
            # 일정 종료 알림(매분 체크)
            application.job_queue.run_repeating(
                bot.send_end_notifications,
                interval=60,  # 60초마다
                first=0
            )
            print("✅ 아침 8시/종료 알림 스케줄이 설정되었습니다.")
        else:
            print("⚠️  JobQueue가 설정되지 않아 알림 기능이 비활성화되었습니다.")
    except Exception as e:
        print(f"⚠️  알림 스케줄 설정 중 오류: {e}")
    
    application.run_polling()

if __name__ == '__main__':
    main() 