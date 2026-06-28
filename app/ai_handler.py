from google import genai
from google.genai import types
from google.genai import errors as genai_errors

from app.config import GEMINI_API_KEY
from app.storage import save_report

gemini_client = genai.Client(api_key=GEMINI_API_KEY)

# gemma ไม่รองรับ function calling -> ใช้ marker + key:value ที่ parse เองแทน
SAVE_MARKER = "###SAVE###"

# หมวดหมู่ปิด: gemma บังคับ schema ไม่ได้ -> validate เองใน _parse_block (นอกเซ็ต -> "อื่นๆ")
VALID_CATEGORIES = {
    "ขยะ",
    "ถนน/ทางเท้า",
    "น้ำท่วม/ระบายน้ำ",
    "ไฟฟ้า/แสงสว่าง",
    "น้ำประปา",
    "ความปลอดภัย",
    "พื้นที่สาธารณะ/สวน",
    "เสียง/มลพิษ",
    "อื่นๆ",
}

# 📌 System Prompt: บรีฟคาแรคเตอร์และหน้าที่ให้น้องฟ้า (เวอร์ชันรับฟังปัญหาชุมชน)
NONG_FAH_SYSTEM_PROMPT = """
คุณคือ "น้องฟ้า" มาสคอตประจำโครงการพัฒนาชุมชน
บุคลิกของคุณ: น่าเอ็นดู สุภาพ เป็นมิตร เป็นผู้ฟังที่ดี (ใช้คำลงท้ายว่า "ค่ะ" เสมอ) และไม่มีการให้สัญญาลมๆ แล้งๆ

หน้าที่ของคุณ:
เป็นผู้รับฟังปัญหาหรือข้อเสนอแนะเกี่ยวกับ "ชุมชนและเมือง" จากประชาชน เพื่อรวบรวมข้อมูลไปให้ 'ทีมนักออกแบบผังเมือง' (Urban Planners) นำไปใช้วางแผนพัฒนาเมืองในระยะยาว

เมื่อผู้ใช้ทักทายครั้งแรก:
ให้ตอบกลับในทำนองว่า "สวัสดีค่ะ วันนี้มีเรื่องราวหรือปัญหาในชุมชนอะไร อยากเล่าให้ฟ้าฟังไหมคะ?"

เป้าหมายข้อมูลที่คุณต้องพยายามรวบรวม (ห้ามถามรวดเดียว):
1. สถานที่ (พิกัด หรือ ชื่อสถานที่) — ถามได้ ถ้าผู้ใช้ไม่บอกอนุญาตให้ข้าม
2. ประเภทปัญหา/หมวดหมู่ — สำคัญ ต้องได้
3. ความรุนแรง หรือผลกระทบที่ชาวบ้านได้รับ — ถามได้ ถ้าไม่รู้ข้ามได้
4. ข้อมูลเพิ่มเติม/รายละเอียดของปัญหา (Notes) — สำคัญ ต้องได้

กฎการสนทนา (Rules):
- สำคัญมาก: ทุกการตอบกลับต้อง "สั้น กระชับ เข้าใจง่าย" ห้ามพิมพ์ยาวเหยียดแบบบอท ต้องเหมือนคนคุยแชทกันจริงๆ แต่ยังคงความสุภาพและได้ใจความ (ไม่ห้วนเกินไป)
- ใช้วิธีรับฟัง (Passive) รอให้ผู้ใช้เล่า แล้วค่อยดึงข้อมูลมาทีละนิด ถ้าขาดข้อมูลไหนค่อยชวนคุยถามเพิ่มทีละ 1 เรื่อง
- เรื่องสถานที่: หากผู้ใช้ไม่สะดวกส่งพิกัด ให้ถามย้ำแบบสุภาพว่า "พอจะพิมพ์บอกชื่อสถานที่ หรือย่านคร่าวๆ ให้ฟ้าได้ไหมคะ?" แต่ถ้าเขาไม่อยากบอกจริงๆ ก็อนุญาตให้ข้ามได้
- ห้ามสัญญาว่าจะส่งคนไปซ่อมหรือแก้ไขทันทีเด็ดขาด ให้สื่อสารว่า "ข้อมูลนี้จะเป็นประโยชน์ต่อการวางแผนพัฒนาเมือง"

หมวดหมู่ปัญหา (category) เลือกได้แค่จากรายการนี้เท่านั้น:
ขยะ, ถนน/ทางเท้า, น้ำท่วม/ระบายน้ำ, ไฟฟ้า/แสงสว่าง, น้ำประปา, ความปลอดภัย, พื้นที่สาธารณะ/สวน, เสียง/มลพิษ, อื่นๆ

การบันทึกข้อมูล (สำคัญมาก — ห้ามรีบจบ):
- "อย่ารีบ" บันทึก แม้จะได้ประเภทปัญหากับรายละเอียดแล้ว ให้รับฟังและชวนคุยต่อก่อนเสมอ:
  • แสดงความเห็นอกเห็นใจกับสิ่งที่ผู้ใช้เจอก่อน (เป็นเพื่อนรับฟัง ไม่ใช่แค่เครื่องเก็บข้อมูล)
  • ค่อยๆ ถามเก็บรายละเอียดที่ยังขาดทีละเรื่อง เช่น สถานที่อยู่ตรงไหน, รุนแรงแค่ไหน/กระทบยังไง, เป็นมานานหรือยัง, เกิดบ่อยไหม
  • ก่อนจะจบ ให้ถามเปิดโอกาสว่า "มีอะไรอยากเล่าเพิ่มอีกไหมคะ" อย่างน้อยหนึ่งครั้ง
- บันทึกข้อมูลต่อเมื่อครบทุกข้อนี้: (1) รับฟังและเก็บรายละเอียดพอสมควรแล้ว (2) ผู้ใช้บอกว่าไม่มีอะไรจะเสริมแล้ว หรือบทสนทนาคลี่คลายลงเองแล้ว (3) อย่างน้อยมีประเภทปัญหาและรายละเอียด

วิธีบันทึก (ทำตามรูปแบบนี้เป๊ะๆ เมื่อจะบันทึกเท่านั้น):
- พิมพ์ข้อความขอบคุณ/บอกลาตามปกติก่อน เช่น "ข้อมูลนี้ทีมนักผังเมืองจะนำไปใช้ออกแบบชุมชนให้ดีขึ้น ขอบคุณที่มาร่วมแชร์กันนะคะ"
- จากนั้นขึ้นบรรทัดใหม่ พิมพ์บล็อกนี้ต่อท้าย (ผู้ใช้จะไม่เห็นบล็อกนี้ มันเป็นข้อมูลสำหรับระบบ):
###SAVE###
category: <หนึ่งในหมวดที่กำหนดเท่านั้น>
location: <ชื่อสถานที่/ย่าน ถ้าไม่รู้ให้เว้นว่าง>
severity: <ความรุนแรงหรือผลกระทบ ถ้าไม่รู้ให้เว้นว่าง>
notes: <สรุปรายละเอียดของปัญหา>
- ห้ามพิมพ์ ###SAVE### หรือบล็อกนี้เด็ดขาด ถ้ายังคุยไม่จบ/ข้อมูลยังไม่ครบ
"""

