import os
import time
import re
import requests
from playwright.sync_api import sync_playwright

# --- 🎯 แก้ไขทางเข้าตรงนี้ให้เข้าหน้าแรกโดยตรง ไม่หลงทาง ---
TARGET_URL = "https://www.dmc.tv/"
LINE_API = "https://api.line.me/v2/bot/message/push"

LINE_TOKEN = os.environ.get("LINE_TOKEN")
LINE_TARGET_ID = os.environ.get("LINE_TARGET_ID")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

def clean_final_message(text):
    """
    🛠️ ฟังก์ชันพิเศษ: ตรวจจับและล้างสิ่งแปลกปลอมในลิงก์บทความก่อนส่งเข้า LINE
    """
    # 1. ถ้า AI เผลอเติม / ปิดท้ายตัวเลขบทความ (เช่น article/34425/) ให้ตัด / ออกเพื่อป้องกัน Bad Gateway
    text = re.sub(r'(https://www\.dmc\.tv/article/\d+)/', r'\1', text)
    
    # 2. ป้องกันกรณี AI แอบใส่วงเล็บปิดมาเบียดท้ายลิงก์ จน LINE แปลงเป็น %5D
    text = text.replace('%5D', '').replace(']', '')
    
    return text

def ask_gemini_to_summarize(raw_web_data):
    if not GEMINI_API_KEY:
        return "⚠️ ไม่ได้ตั้งค่า GEMINI_API_KEY ใน GitHub Secrets"
        
    model_name = 'gemini-2.5-flash'
    url = f"https://generativelanguage.googleapis.com/v1/models/{model_name}:generateContent?key={GEMINI_API_KEY}"
    
    # 🧠 บรีฟคุมเข้ม: ถอดวงเล็บ [] ออกจากโครงสร้าง ห้ามเติม / ปิดท้ายลิงก์เด็ดขาด
    prompt = f"""
    คุณคือนักข่าวสายบุญ ทำหน้าที่สรุปข้อมูลจาก DMC.tv ให้สั้น กระชับ น่าสนใจ และเปี่ยมด้วยบุญบันเทิง 
    (แต่ละข้อเขียนกระชับ 1-2 บรรทัดจบ เพื่อให้อ่านง่ายใน LINE)
    
    [กฎเหล็กเรื่องลิงก์และการห้ามเดา]
    - ห้ามคิด ลิงก์ ขึ้นมาเองเด็ดขาด! เอาลิงก์มาจากข้อมูลดิบเท่านั้น
    - ห้ามเติมเครื่องหมายสแลช (/) ปิดท้ายเลขไอดีบทความเด็ดขาด เช่น article/34425 ห้ามแก้เป็น article/34425/
    - ห้ามใช้เครื่องหมายวงเล็บสี่เหลี่ยม [] ล้อมรอบลิงก์เด็ดขาด ให้ใช้สัญลักษณ์ 🔗 นำหน้าลิงก์แบบปล่อยอิสระ
    - คัดเลือกเฉพาะกิจกรรมในเดือนนี้ และเดือนหน้าเท่านั้น

    ข้อมูลดิบจากหน้าเว็บ:
    \"\"\"{raw_web_data}\"\"\"

    เขียนสรุปส่งเข้า LINE ตามโครงสร้างนี้เท่านั้น (ห้ามมีคำเกริ่นนำของ AI):

    ✨ สรุปงานบุญดีเอ็มซีประจำวัน ✨

    🙏 [ธรรมะสอนใจ]
    • (ดึงโอวาทสั้นๆ 1 ข้อคิด + 🔗 ที่มา: ลิงก์ธรรมะ)

    🧡 [โครงการบวช & อบรม]
    • (สรุปโครงการบวชหรืออบรมที่เปิดรับสมัคร + 🔗 รายละเอียด: ลิงก์ของโครงการ)

    💰 [งานบุญเด่น & กิจกรรมเดือนนี้]
    • (งานบุญเชิญชวนสร้างบารมี เช่น ทอดผ้าป่า บูชาข้าวพระ ตอกเสาเข็ม สรุปสั้นๆ บอกวันชัดเจน + 🔗 ลิงก์ร่วมบุญ: ลิงก์ของงานบุญ)

    💡 [คลังความรู้ที่น่าสนใจ]
    • (สรุปแก่นความรู้วันสำคัญ นิทรรศการ หรือสาระธรรมะ 1-2 ข้อ + 🔗 ความรู้: ลิงก์ที่ตรงกัน)

    🎉 [บันทึกภาพงานบุญชวนอนุโมทนา]
    • (สรุปงานบุญประมวลภาพที่เพิ่งผ่านพ้นไปเพื่อให้ร่วมอนุโมทนาย้อนหลัง + 🔗 รวมรูป: ลิงก์ของข่าว)
    """
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    headers = {"Content-Type": "application/json"}
    
    for attempt in range(3):
        try:
            print(f"📡 ส่งข้อมูลล็อกลิงก์ไปที่รุ่น: {model_name} (รอบที่ {attempt + 1}/3)...")
            res = requests.post(url, headers=headers, json=payload, timeout=30)
            result_json = res.json()
            
            if res.status_code == 200 and 'candidates' in result_json:
                ai_response = result_json['candidates'][0]['content']['parts'][0]['text']
                print("🎉 AI ประมวลผลสำเร็จ ลิงก์แม่นยำ!")
                return ai_response.strip()
                
            elif res.status_code in [503, 429]:
                print(f"⏳ คิวเต็มชั่วคราว รอ 10 วินาที...")
                time.sleep(10)
                continue
            else:
                print(f"❌ พังด้วยรหัส: {res.status_code}")
                break
        except Exception as e:
            print(f"⚠️ ข้อผิดพลาดเทคนิค: {e}")
            time.sleep(5)
            
    return "❌ บอทกูเกิลติดขัดชั่วคราว โปรดกดรันใหม่อีกครั้งครับจ้ะ"

