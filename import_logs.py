import os
import pandas as pd
from sqlalchemy import create_engine
import pymysql

# MySQL 연결 설정
DB_HOST = "localhost"
DB_USER = "root"
DB_NAME = "market_db"
TABLE_NAME = "action_logs"
CSV_FILE = r"C:\HDCLab\ai01-3rd-3team\ai_03_action_logs.csv"

# 비밀번호 입력
db_password = input(f"Enter password for user '{DB_USER}': ")

print(f" Reading & Parsing CSV file: {CSV_FILE}...")
data = []
columns = ['timestamp', 'user_ip', 'session_id', 'user_id', 'action', 
           'target_id', 'click_pos_x', 'click_pos_y', 'time_delta', 'extra']

try:
    with open(CSV_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    # 헤더 제외 (첫 줄이 헤더인 경우)
    start_idx = 1 if lines[0].startswith('timestamp') else 0
    
    for i, line in enumerate(lines[start_idx:]):
        line = line.strip()
        if not line: continue
        
        # 단순히 콤마로 합쳐진 파일이라, 'extra'(JSON) 내부의 콤마 때문에 깨짐
        # 해결: 앞에서부터 9번만 자르고(총 10개 필드), 나머지는 묶음
        parts = line.split(',', 9)
        
        if len(parts) == 10:
            data.append(parts)
        elif len(parts) < 10:
            # 필드가 부족한 경우 빈 값으로 채움
            parts.extend([''] * (10 - len(parts)))
            data.append(parts)
        # 10개 넘는 경우는 split maxsplit으로 방지됨
            
    df = pd.DataFrame(data, columns=columns)
    
    print(f"  >> Successfully parsed {len(df)} rows.")
    
    # SQLAlchemy 엔진 생성
    connection_string = f"mysql+mysqlconnector://{DB_USER}:{db_password}@{DB_HOST}/{DB_NAME}"
    engine = create_engine(connection_string)
    
    print(f" Connecting to MySQL ({DB_NAME})...")
    
    # 데이터베이스에 저장
    print(f" Importing to table '{TABLE_NAME}'...")
    df.to_sql(name=TABLE_NAME, con=engine, if_exists='replace', index=False)
    
    print("Succesfully imported!")
    
except Exception as e:
    print(f"Error: {e}")
