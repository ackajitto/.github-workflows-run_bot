import os
import time
import re
import requests
from playwright.sync_api import sync_playwright

# --- ตั้งค่า URL และ API หลัก ---
TARGET_URL = "https://www.dmc.tv/home/"
LINE_API = "https://api.line.me/v2/bot/message/push"

LINE_TOKEN = os.environ.get("LINE_TOKEN")
LINE_TARGET_ID = os.environ.get("LINE_TARGET_ID")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

def clean_final_message(text):
    """
    🛠️ ฟังก์ชันด่านสุดท้าย: ช่วยล้างสิ่งแปลกปลอมที่อาจหลุดรอดมา เพื่อป้องกัน Bad Gateway
    """
    # 1. ถ้ามี / ปิดท้ายเลขบทความ (เช่น article/34425/) ให้ตัดออกทันที
    text = re.sub(r'(https://www\.dmc\.tv/article/\d+)/', r'\1', text)
    
    # 2. ล้างเศษวงเล็บหรือรหัส %5D ที่ LINE ชอบอ่านเพี้ยน
    text = text.replace('%5D', '').replace(']', '')
    return text

def ask_gemini_to_summarize(raw_web_data):
    if not GEMINI_API_KEY:
        return "⚠️ ไม่ได้ตั้งค่า GEMINI_API_KEY ใน GitHub Secrets"
        
    model_name = 'gemini-2.5-flash'
    url = f"https://generativelanguage.googleapis.com/v1/models/{model_name}:generateContent?key={GEMINI_API_KEY}"
    
    # 🧠 บรีฟคุมเข้มรุ่นอัปเกรด: สั่งห้ามเติม / ปิดท้ายเลขบทความ และให้ใช้ 🔗 แทนวงเล็บ []
    prompt = f"""
    คุณคือนักข่าวสายบุญ ทำหน้าที่สรุปข้อมูลจาก DMC.tv ให้สั้น กระชับ น่าสนใจ และเปี่ยมด้วยบุญบันเทิง 
    (แต่ละข้อเขียนกระชับ 1-2 บรรทัดจบ เพื่อให้อ่านง่ายใน LINE)
    
    [กฎเหล็กเรื่องลิงก์และการห้ามเดา]
    - ห้ามคิด ลิงก์ ขึ้นมาเองเด็ดขาด! ลิงก์ที่นำมาใส่จะต้องเป็นลิงก์ที่อยู่ต่อท้าย "หัวข้อ" นั้นๆ ในข้อมูลดิบเป๊ะๆ 
    - ห้ามเติมเครื่องหมายสแลช (/) ปิดท้ายเลขไอดีบทความเด็ดขาด เช่น ให้ใช้ article/34425 ห้ามแก้เป็น article/34425/
    - ห้ามใช้เครื่องหมายวงเล็บสี่เหลี่ยม [] ล้อมรอบลิงก์เด็ดขาด ให้ใช้สัญลักษณ์ 🔗 นำหน้าลิงก์แบบปล่อยอิสระ เพื่อป้องกันแอป LINE อ่านลิงก์เพี้ยน
    - คัดเลือกเฉพาะกิจกรรมในเดือนนี้ (มิถุนายน 2569) และเดือนหน้าเท่านั้น

    ข้อมูลดิบจากหน้าเว็บ:
    \"\"\"{raw_web_data}\"\"\"

    เขียนสรุปส่งเข้า LINE ตามโครงสร้างนี้เท่านั้น (ห้ามมีคำเกริ่นนำของ AI):

    ✨ สรุปงานบุญดีเอ็มซีประจำวัน ✨

    🙏 [ธรรมะสอนใจ]
    • (ดึงโอวาทคุณครูไม่ใหญ่ คำสอนคุณยาย หรือหลวงปู่ สั้นๆ 1 ข้อคิดอ่านแล้วได้ปัญญา + 🔗 ที่มา: ลิงก์ที่ตรงกับหัวข้อธรรมะ)

    🧡 [โครงการบวช & อบรม]
    • (สรุปโครงการบวชหรืออบรมเยาวชนที่กำลังเปิดรับสมัครแบบย่นย่อ + 🔗 รายละเอียด: ลิงก์ของโครงการ)

    💰 [งานบุญเด่น & กิจกรรมเดือนนี้]
    • (เจาะจงค้นหาและเรียบเรียงงานบุญเชิญชวนสร้างบารมี เช่น ทอดผ้าป่า บูชาข้าวพระ ตอกเสาเข็ม หรือกิจกรรมสำคัญในเดือนมิถุนายน 2569 นี้มาให้ครบถ้วน สรุปสั้นๆ บอกวันจัดงานชัดเจน + 🔗 ร่วมบุญ: ลิงก์ของงานบุญนั้นๆ)

    💡 [คลังความรู้ที่น่าสนใจ]
    • (สรุปแก่นความรู้วันสำคัญ นิทรรศการ หรือสาระธรรมะให้อ่านเข้าใจทันที 1-2 ข้อ + 🔗 ความรู้: ลิงก์ที่ตรงกัน)

    🎉 [บันทึกภาพงานบุญชวนอนุโมทนา]
    • (สรุปงานบุญประมวลภาพที่เพิ่งผ่านพ้นไป เพื่อให้สาธุชนได้ร่วมอนุโมทนาย้อนหลัง 1-2 งาน + 🔗 รวมรูป: ลิงก์ของข่าวนั้น)
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
        print(f"📲 สถานะการส่ง LINE: {res.status_code}")
    except Exception as e:
        print(f"❌ ส่ง LINE ไม่สำเร็จ: {e}")

def main():
    print("🚀 บอทสายบุญอัจฉริยะ (เวอร์ชันแก้ทางเทคนิคเรื่องลิงก์บทความล่ม) เริ่มรัน...")
    
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
                    
                    # 🎯 ชั้นที่ 1: ตรวจสอบและตัด / ปิดท้ายลิงก์ที่เป็นเลขบทความตั้งแต่ตอนดึงข้อมูลดิบ
                    if "/article/" in h and h.endswith("/"):
                        h = h.rstrip("/")
                        
                    web_data_list.append(f"หัวข้อ: {t} | ลิงก์: {h}")
                    
            raw_web_data = "\n".join(web_data_list[:40])
            browser.close()
            
            print("🧠 ส่งต่อข้อมูลดิบเข้าสู่ระบบคัดกรองแก่นธรรม...")
            ai_report = ask_gemini_to_summarize(raw_web_data)
            
            # 🎯 ชั้นที่ 3: กรองล้างสีกแปลกปลอมรอบสุดท้ายก่อนยิงเข้า LINE ป้องกันภัยเงียบ Bad Gateway
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