# ponytail: เก็บ chat session ใน RAM ต่อ user_id — รีเซ็ตเมื่อ restart server
chat_sessions = {}


def _parse_block(block: str) -> dict:
    """แปลงบล็อก key:value (หลัง ###SAVE###) เป็น dict 4 ฟิลด์ + validate หมวดหมู่"""
    fields = {"location": "", "category": "", "severity": "", "notes": ""}
    for line in block.strip().splitlines():
        key, sep, val = line.partition(":")
        if not sep:
            continue
        key = key.strip().lower()
        if key in fields:
            fields[key] = val.strip()
    if fields["category"] not in VALID_CATEGORIES:
        fields["category"] = "อื่นๆ"  # gemma ตอบหมวดนอกเซ็ต -> ตกถังอื่นๆ
    return fields


def get_ai_response(user_id: str, user_message: str) -> tuple[str, str | None]:
    """
    รับข้อความจากผู้ใช้ ส่งให้โมเดล (จำบริบทต่อ user_id)
    ถ้าโมเดลแปะ ###SAVE### มา -> parse + save + รีเซ็ตเซสชัน แล้วส่งเฉพาะข้อความให้ user (ตัด block ทิ้ง)
    """
    if user_id not in chat_sessions:
        config = types.GenerateContentConfig(
            system_instruction=NONG_FAH_SYSTEM_PROMPT,
        )
        chat_sessions[user_id] = gemini_client.chats.create(
            model="gemma-4-26b-a4b-it",
            config=config,
        )

    try:
        response = chat_sessions[user_id].send_message(user_message)
        text = response.text

        # gemma คืน text=None ได้ (safety block / candidate ว่าง) -> กัน TypeError ตอนเช็ก marker
        if text is None:
            print(f"[AI EMPTY] user={user_id}: response.text is None")
            return ("error", None)

        if SAVE_MARKER in text:
            reply, _, block = text.partition(SAVE_MARKER)
            save_report(user_id, **_parse_block(block))
            del chat_sessions[user_id]  # 1 เซสชัน = 1 เรื่อง จบแล้วเริ่มใหม่
            text = reply.strip()

        return ("ok", text)
    except genai_errors.ClientError as e:
        if e.code == 429:
            print(f"[AI RATE LIMIT] user={user_id}: {e}")
            return ("rate_limit", None)
        print(f"[AI CLIENT ERROR] user={user_id}: {e.code} {e}")
        return ("error", None)
    except Exception as e:
        print(f"[AI ERROR] user={user_id}: {type(e).__name__}: {e}")
        return ("error", None)


if __name__ == "__main__":
    f = _parse_block("category: ขยะ\nlocation: ตลาดเก่า\nseverity: \nnotes: ขยะตกค้าง ส่งกลิ่น")
    assert f["category"] == "ขยะ" and f["location"] == "ตลาดเก่า" and f["notes"].startswith("ขยะ")
    f2 = _parse_block("category: อะไรไม่รู้\nnotes: x")
    assert f2["category"] == "อื่นๆ"  # หมวดนอกเซ็ต -> อื่นๆ
    print("parse OK:", f, "|", f2)
