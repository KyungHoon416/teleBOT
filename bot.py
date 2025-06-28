import logging
import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters, ConversationHandler
from database import Database
from ai_helper import AIHelper
from config import BOT_TOKEN, COMMANDS, DAILY_PROMPTS, WEEKLY_PROMPTS, MONTHLY_PROMPTS, AI_REFLECTION_PROMPTS

# 로깅 설정
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# 대화 상태
WAITING_SCHEDULE_TITLE, WAITING_SCHEDULE_DESC, WAITING_SCHEDULE_DATE, WAITING_SCHEDULE_TIME = range(4)
WAITING_REFLECTION = range(4, 5)
WAITING_FEEDBACK = range(5, 6)
WAITING_EDIT_TITLE, WAITING_EDIT_DESC, WAITING_EDIT_DATE, WAITING_EDIT_TIME = range(6, 10)
WAITING_AI_REFLECTION = range(10, 11)

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
안녕하세요 {user.first_name}님! 👋

📅 일정관리 & 회고 봇입니다.

주요 기능:
• 📝 일정 추가/조회/수정/삭제
• 📖 당일/주간/월간 회고 작성
• 💡 회고에 대한 피드백 제공
• 🤖 AI와 함께하는 묵상 (GPT-4o-mini)

사용 가능한 명령어:
/help - 도움말 보기
/add_schedule - 일정 추가하기
/view_schedule - 일정 보기
/edit_schedule - 일정 수정하기
/delete_schedule - 일정 삭제하기
/daily_reflection - 오늘 회고 작성하기
/weekly_reflection - 주간 회고 작성하기
/monthly_reflection - 월간 회고 작성하기
/view_reflections - 회고 보기
/feedback - 피드백 받기
/ai_reflection - AI와 함께 묵상하기
/ai_feedback - AI 피드백 받기

시작하려면 /help를 입력해주세요!
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

📖 **회고 작성**
/daily_reflection - 오늘 하루 회고
/weekly_reflection - 이번 주 회고
/monthly_reflection - 이번 달 회고
/view_reflections - 작성한 회고 보기

💡 **피드백**
/feedback - 회고에 대한 피드백 받기

