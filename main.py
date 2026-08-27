import requests
import time
import json
import sqlite3
import sys

# Настройки
TOKEN = " 8941382272:AAEhyVrvq21MZUrls1Ng0KanIz0E6bZLi8M"
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"
OFFSET = 0

# База данных
class Database:
    def __init__(self):
        self.conn = sqlite3.connect('users.db')
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                status INTEGER DEFAULT 0,
                rival_id INTEGER DEFAULT 0
            )
        ''')
        self.conn.commit()
    
    def get_user(self, user_id):
        self.cursor.execute("SELECT user_id, status, rival_id FROM users WHERE user_id = ?", (user_id,))
        result = self.cursor.fetchone()
        if result:
            return {"user_id": result[0], "status": result[1], "rival_id": result[2]}
        return None
    
    def add_user(self, user_id):
        self.cursor.execute("INSERT OR IGNORE INTO users (user_id, status, rival_id) VALUES (?, 0, 0)", (user_id,))
        self.conn.commit()
    
    def get_search_count(self):
        self.cursor.execute("SELECT COUNT(*) FROM users WHERE status = 1")
        return self.cursor.fetchone()[0]
    
    def start_search(self, user_id):
        self.cursor.execute("UPDATE users SET status = 1, rival_id = 0 WHERE user_id = ?", (user_id,))
        self.conn.commit()
    
    def stop_search(self, user_id):
        self.cursor.execute("UPDATE users SET status = 0, rival_id = 0 WHERE user_id = ?", (user_id,))
        self.conn.commit()
    
    def find_rival(self, user_id):
        self.cursor.execute("SELECT user_id FROM users WHERE status = 1 AND user_id != ? LIMIT 1", (user_id,))
        result = self.cursor.fetchone()
        return result[0] if result else None
    
    def start_chat(self, user_id, rival_id):
        self.cursor.execute("UPDATE users SET status = 2, rival_id = ? WHERE user_id = ?", (rival_id, user_id))
        self.cursor.execute("UPDATE users SET status = 2, rival_id = ? WHERE user_id = ?", (user_id, rival_id))
        self.conn.commit()
    
    def stop_chat(self, user_id, rival_id):
        self.cursor.execute("UPDATE users SET status = 0, rival_id = 0 WHERE user_id = ?", (user_id,))
        self.cursor.execute("UPDATE users SET status = 0, rival_id = 0 WHERE user_id = ?", (rival_id,))
        self.conn.commit()
    
    def close(self):
        self.conn.close()

db = Database()

def send_message(chat_id, text, keyboard=None):
    url = f"{BASE_URL}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    if keyboard:
        data["reply_markup"] = json.dumps(keyboard)
    try:
        response = requests.post(url, data=data, timeout=10)
        return response.json()
    except Exception as e:
        print(f"Error sending message: {e}")
        return None

def create_keyboard(buttons):
    return {
        "keyboard": [[{"text": btn}] for btn in buttons],
        "resize_keyboard": True,
        "one_time_keyboard": False
    }

def handle_message(message):
    user_id = message["from"]["id"]
    text = message.get("text", "")
    
    user = db.get_user(user_id)
    if user is None:
        db.add_user(user_id)
        user = db.get_user(user_id)
    
    # Команда /start
    if text == "/start":
        keyboard = create_keyboard(["🔎 Найти чат"])
        send_message(
            user_id,
            f"👥 Добро пожаловать в Анонимный Чат Бот!\n"
            f"👁‍🗨 Людей в поиске: {db.get_search_count()}",
            keyboard
        )
        return
    
    # Кнопка "Найти чат"
    if text == "🔎 Найти чат":
        if user["status"] == 2:
            send_message(user_id, "❌ Вы уже в диалоге!", create_keyboard(["❌ Завершить диалог"]))
            return
        
        rival_id = db.find_rival(user_id)
        
        if rival_id is None:
            db.start_search(user_id)
            keyboard = create_keyboard(["❌ Завершить поиск"])
            send_message(
                user_id,
                f"🔎 Вы начали поиск собеседника...\n"
                f"👁‍🗨 Людей в поиске: {db.get_search_count()}",
                keyboard
            )
        else:
            db.start_chat(user_id, rival_id)
            keyboard = create_keyboard(["❌ Завершить диалог"])
            
            msg = "✅ Собеседник найден!\nЧтобы завершить диалог, нажмите кнопку ниже."
            send_message(user_id, msg, keyboard)
            send_message(rival_id, msg, keyboard)
        return
    
    # Кнопка "Завершить поиск"
    if text == "❌ Завершить поиск":
        if user["status"] == 1:
            db.stop_search(user_id)
            keyboard = create_keyboard(["🔎 Найти чат"])
            send_message(user_id, "✅ Вы завершили поиск собеседника", keyboard)
        return
    
    # Кнопка "Завершить диалог"
    if text == "❌ Завершить диалог":
        if user["status"] == 2:
            rival_id = user["rival_id"]
            db.stop_chat(user_id, rival_id)
            
            keyboard = create_keyboard(["🔎 Найти чат"])
            send_message(user_id, "✅ Вы завершили диалог", keyboard)
            send_message(rival_id, "❌ Собеседник завершил диалог", keyboard)
        return
    
    # Отправка сообщения собеседнику
    if user["status"] == 2 and text:
        rival_id = user["rival_id"]
        send_message(rival_id, text)

def main():
    print("Bot started successfully!")
    offset = 0
    last_update_time = time.time()
    
    while True:
        try:
            url = f"{BASE_URL}/getUpdates"
            params = {"offset": offset, "timeout": 30}
            response = requests.get(url, params=params, timeout=35)
            updates = response.json().get("result", [])
            
            for update in updates:
                offset = update["update_id"] + 1
                if "message" in update:
                    handle_message(update["message"])
            
            # Каждые 5 минут выводим статус
            if time.time() - last_update_time > 300:
                print(f"Bot is running. Users: {db.get_search_count()} in search")
                last_update_time = time.time()
            
            time.sleep(1)
            
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Bot stopped")
    finally:
        db.close()