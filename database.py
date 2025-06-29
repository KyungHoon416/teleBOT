import sqlite3
import datetime
from typing import List, Dict, Optional
from config import DATABASE_PATH

class Database:
    def __init__(self):
        self.db_path = DATABASE_PATH
        self.init_database()
    
    def init_database(self):
        """데이터베이스 테이블 초기화 및 마이그레이션"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 일정 테이블
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS schedules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    date TEXT NOT NULL,
                    time TEXT,
                    is_done INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 마이그레이션: is_done 컬럼 없으면 추가
            cursor.execute("PRAGMA table_info(schedules)")
            columns = [row[1] for row in cursor.fetchall()]
            if 'is_done' not in columns:
                cursor.execute('ALTER TABLE schedules ADD COLUMN is_done INTEGER DEFAULT 0')
            
            # 회고 테이블
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS reflections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    type TEXT NOT NULL, -- 'daily', 'weekly', 'monthly'
                    content TEXT NOT NULL,
                    date TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 피드백 테이블
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    reflection_id INTEGER,
                    feedback_text TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (reflection_id) REFERENCES reflections (id)
                )
            ''')
            
            # 알림 테이블
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    schedule_id INTEGER,
                    notification_type TEXT NOT NULL, -- 'morning', 'custom'
                    notification_time TEXT NOT NULL, -- '08:00' 형식
                    message TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (schedule_id) REFERENCES schedules (id)
                )
            ''')
            
            # 루틴(반복 일정) 테이블
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS routines (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    frequency TEXT NOT NULL, -- 'daily', 'weekly', 'monthly'
                    days_of_week TEXT, -- '1,2,3,4,5' (월=1, 화=2, ...)
                    start_date TEXT NOT NULL,
                    end_date TEXT,
                    time TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 루틴 완료 기록 테이블
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS routine_completions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    routine_id INTEGER NOT NULL,
                    completion_date TEXT NOT NULL,
                    is_done BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (routine_id) REFERENCES routines (id)
                )
            ''')
            
            conn.commit()
    
    def add_schedule(self, user_id: int, title: str, description: str, date: str, time: Optional[str] = None) -> bool:
        """일정 추가"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO schedules (user_id, title, description, date, time, is_done)
                    VALUES (?, ?, ?, ?, ?, 0)
                ''', (user_id, title, description, date, time))
                conn.commit()
                return True
        except Exception as e:
            print(f"일정 추가 오류: {e}")
            return False
    
    def get_schedules(self, user_id: int, date: Optional[str] = None) -> List[Dict]:
        """일정 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                if date:
                    cursor.execute('''
                        SELECT * FROM schedules 
                        WHERE user_id = ? AND date = ?
                        ORDER BY time ASC, created_at ASC
                    ''', (user_id, date))
                else:
                    cursor.execute('''
                        SELECT * FROM schedules 
                        WHERE user_id = ?
                        ORDER BY date ASC, time ASC
                    ''', (user_id,))
                
                columns = [description[0] for description in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            print(f"일정 조회 오류: {e}")
            return []
    
    def update_schedule(self, schedule_id: int, user_id: int, title: str, description: str, date: str, time: Optional[str] = None) -> bool:
        """일정 수정"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE schedules 
                    SET title = ?, description = ?, date = ?, time = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ? AND user_id = ?
                ''', (title, description, date, time, schedule_id, user_id))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"일정 수정 오류: {e}")
            return False
    
    def delete_schedule(self, schedule_id: int, user_id: int) -> bool:
        """일정 삭제"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    DELETE FROM schedules 
                    WHERE id = ? AND user_id = ?
                ''', (schedule_id, user_id))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"일정 삭제 오류: {e}")
            return False
    
    def add_reflection(self, user_id: int, reflection_type: str, content: str, date: str) -> bool:
        """회고 추가"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO reflections (user_id, type, content, date)
                    VALUES (?, ?, ?, ?)
                ''', (user_id, reflection_type, content, date))
                conn.commit()
                return True
        except Exception as e:
            print(f"회고 추가 오류: {e}")
            return False
    
    def get_reflections(self, user_id: int, reflection_type: Optional[str] = None, date: Optional[str] = None) -> List[Dict]:
        """회고 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                if reflection_type and date:
                    cursor.execute('''
                        SELECT * FROM reflections 
                        WHERE user_id = ? AND type = ? AND date = ?
                        ORDER BY created_at DESC
                    ''', (user_id, reflection_type, date))
                elif reflection_type:
                    cursor.execute('''
                        SELECT * FROM reflections 
                        WHERE user_id = ? AND type = ?
                        ORDER BY date DESC, created_at DESC
                    ''', (user_id, reflection_type))
                else:
                    cursor.execute('''
                        SELECT * FROM reflections 
                        WHERE user_id = ?
                        ORDER BY date DESC, created_at DESC
                    ''', (user_id,))
                
                columns = [description[0] for description in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            print(f"회고 조회 오류: {e}")
            return []
    
    def add_feedback(self, user_id: int, reflection_id: int, feedback_text: str) -> bool:
        """피드백 추가"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO feedback (user_id, reflection_id, feedback_text)
                    VALUES (?, ?, ?)
                ''', (user_id, reflection_id, feedback_text))
                conn.commit()
                return True
        except Exception as e:
            print(f"피드백 추가 오류: {e}")
            return False
    
    def get_feedback(self, reflection_id: int) -> List[Dict]:
        """피드백 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM feedback 
                    WHERE reflection_id = ?
                    ORDER BY created_at DESC
                ''', (reflection_id,))
                
                columns = [description[0] for description in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            print(f"피드백 조회 오류: {e}")
            return []
    
    def add_notification(self, user_id: int, schedule_id: int, notification_type: str, notification_time: str, message: str) -> bool:
        """알림 추가"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO notifications (user_id, schedule_id, notification_type, notification_time, message)
                    VALUES (?, ?, ?, ?, ?)
                ''', (user_id, schedule_id, notification_type, notification_time, message))
                conn.commit()
                return True
        except Exception as e:
            print(f"알림 추가 오류: {e}")
            return False
    
    def get_notifications(self, user_id: int, notification_type: Optional[str] = None) -> List[Dict]:
        """알림 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                if notification_type:
                    cursor.execute('''
                        SELECT n.*, s.title as schedule_title 
                        FROM notifications n
                        LEFT JOIN schedules s ON n.schedule_id = s.id
                        WHERE n.user_id = ? AND n.notification_type = ? AND n.is_active = 1
                        ORDER BY n.notification_time ASC
                    ''', (user_id, notification_type))
                else:
                    cursor.execute('''
                        SELECT n.*, s.title as schedule_title 
                        FROM notifications n
                        LEFT JOIN schedules s ON n.schedule_id = s.id
                        WHERE n.user_id = ? AND n.is_active = 1
                        ORDER BY n.notification_time ASC
                    ''', (user_id,))
                
                columns = [description[0] for description in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            print(f"알림 조회 오류: {e}")
            return []
    
    def get_last_schedule_id(self, user_id: int) -> Optional[int]:
        """사용자의 마지막 일정 ID 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id FROM schedules 
                    WHERE user_id = ?
                    ORDER BY created_at DESC
                    LIMIT 1
                ''', (user_id,))
                
                result = cursor.fetchone()
                return result[0] if result else None
        except Exception as e:
            print(f"마지막 일정 ID 조회 오류: {e}")
            return None
    
    def update_schedule_done(self, schedule_id: int, user_id: int) -> bool:
        """일정 완료 처리"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE schedules SET is_done = 1, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ? AND user_id = ?
                ''', (schedule_id, user_id))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"일정 완료 처리 오류: {e}")
            return False
    
    def get_schedule_stats(self, user_id: int, period: str = 'week') -> dict:
        """주간/월간 일정 완료/미완료 개수 반환"""
        import datetime
        now = datetime.datetime.now()
        if period == 'week':
            start = (now - datetime.timedelta(days=now.weekday())).strftime('%Y-%m-%d')
            end = (now + datetime.timedelta(days=6-now.weekday())).strftime('%Y-%m-%d')
        elif period == 'month':
            start = now.replace(day=1).strftime('%Y-%m-%d')
            if now.month == 12:
                next_month = now.replace(year=now.year+1, month=1, day=1)
            else:
                next_month = now.replace(month=now.month+1, day=1)
            end = (next_month - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
        else:
            return {'done': 0, 'not_done': 0}
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''SELECT COUNT(*) FROM schedules WHERE user_id = ? AND date BETWEEN ? AND ? AND is_done = 1''', (user_id, start, end))
            done = cursor.fetchone()[0]
            cursor.execute('''SELECT COUNT(*) FROM schedules WHERE user_id = ? AND date BETWEEN ? AND ? AND is_done = 0''', (user_id, start, end))
            not_done = cursor.fetchone()[0]
        return {'done': done, 'not_done': not_done}

    def get_reflection_stats(self, user_id: int, period: str = 'week') -> dict:
        """주간/월간 회고 작성률 반환 (작성/전체/비율)"""
        import datetime
        now = datetime.datetime.now()
        if period == 'week':
            start = (now - datetime.timedelta(days=now.weekday())).strftime('%Y-%m-%d')
            end = (now + datetime.timedelta(days=6-now.weekday())).strftime('%Y-%m-%d')
            total = 7
        elif period == 'month':
            start = now.replace(day=1).strftime('%Y-%m-%d')
            if now.month == 12:
                next_month = now.replace(year=now.year+1, month=1, day=1)
            else:
                next_month = now.replace(month=now.month+1, day=1)
            end = (next_month - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
            total = int(end.split('-')[2])
        else:
            return {'written': 0, 'total': 0, 'rate': 0.0}
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''SELECT COUNT(DISTINCT date) FROM reflections WHERE user_id = ? AND date BETWEEN ? AND ?''', (user_id, start, end))
            written = cursor.fetchone()[0]
        rate = (written / total) * 100 if total > 0 else 0.0
        return {'written': written, 'total': total, 'rate': rate}
    
    # 루틴(반복 일정) 관리 함수들
    def add_routine(self, user_id: int, title: str, description: str, frequency: str, 
                   start_date: str, end_date: Optional[str] = None, time: Optional[str] = None, 
                   days_of_week: Optional[str] = None) -> bool:
        """루틴 추가"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO routines (user_id, title, description, frequency, start_date, end_date, time, days_of_week)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (user_id, title, description, frequency, start_date, end_date, time, days_of_week))
                conn.commit()
                return True
        except Exception as e:
            print(f"루틴 추가 오류: {e}")
            return False
    
    def get_routines(self, user_id: int, active_only: bool = True) -> List[Dict]:
        """루틴 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                if active_only:
                    cursor.execute('''
                        SELECT * FROM routines 
                        WHERE user_id = ? AND is_active = 1
                        ORDER BY created_at DESC
                    ''', (user_id,))
                else:
                    cursor.execute('''
                        SELECT * FROM routines 
                        WHERE user_id = ?
                        ORDER BY created_at DESC
                    ''', (user_id,))
                
                columns = [description[0] for description in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            print(f"루틴 조회 오류: {e}")
            return []
    
    def get_today_routines(self, user_id: int) -> List[Dict]:
        """오늘의 루틴 조회"""
        import datetime
        today = datetime.datetime.now()
        today_str = today.strftime('%Y-%m-%d')
        weekday = today.weekday() + 1  # 월=1, 화=2, ..., 일=7
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT r.*, rc.is_done 
                    FROM routines r
                    LEFT JOIN routine_completions rc ON r.id = rc.routine_id AND rc.completion_date = ?
                    WHERE r.user_id = ? AND r.is_active = 1
                    AND r.start_date <= ?
                    AND (r.end_date IS NULL OR r.end_date >= ?)
                ''', (today_str, user_id, today_str, today_str))
                
                routines = []
                for row in cursor.fetchall():
                    routine = {
                        'id': row[0], 'user_id': row[1], 'title': row[2], 'description': row[3],
                        'frequency': row[4], 'days_of_week': row[5], 'start_date': row[6],
                        'end_date': row[7], 'time': row[8], 'is_active': row[9],
                        'created_at': row[10], 'is_done': row[11] if row[11] is not None else 0
                    }
                    
                    # 주간 루틴인 경우 요일 확인
                    if routine['frequency'] == 'weekly' and routine['days_of_week']:
                        days = [int(d) for d in routine['days_of_week'].split(',')]
                        if weekday in days:
                            routines.append(routine)
                    elif routine['frequency'] == 'daily':
                        routines.append(routine)
                    elif routine['frequency'] == 'monthly':
                        # 월간 루틴은 매월 같은 날짜
                        start_day = int(routine['start_date'].split('-')[2])
                        if today.day == start_day:
                            routines.append(routine)
                
                return routines
        except Exception as e:
            print(f"오늘의 루틴 조회 오류: {e}")
            return []
    
    def update_routine_completion(self, routine_id: int, completion_date: str, is_done: bool = True) -> bool:
        """루틴 완료 상태 업데이트"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # 기존 완료 기록 확인
                cursor.execute('''
                    SELECT id FROM routine_completions 
                    WHERE routine_id = ? AND completion_date = ?
                ''', (routine_id, completion_date))
                
                existing = cursor.fetchone()
                if existing:
                    # 기존 기록 업데이트
                    cursor.execute('''
                        UPDATE routine_completions 
                        SET is_done = ?, created_at = CURRENT_TIMESTAMP
                        WHERE routine_id = ? AND completion_date = ?
                    ''', (is_done, routine_id, completion_date))
                else:
                    # 새 기록 추가
                    cursor.execute('''
                        INSERT INTO routine_completions (routine_id, completion_date, is_done)
                        VALUES (?, ?, ?)
                    ''', (routine_id, completion_date, is_done))
                
                conn.commit()
                return True
        except Exception as e:
            print(f"루틴 완료 상태 업데이트 오류: {e}")
            return False
    
    def delete_routine(self, routine_id: int, user_id: int) -> bool:
        """루틴 삭제"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    DELETE FROM routines 
                    WHERE id = ? AND user_id = ?
                ''', (routine_id, user_id))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"루틴 삭제 오류: {e}")
            return False 