🤖 **AI 기능**
/ai_reflection - AI와 함께 묵상하기
/ai_feedback - AI 피드백 받기

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
        """일정 시간 입력 처리"""
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
        user_id = update.effective_user.id
        
        # 오늘 날짜
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        
        # 오늘 일정 조회
        today_schedules = self.db.get_schedules(user_id, today)
        
        if not today_schedules:
            await update.message.reply_text("📅 오늘 등록된 일정이 없습니다.")
            return
        
        message = "📅 **오늘의 일정**\n\n"
        for schedule in today_schedules:
            time_str = f"⏰ {schedule['time']} " if schedule['time'] else ""
            message += f"• {time_str}{schedule['title']}\n"
            if schedule['description']:
                message += f"  📄 {schedule['description']}\n"
            message += "\n"
        
        await update.message.reply_text(message)
    
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
        
        # 일정 삭제
        success = self.db.delete_schedule(schedule_id, user_id)
        
        if success:
            await query.edit_message_text("✅ 일정이 성공적으로 삭제되었습니다!")
        else:
            await query.edit_message_text("❌ 일정 삭제 중 오류가 발생했습니다.")
    
    async def daily_reflection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """일일 회고 시작"""
        user_id = update.effective_user.id
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        
        # 오늘 회고가 이미 있는지 확인
        existing_reflections = self.db.get_reflections(user_id, 'daily', today)
        if existing_reflections:
            await update.message.reply_text("📖 오늘 이미 회고를 작성하셨습니다. 수정하시겠습니까?")
            return WAITING_REFLECTION
        
        prompt = "📖 **오늘 하루 회고를 작성해주세요**\n\n"
        for i, prompt_text in enumerate(DAILY_PROMPTS, 1):
            prompt += f"{i}. {prompt_text}\n"
        prompt += "\n자유롭게 작성해주세요!"
        
        await update.message.reply_text(prompt)
        return WAITING_REFLECTION
    
    async def weekly_reflection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """주간 회고 시작"""
        user_id = update.effective_user.id
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        
        # 이번 주 회고가 이미 있는지 확인
        existing_reflections = self.db.get_reflections(user_id, 'weekly', today)
        if existing_reflections:
            await update.message.reply_text("📖 이번 주 이미 회고를 작성하셨습니다. 수정하시겠습니까?")
            return WAITING_REFLECTION
        
        prompt = "📖 **이번 주 회고를 작성해주세요**\n\n"
        for i, prompt_text in enumerate(WEEKLY_PROMPTS, 1):
            prompt += f"{i}. {prompt_text}\n"
        prompt += "\n자유롭게 작성해주세요!"
        
        await update.message.reply_text(prompt)
        return WAITING_REFLECTION
    
    async def monthly_reflection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """월간 회고 시작"""
        user_id = update.effective_user.id
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        
        # 이번 달 회고가 이미 있는지 확인
        existing_reflections = self.db.get_reflections(user_id, 'monthly', today)
        if existing_reflections:
            await update.message.reply_text("📖 이번 달 이미 회고를 작성하셨습니다. 수정하시겠습니까?")
            return WAITING_REFLECTION
        
        prompt = "📖 **이번 달 회고를 작성해주세요**\n\n"
        for i, prompt_text in enumerate(MONTHLY_PROMPTS, 1):
            prompt += f"{i}. {prompt_text}\n"
        prompt += "\n자유롭게 작성해주세요!"
        
        await update.message.reply_text(prompt)
        return WAITING_REFLECTION
    
    async def save_reflection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """회고 저장"""
        user_id = update.effective_user.id
        content = update.message.text
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        
        # 회고 타입 결정 (간단한 방법으로 구현)
        if "오늘" in content or "하루" in content:
            reflection_type = 'daily'
        elif "주" in content or "이번 주" in content:
            reflection_type = 'weekly'
        elif "달" in content or "이번 달" in content:
            reflection_type = 'monthly'
        else:
            reflection_type = 'daily'  # 기본값
        
        success = self.db.add_reflection(user_id, reflection_type, content, today)
        
        if success:
            await update.message.reply_text("✅ 회고가 성공적으로 저장되었습니다!")
        else:
            await update.message.reply_text("❌ 회고 저장 중 오류가 발생했습니다.")
        
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
            WAITING_REFLECTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.save_reflection)],
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
    
    # 핸들러 등록
    application.add_handler(CommandHandler("start", bot.start))
    application.add_handler(CommandHandler("help", bot.help_command))
    application.add_handler(schedule_handler)
    application.add_handler(edit_handler)
    application.add_handler(reflection_handler)
    application.add_handler(ai_reflection_handler)
    application.add_handler(CommandHandler("view_schedule", bot.view_schedule))
    application.add_handler(CommandHandler("delete_schedule", bot.delete_schedule))
    application.add_handler(CommandHandler("view_reflections", bot.view_reflections))
    application.add_handler(CommandHandler("feedback", bot.feedback))
    application.add_handler(CommandHandler("ai_feedback", bot.ai_feedback))
    application.add_handler(CommandHandler("ai_pattern_analysis", bot.ai_pattern_analysis))
    
    # 콜백 핸들러
    application.add_handler(CallbackQueryHandler(bot.edit_schedule_callback, pattern="^edit_"))
    application.add_handler(CallbackQueryHandler(bot.delete_schedule_callback, pattern="^delete_"))
    
    # 봇 시작
    print("🤖 텔레그램 봇이 시작되었습니다...")
    if bot.ai_helper.is_available():
        print("✅ AI 기능이 활성화되었습니다.")
    else:
        print("⚠️  AI 기능이 비활성화되었습니다. OpenAI API 키를 설정해주세요.")
    application.run_polling()

if __name__ == '__main__':
    main() 