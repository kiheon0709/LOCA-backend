#!/usr/bin/env python3
"""
Contest 테이블에 deadline 컬럼을 추가하는 마이그레이션 스크립트
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SQLALCHEMY_DATABASE_URL

def migrate_deadline_column():
    """Contest 테이블에 deadline 컬럼을 추가합니다."""
    
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    
    try:
        with engine.connect() as connection:
            # deadline 컬럼이 이미 존재하는지 확인 (SQLite용)
            result = connection.execute(text("""
                PRAGMA table_info(contests)
            """))
            
            columns = [row[1] for row in result.fetchall()]
            if 'deadline' in columns:
                print("deadline 컬럼이 이미 존재합니다.")
                return
            
            # deadline 컬럼 추가 (SQLite용)
            connection.execute(text("""
                ALTER TABLE contests 
                ADD COLUMN deadline DATETIME
            """))
            
            connection.commit()
            print("deadline 컬럼이 성공적으로 추가되었습니다.")
            
    except Exception as e:
        print(f"마이그레이션 중 오류 발생: {e}")
        raise

if __name__ == "__main__":
    print("Contest 테이블에 deadline 컬럼 추가 중...")
    migrate_deadline_column()
    print("마이그레이션 완료!")
