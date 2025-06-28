#!/usr/bin/env python3
"""
텔레그램 봇 테스트 파일
실제 봇을 실행하기 전에 기본 기능들을 테스트할 수 있습니다.
"""

import sqlite3
import datetime
from database import Database

def test_database():
    """데이터베이스 기능 테스트"""
    print("🧪 데이터베이스 테스트 시작...")
    
    # 테스트용 데이터베이스 생성
    db = Database()
    
    # 테스트 사용자 ID
    test_user_id = 12345
    
    # 1. 일정 추가 테스트
    print("\n1. 일정 추가 테스트")
    success = db.add_schedule(
        user_id=test_user_id,
        title="테스트 일정",
        description="테스트용 일정입니다.",
        date="2024-01-15",
        time="14:30"
    )
    print(f"일정 추가 결과: {'성공' if success else '실패'}")
    
    # 2. 일정 조회 테스트
    print("\n2. 일정 조회 테스트")
    schedules = db.get_schedules(test_user_id, "2024-01-15")
    print(f"조회된 일정 수: {len(schedules)}")
    for schedule in schedules:
        print(f"  - {schedule['title']} ({schedule['time']})")
    
    # 3. 회고 추가 테스트
    print("\n3. 회고 추가 테스트")
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    success = db.add_reflection(
        user_id=test_user_id,
        reflection_type='daily',
        content="오늘은 테스트를 진행했습니다. 새로운 것을 배우는 하루였습니다.",
        date=today
    )
    print(f"회고 추가 결과: {'성공' if success else '실패'}")
    
    # 4. 회고 조회 테스트
    print("\n4. 회고 조회 테스트")
    reflections = db.get_reflections(test_user_id, 'daily', today)
    print(f"조회된 회고 수: {len(reflections)}")
    for reflection in reflections:
        print(f"  - {reflection['type']}: {reflection['content'][:50]}...")
    
    # 5. 피드백 추가 테스트
    print("\n5. 피드백 추가 테스트")
    if reflections:
        reflection_id = reflections[0]['id']
        success = db.add_feedback(
            user_id=test_user_id,
            reflection_id=reflection_id,
            feedback_text="테스트 회고에 대한 피드백입니다. 잘 작성하셨네요!"
        )
        print(f"피드백 추가 결과: {'성공' if success else '실패'}")
    
    print("\n✅ 데이터베이스 테스트 완료!")

def test_config():
    """설정 파일 테스트"""
    print("\n🧪 설정 파일 테스트 시작...")
    
    try:
        from config import COMMANDS, DAILY_PROMPTS, WEEKLY_PROMPTS, MONTHLY_PROMPTS
        
        print(f"명령어 수: {len(COMMANDS)}")
        print(f"일일 회고 프롬프트 수: {len(DAILY_PROMPTS)}")
        print(f"주간 회고 프롬프트 수: {len(WEEKLY_PROMPTS)}")
        print(f"월간 회고 프롬프트 수: {len(MONTHLY_PROMPTS)}")
        
        print("✅ 설정 파일 테스트 완료!")
        
    except ImportError as e:
        print(f"❌ 설정 파일 임포트 오류: {e}")

def test_bot_import():
    """봇 모듈 임포트 테스트"""
    print("\n🧪 봇 모듈 임포트 테스트 시작...")
    
    try:
        from bot import ScheduleBot
        bot = ScheduleBot()
        print("✅ 봇 클래스 생성 성공!")
        
    except ImportError as e:
        print(f"❌ 봇 모듈 임포트 오류: {e}")
    except Exception as e:
        print(f"❌ 봇 클래스 생성 오류: {e}")

def main():
    """메인 테스트 함수"""
    print("🚀 텔레그램 봇 테스트 시작")
    print("=" * 50)
    
    # 설정 파일 테스트
    test_config()
    
    # 데이터베이스 테스트
    test_database()
    
    # 봇 모듈 테스트
    test_bot_import()
    
    print("\n" + "=" * 50)
    print("🎉 모든 테스트 완료!")
    print("\n📝 다음 단계:")
    print("1. .env 파일에 BOT_TOKEN 설정")
    print("2. python bot.py로 봇 실행")
    print("3. 텔레그램에서 봇과 대화 시작")

if __name__ == "__main__":
    main() 