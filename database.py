import sqlite3
import datetime
from typing import List, Dict, Optional
from config import DATABASE_PATH

class Database:
    def __init__(self):
        self.db_path = DATABASE_PATH
        self.init_database()
    
    def init_database(self):
        """데이터베이스 테이블 초기화"""
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
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
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
            
            conn.commit()
    
    def add_schedule(self, user_id: int, title: str, description: str, date: str, time: Optional[str] = None) -> bool:
        """일정 추가"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO schedules (user_id, title, description, date, time)
                    VALUES (?, ?, ?, ?, ?)
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