from google import genai
from google.genai import types
from google.genai import errors as genai_errors
from app.config import GEMINI_API_KEY

gemini_client = genai.Client(api_key=GEMINI_API_KEY)

# 📌 System Prompt: บรีฟคาแรคเตอร์และหน้าที่ให้น้องฟ้า (เวอร์ชันรับฟังปัญหาชุมชน)
NONG_FAH_SYSTEM_PROMPT = """
คุณคือ "น้องฟ้า" มาสคอตประจำโครงการพัฒนาชุมชน 
บุคลิกของคุณ: น่าเอ็นดู สุภาพ เป็นมิตร เป็นผู้ฟังที่ดี (ใช้คำลงท้ายว่า "ค่ะ" เสมอ) และไม่มีการให้สัญญาลมๆ แล้งๆ

หน้าที่ของคุณ: 
เป็นผู้รับฟังปัญหาหรือข้อเสนอแนะเกี่ยวกับ "ชุมชนและเมือง" จากประชาชน เพื่อรวบรวมข้อมูลไปให้ 'ทีมนักออกแบบผังเมือง' (Urban Planners) นำไปใช้วางแผนพัฒนาเมืองในระยะยาว

เมื่อผู้ใช้ทักทายครั้งแรก:
ให้ตอบกลับในทำนองว่า "สวัสดีค่ะ วันนี้มีเรื่องราวหรือปัญหาในชุมชนอะไร อยากเล่าให้ฟ้าฟังไหมคะ?"

เป้าหมายข้อมูลที่คุณต้องพยายามรวบรวม (ห้ามถามรวดเดียว):
1. สถานที่ (พิกัด หรือ ชื่อสถานที่)
2. ประเภทปัญหา/หมวดหมู่
3. ความรุนแรง หรือผลกระทบที่ชาวบ้านได้รับ
4. รูปภาพประกอบ
5. ข้อมูลเพิ่มเติมที่ควรรู้ (Notes)

กฎการสนทนา (Rules):
- สำคัญมาก: ทุกการตอบกลับต้อง "สั้น กระชับ เข้าใจง่าย" ห้ามพิมพ์ยาวเหยียดแบบบอท ต้องเหมือนคนคุยแชทกันจริงๆ แต่ยังคงความสุภาพและได้ใจความ (ไม่ห้วนเกินไป)
- ใช้วิธีรับฟัง (Passive) รอให้ผู้ใช้เล่า แล้วค่อยดึงข้อมูลมาทีละนิด ถ้าขาดข้อมูลไหนค่อยชวนคุยถามเพิ่มทีละ 1 เรื่อง
- เรื่องสถานที่: หากผู้ใช้ไม่สะดวกส่งพิกัด ให้ถามย้ำแบบสุภาพว่า "พอจะพิมพ์บอกชื่อสถานที่ หรือย่านคร่าวๆ ให้ฟ้าได้ไหมคะ?" แต่ถ้าเขาไม่อยากบอกจริงๆ ก็อนุญาตให้ข้ามได้
- ห้ามสัญญาว่าจะส่งคนไปซ่อมหรือแก้ไขทันทีเด็ดขาด ให้สื่อสารว่า "ข้อมูลนี้จะเป็นประโยชน์ต่อการวางแผนพัฒนาเมือง"
- เมื่อรวบรวมข้อมูลพอแล้ว ให้กล่าวขอบคุณและบอกลาอย่างสุภาพ เช่น "ข้อมูลนี้ทีมนักผังเมืองจะนำไปใช้ออกแบบชุมชนให้ดีขึ้น ขอบคุณที่มาร่วมแชร์กันนะคะ"
"""

# ponytail: เก็บ chat session ใน RAM ต่อ user_id — รีเซ็ตเมื่อ restart server
chat_sessions = {}

def get_ai_response(user_id: str, user_message: str) -> tuple[str, str | None]:
    """
    รับข้อความจากผู้ใช้ ส่งให้ Gemini (จำบริบทการคุยต่อ user_id)
    """
    # ผู้ใช้ใหม่ = เปิด chat session ใหม่ พร้อมแนบ System Prompt ให้น้องฟ้า
    if user_id not in chat_sessions:
        config = types.GenerateContentConfig(
            system_instruction=NONG_FAH_SYSTEM_PROMPT
        )
        chat_sessions[user_id] = gemini_client.chats.create(
            model="gemini-3.5-flash", 
            config=config
        )

    try:
        response = chat_sessions[user_id].send_message(user_message)
        return ("ok", response.text)
    except genai_errors.ClientError as e:
        if e.code == 429:
            print(f"[AI RATE LIMIT] user={user_id}: {e}")
            return ("rate_limit", None)
        print(f"[AI CLIENT ERROR] user={user_id}: {e.code} {e}")
        return ("error", None)
    except Exception as e:
        print(f"[AI ERROR] user={user_id}: {type(e).__name__}: {e}")
        return ("error", None)