def send_line_message(msg):
    if not LINE_TOKEN or not LINE_TARGET_ID:
        print("⚠️ ไม่ได้ตั้งค่า LINE_TOKEN หรือ LINE_TARGET_ID")
        return
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_TOKEN}"
    }
    payload = {
        "to": LINE_TARGET_ID,
        "messages": [{"type": "text", "text": msg}]
    }
    try:
        res = requests.post(LINE_API, headers=headers, json=payload)
        print(f"📲 Status LINE: {res.status_code}")
    except Exception as e:
        print(f"❌ ส่ง LINE ไม่สำเร็จ: {e}")

def main():
    print("🚀 บอทสายบุญอัจฉริยะ (เวอร์ชันป้องกันลิงก์เอ๋อและกันภัย Bad Gateway) เริ่มรัน...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            page.goto(TARGET_URL, timeout=30000)
            page.wait_for_load_state("networkidle")
            
            links = page.locator('a').all()
            web_data_list = []
            for link in links:
                t = link.inner_text().strip()
                h = link.get_attribute("href")
                if t and len(t) > 12 and h and h.startswith("http") and "dmc.tv" in h:
                    web_data_list.append(f"หัวข้อ: {t} | ลิงก์: {h}")
                    
            raw_web_data = "\n".join(web_data_list[:40])
            browser.close()
            
            print("🧠 ส่งต่อข้อมูลดิบเข้าสู่ระบบคัดกรองแก่นธรรม...")
            ai_report = ask_gemini_to_summarize(raw_web_data)
            
            # 🎯 [จุดสำคัญ] ทำการกรองและล้างลิงก์บทความที่ AI ส่งกลับมา ป้องกันเซิร์ฟเวอร์ปลายทางล่ม
            final_report = clean_final_message(ai_report)
            
            print("\n=== ผลลัพธ์สุดท้าย ===")
            print(final_report)
            
            send_line_message(final_report)

        except Exception as e:
            print(f"❌ ระบบภายนอกพังเนื่องจาก: {e}")
            if 'browser' in locals():
                browser.close()

if __name__ == "__main__":
    main()
