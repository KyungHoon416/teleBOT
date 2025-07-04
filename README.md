# 🤖 봇에 대한 도움이 필요하시나요?

아래 설명서를 참고하시면 처음 사용하는 분도 쉽게 따라할 수 있습니다!

---

# 📋 텔레그램 일정/회고/루틴/AI 통합 봇 사용 설명서
━━━━━━━━━━━━━━━━━━━━━━

## 1️⃣ 시작하기

- **텔레그램에서 봇 찾기**
  - 검색창에 `@MyLoging_bot` 입력 후 채팅 시작
- **봇 활성화**
  - `/start` 입력 → 환영 메시지 확인
- **도움말 보기**
  - `/help` 입력 → 모든 명령어와 사용법 안내

━━━━━━━━━━━━━━━━━━━━━━

## 2️⃣ 주요 기능별 사용법

### 🗓️ 일정 관리

- **일정 추가**
  - `/add_schedule` 입력 → 날짜, 시간, 내용을 순서대로 입력
  - 예시:
    ```
    /add_schedule
    2024-07-01
    08:00
    아침 미팅
    ```
- **일정 조회**
  - `/view_schedule` 입력 → 날짜(예: 2024-07-01) 또는 `전체` 입력
- **일정 수정/삭제**
  - `/edit_schedule` 또는 `/delete_schedule` 입력 → 날짜/번호 선택 후 수정/삭제

### 🔄 루틴(반복 일정) 관리

- **루틴 추가**
  - `/add_routine` 입력 → 루틴 이름, 반복 요일(예: 월,수,금), 시간 입력
- **오늘의 루틴 보기**
  - `/today_routines` 입력
- **루틴 완료 체크**
  - `/done_routine` 입력 → 오늘 완료한 루틴 번호 입력

### 📖 회고/피드백/AI

- **일일 회고 작성**
  - `/daily_reflection` 입력 → 오늘 회고 작성
- **회고 피드백**
  - `/feedback` 입력 → 최근 회고에 대한 AI 피드백 제공
- **AI 루틴 분석**
  - `/analyze_routines` 입력 → 최근 1주일간 루틴 패턴/성공률/AI 인사이트 제공

### 💡 기타

- **동기부여 메시지**
  - `/motivate` 입력 → 랜덤 명언/동기부여 메시지 받기
- **도움말**
  - `/help` 입력

━━━━━━━━━━━━━━━━━━━━━━

## 3️⃣ 사용 꿀팁

- 날짜는 `YYYY-MM-DD`, 시간은 `HH:MM` 형식으로 입력하세요.
- 각 명령어를 입력하면 챗봇이 단계별로 안내해줍니다.
- 잘 모르겠으면 언제든 `/help`를 입력하세요!
- 문제가 있거나 궁금한 점이 있으면 `/start`로 다시 시작할 수 있습니다.

━━━━━━━━━━━━━━━━━━━━━━

## 4️⃣ 예시 대화

```
/add_schedule
→ "날짜를 입력해주세요." → 2024-07-01
→ "시간을 입력해주세요." → 08:00
→ "일정 내용을 입력해주세요." → 아침 미팅
→ "일정이 추가되었습니다!"
```

━━━━━━━━━━━━━━━━━━━━━━

## 5️⃣ 자주 묻는 질문(FAQ)

- **Q. 봇이 응답하지 않아요!**
  - A. `/start`로 다시 시작하거나, 네트워크 연결을 확인하세요.
- **Q. AI 기능이 안 돼요!**
  - A. 관리자에게 문의해 OpenAI API 키가 정상 등록되어 있는지 확인하세요.

━━━━━━━━━━━━━━━━━━━━━━

## 6️⃣ 문의/피드백

- 봇 사용 중 불편사항, 개선 요청, 버그 제보는 [이메일/오픈채팅/이슈트래커 등]으로 연락해 주세요.

## 📅 텔레그램 일정관리 & 회고 봇

텔레그램을 통해 일정을 관리하고 회고를 작성할 수 있는 봇입니다.

## 🚀 주요 기능

