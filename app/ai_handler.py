from google import genai
from app.config import GEMINI_API_KEY

# 📌 แยกการตั้งค่า AI มาไว้ที่ไฟล์นี้ทั้งหมด (Separation of Concerns)
# ถ้าเปลี่ยนโมเดล หรือเปลี่ยนค่าย (เช่นกลับไปใช้ Claude) เราแก้แค่ไฟล์นี้ไฟล์เดียว
gemini_client = genai.Client(api_key=GEMINI_API_KEY)

# ponytail: เก็บ chat session ใน RAM ต่อ user_id — รีเซ็ตเมื่อ restart server
# ถ้าต้องจำข้ามการ restart ค่อยย้ายไป DB/Redis
chat_sessions = {}


def get_ai_response(user_id: str, user_message: str) -> str:
    """
    รับข้อความจากผู้ใช้ ส่งให้ Gemini (จำบริบทการคุยต่อ user_id) แล้วส่งคำตอบกลับ
    """
    # ผู้ใช้ใหม่ = เปิด chat session ใหม่ (ตัว session จะจำ history ให้เราเอง)
    if user_id not in chat_sessions:
        chat_sessions[user_id] = gemini_client.chats.create(model="gemini-2.5-flash")

    try:
        response = chat_sessions[user_id].send_message(user_message)
        return response.text
    except Exception as e:
        return f"ระบบ AI มีปัญหาครับ: {e}"
