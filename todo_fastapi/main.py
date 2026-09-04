from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import psycopg2
from psycopg2 import sql
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi import Path

# -----------------------
# 環境変数読み込み
# -----------------------
load_dotenv()
db_password = os.environ.get("PG_PASSWORD")

DB_CONFIG = {
    "host": "localhost",
    "dbname": "todo",
    "user": "postgres",
    "password": db_password,
    "port": 5432,
}

# -----------------------
# FastAPI & CORS設定
# -----------------------
app = FastAPI(title="Todo API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vue 開発サーバー
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------
# パスワードハッシュ用
# -----------------------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# -----------------------
# JWT設定
# -----------------------
SECRET_KEY = "YOUR_SECRET_KEY"  # 長めのランダム文字列にする
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="認証エラー")
        return int(user_id)
    except JWTError:
        raise HTTPException(status_code=401, detail="認証エラー")

# -----------------------
# Pydantic モデル
# -----------------------
class UserCreate(BaseModel):
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class TaskCreate(BaseModel):
    title: str
    description: str | None = None
    status: str
    priority: int
    deadline: str | None = None  # YYYY-MM-DD

# -----------------------
# ユーザー登録
# -----------------------
@app.post("/users/")
def register_user(user: UserCreate):
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = True
        cur = conn.cursor()
        hashed_pw = hash_password(user.password)
        query = sql.SQL("""
            INSERT INTO users (email, password_hash)
            VALUES (%s, %s)
            RETURNING id;
        """)
        cur.execute(query, (user.email, hashed_pw))
        new_id = cur.fetchone()[0]
        return {"status": "ok", "user_id": new_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'cur' in locals(): cur.close()
        if 'conn' in locals(): conn.close()

# -----------------------
# ログイン
# -----------------------
@app.post("/login/")
def login(user: UserLogin):
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("SELECT id, password_hash FROM users WHERE email=%s", (user.email,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=400, detail="ユーザーが存在しません")
        user_id, password_hash = row
        if not verify_password(user.password, password_hash):
            raise HTTPException(status_code=400, detail="パスワードが間違っています")
        access_token = create_access_token(data={"sub": str(user_id)})
        return {"access_token": access_token, "token_type": "bearer"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'cur' in locals(): cur.close()
        if 'conn' in locals(): conn.close()

# -----------------------
# タスク登録（ログイン必須）
# -----------------------
@app.post("/tasks/")
def insert_task(task: TaskCreate, current_user: int = Depends(get_current_user)):
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = True
        cur = conn.cursor()
        sql_query = """
            INSERT INTO tasks (user_id, title, description, status, priority, deadline)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id;
        """
        cur.execute(sql_query, (
            current_user, task.title, task.description,
            task.status, task.priority, task.deadline
        ))
        new_id = cur.fetchone()[0]
        return {"status": "ok", "task_id": new_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'cur' in locals(): cur.close()
        if 'conn' in locals(): conn.close()

# -----------------------
# タスク一覧取得（ログイン必須）
# -----------------------
@app.get("/tasks/")
def show_tasks(current_user: int = Depends(get_current_user)):
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("""
            SELECT id, title, description, status, priority, deadline, created_at, updated_at
            FROM tasks WHERE user_id=%s;
        """, (current_user,))
        rows = cur.fetchall()
        tasks = []
        for row in rows:
            task_id, title, desc, status, priority, deadline, created_at, updated_at = row
            tasks.append({
                "id": task_id,
                "title": title,
                "description": desc,
                "status": status,
                "priority": priority,
                "deadline": str(deadline) if deadline else None,
                "created_at": str(created_at),
                "updated_at": str(updated_at),
            })
        return {"tasks": tasks}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'cur' in locals(): cur.close()
        if 'conn' in locals(): conn.close()


# タスク更新（ログイン必須）
@app.put("/tasks/{task_id}")
def update_task(
    task_id: int = Path(..., description="更新対象のタスクID"),
    task: TaskCreate = None,  # 既存の TaskCreate を再利用（全項目送信）
    current_user: int = Depends(get_current_user),
):
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = True
        cur = conn.cursor()
        sql_query = """
            UPDATE tasks
            SET title=%s, description=%s, status=%s, priority=%s, deadline=%s, updated_at=NOW()
            WHERE id=%s AND user_id=%s
            RETURNING id;
        """
        cur.execute(
            sql_query,
            (task.title, task.description, task.status, task.priority, task.deadline, task_id, current_user),
        )
        result = cur.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="タスクが見つからないか、権限がありません")
        return {"status": "ok", "task_id": result[0]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if "cur" in locals():
            cur.close()
        if "conn" in locals():
            conn.close()