### 📝 일정 관리
- 일정 추가, 조회, 수정, 삭제
- 날짜별 일정 관리
- 시간 설정 (선택사항)
- 🔔 **자동 아침 알림**: 일정 추가 시 자동으로 아침 8시 알림 설정

### 📖 회고 시스템
- **당일 회고**: 하루를 마무리하며 작성
- **주간 회고**: 한 주를 돌아보며 작성  
- **월간 회고**: 한 달을 정리하며 작성

### 💡 피드백 시스템
- 작성한 회고에 대한 AI 피드백 제공
- 긍정적인 동기부여와 개선점 제안

### 🤖 AI 기능 (GPT-4o-mini)
- **AI와 함께하는 묵상**: GPT-4o-mini와 대화하며 자기 성찰
- **AI 피드백**: 회고에 대한 지능적인 분석과 조언
- **회고 패턴 분석**: 작성한 회고들의 패턴을 분석하여 인사이트 제공
- **동기부여 메시지**: 개인화된 격려 메시지 생성
- **ChatGPT 대화**: 자유로운 질문과 대화

## 🚀 배포 및 공개 사용

### **Render 배포 (추천)**

1. **Render 계정 생성**
   - [Render.com](https://render.com)에서 계정 생성

2. **GitHub 저장소 연결**
   - Render 대시보드에서 "New +" → "Web Service"
   - GitHub 저장소 연결

3. **환경변수 설정**
   - `BOT_TOKEN`: BotFather에서 받은 텔레그램 봇 토큰
   - `OPENAI_API_KEY`: OpenAI API 키 (AI 기능 사용시)

4. **배포**
   - "Create Web Service" 클릭
   - 자동으로 배포 시작

### **공개 봇 사용법**

봇이 배포되면 다른 사람들도 사용할 수 있습니다:

1. **봇 찾기**: 텔레그램에서 봇 사용자명으로 검색
2. **봇 추가**: `/start` 명령어로 시작
3. **기능 사용**: 모든 기능을 개인별로 사용 가능

### **개인 정보 보호**

- 각 사용자의 데이터는 개별적으로 저장
- 사용자 간 데이터 공유 없음
- OpenAI API 키는 서버에서만 사용

## 🛠️ 로컬 설치 및 설정

### 1. 저장소 클론
```bash
git clone <repository-url>
cd teleBOT
```

### 2. 의존성 설치
```bash
pip install -r requirements.txt
```

### 3. 텔레그램 봇 생성
1. 텔레그램에서 [@BotFather](https://t.me/botfather) 찾기
2. `/newbot` 명령어로 새 봇 생성
3. 봇 이름과 사용자명 설정
4. 받은 토큰을 복사

### 4. OpenAI API 키 설정 (AI 기능 사용시)
1. [OpenAI](https://platform.openai.com/)에서 API 키 발급
2. GPT-4o-mini 모델 사용 권한 확인

### 5. 환경변수 설정
```bash
# .env 파일 생성
cp env_example.txt .env

# .env 파일 편집하여 토큰 입력
BOT_TOKEN=your_actual_bot_token_here
OPENAI_API_KEY=your_openai_api_key_here  # AI 기능 사용시
```

### 6. 봇 실행
```bash
python bot.py
```

## 🛠️ 텔레그램 봇 사용법 (초보자용)

1. 텔레그램에서 봇을 찾고 `/start` 입력
2. 원하는 기능의 명령어를 입력 (예: `/add_schedule`)
3. 챗봇의 안내에 따라 단계별로 입력
   - 날짜: 2024-07-01
   - 시간: 09:00
   - 설명: "아침 운동"
4. 완료/수정/삭제/루틴/회고 등도 모두 대화형으로 안내

### 주요 명령어
- `/add_schedule` : 일정 추가
- `/view_schedule` : 일정 보기
- `/edit_schedule` : 일정 수정
- `/delete_schedule` : 일정 삭제
- `/add_routine` : 루틴 추가
- `/view_routines` : 루틴 목록
- `/today_routines` : 오늘의 루틴
- `/complete_schedule` : 일정 완료 체크
- `/routine_analysis` : 루틴 AI 분석
- `/help` : 도움말

**모든 명령어는 챗봇이 친절하게 안내해주니,  
처음 써보는 분도 걱정하지 마세요!**

## 📋 사용법

### 기본 명령어
- `/start` - 봇 시작
- `/help` - 도움말 보기

### 일정 관리
- `/add_schedule` - 일정 추가하기
- `/view_schedule` - 일정 보기
- `/edit_schedule` - 일정 수정하기
- `/delete_schedule` - 일정 삭제하기

### 회고 작성
- `/daily_reflection` - 오늘 회고 작성
- `/weekly_reflection` - 주간 회고 작성
- `/monthly_reflection` - 월간 회고 작성
- `/view_reflections` - 작성한 회고 보기

### 피드백
- `/feedback` - 회고에 대한 피드백 받기 (AI 사용 가능시 AI 피드백, 아니면 기본 피드백)

### AI 기능
- `/ai_reflection` - AI와 함께 묵상하기
- `/ai_feedback` - AI 피드백 받기
- `/ai_pattern_analysis` - 회고 패턴 분석
- `/chatgpt` - ChatGPT와 자유로운 대화하기

## 🗄️ 데이터베이스 구조

### schedules 테이블
- 일정 정보 저장
- 사용자별 일정 관리

### reflections 테이블
- 회고 내용 저장
- 일일/주간/월간 회고 구분

### feedback 테이블
- 회고에 대한 피드백 저장

### notifications 테이블
- 알림 정보 저장
- 사용자별 알림 관리

## 🔧 기술 스택

- **Python 3.8+**
- **python-telegram-bot** - 텔레그램 봇 API
- **SQLite** - 데이터베이스
- **python-dotenv** - 환경변수 관리
- **OpenAI API** - GPT-4o-mini 모델

## 📁 프로젝트 구조

```
teleBOT/
├── bot.py              # 메인 봇 로직
├── database.py         # 데이터베이스 관리
├── ai_helper.py        # AI 기능 관리
├── config.py           # 설정 파일
├── requirements.txt    # 의존성 목록
├── env_example.txt     # 환경변수 예시
├── render.yaml         # Render 배포 설정
├── README.md          # 프로젝트 설명
└── schedule_bot.db    # SQLite 데이터베이스 (자동 생성)
```

## 🎯 AI 기능 상세 설명

### 🤖 AI와 함께하는 묵상
- GPT-4o-mini와 자연스러운 대화를 통해 자기 성찰
- 대화 히스토리를 기억하여 연속적인 대화 가능
- 깊이 있는 질문을 통한 자기 이해 증진

### 💭 AI 피드백
- 회고 내용을 분석하여 개인화된 피드백 제공
- 긍정적 인정, 통찰력, 실용적 조언, 감정적 지원 포함
- 회고 타입별 맞춤형 피드백

### 📊 회고 패턴 분석
- 작성한 회고들의 패턴을 분석
- 주요 주제, 성장 영역, 일관성 등 인사이트 제공
- 더 나은 회고를 위한 구체적 제안

### 💬 ChatGPT와 대화
- GPT-4o-mini와 자유로운 대화 가능
- 질문, 조언, 정보 검색 등 다양한 주제로 대화
- 대화 히스토리를 기억하여 연속적인 대화 가능
- 한국어와 영어 모두 지원

## 💰 비용 고려사항

### OpenAI API 사용료
- GPT-4o-mini: 약 $0.00015 / 1K input tokens, $0.0006 / 1K output tokens
- 일반적인 회고 피드백: 약 $0.01-0.05 정도
- 월 사용량에 따라 비용이 달라질 수 있습니다

### Render 호스팅
- 무료 티어: 월 750시간 (약 31일)
- 유료 플랜: 월 $7부터

## 🎯 향후 개선 계획

- [ ] 일정 알림 기능 (구현 완료)
- [ ] 회고 통계 및 분석
- [ ] 더 정교한 AI 피드백
- [ ] 웹 대시보드 연동
- [ ] 다국어 지원
- [ ] AI 모델 선택 옵션
- [ ] 개인화된 AI 프롬프트

## 🤝 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 📞 문의

프로젝트에 대한 문의사항이 있으시면 이슈를 생성해주세요. 