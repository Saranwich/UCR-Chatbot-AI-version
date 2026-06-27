from google import genai
from google.genai import errors as genai_errors
from app.config import GEMINI_API_KEY

# 📌 แยกการตั้งค่า AI มาไว้ที่ไฟล์นี้ทั้งหมด (Separation of Concerns)
# ถ้าเปลี่ยนโมเดล หรือเปลี่ยนค่าย (เช่นกลับไปใช้ Claude) เราแก้แค่ไฟล์นี้ไฟล์เดียว
gemini_client = genai.Client(api_key=GEMINI_API_KEY)

# ponytail: เก็บ chat session ใน RAM ต่อ user_id — รีเซ็ตเมื่อ restart server
# ถ้าต้องจำข้ามการ restart ค่อยย้ายไป DB/Redis
chat_sessions = {}


def get_ai_response(user_id: str, user_message: str) -> tuple[str, str | None]:
    """
    รับข้อความจากผู้ใช้ ส่งให้ Gemini (จำบริบทการคุยต่อ user_id)
    คืน (status, text):
      ("ok", คำตอบ)        = สำเร็จ
      ("rate_limit", None) = โดน rate limit / quota หมด (HTTP 429)
      ("error", None)      = error อื่นๆ
    -> save ได้เฉพาะตอน status == "ok" เท่านั้น
    """
    # ผู้ใช้ใหม่ = เปิด chat session ใหม่ (ตัว session จะจำ history ให้เราเอง)
    if user_id not in chat_sessions:
        chat_sessions[user_id] = gemini_client.chats.create(model="gemini-2.5-flash")

    try:
        response = chat_sessions[user_id].send_message(user_message)
        return ("ok", response.text)
    except genai_errors.ClientError as e:
        # ClientError = error ฝั่ง request (4xx). 429 = ติด rate limit / quota หมด
        if e.code == 429:
            print(f"[AI RATE LIMIT] user={user_id}: {e}")
            return ("rate_limit", None)
        print(f"[AI CLIENT ERROR] user={user_id}: {e.code} {e}")
        return ("error", None)
    except Exception as e:
        # error อื่นๆ ทั้งหมด (เซิร์ฟเวอร์ล่ม, เน็ตหลุด, bug) — log ไว้ดูฝั่ง server
        print(f"[AI ERROR] user={user_id}: {type(e).__name__}: {e}")
        return ("error", None)
