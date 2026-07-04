import sys
sys.path.insert(0, r'D:\vps\python\ComfyUI-yezhi-api')
import bcrypt, os
from dotenv import load_dotenv

BASE_DIR = r'D:\vps\python\ComfyUI-yezhi-api'
load_dotenv(os.path.join(BASE_DIR, '.env'))

from services.db import get_db_session
from models.user import User, Account

ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'admin@localhost')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')
ADMIN_NICKNAME = os.getenv('ADMIN_NICKNAME', '管理员')

db = get_db_session()
try:
    existing = db.query(User).filter(User.email == ADMIN_EMAIL).first()
    if existing:
        print(f'Admin already exists: {ADMIN_EMAIL}')
        existing.is_admin = True
        existing.is_premium = True
        existing.banned = False
        db.commit()
        print(f'  -> Updated: is_admin=True, is_premium=True')
    else:
        hashed = bcrypt.hashpw(ADMIN_PASSWORD.encode(), bcrypt.gensalt())
        user = User(
            email=ADMIN_EMAIL,
            name=ADMIN_NICKNAME,
            nickname=ADMIN_NICKNAME,
            is_admin=True,
            is_premium=True,
            email_verified=True,
        )
        db.add(user)
        db.flush()
        acc = Account(
            account_id=ADMIN_EMAIL,
            provider_id='credential',
            user_id=user.id,
            password_hash=hashed.decode(),
        )
        db.add(acc)
        db.commit()
        print(f'Admin created: {ADMIN_EMAIL} / {ADMIN_PASSWORD}')
        print(f'  User ID: {user.id}')
finally:
    db.close()
