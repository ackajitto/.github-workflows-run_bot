import os
import time
import requests
from playwright.sync_api import sync_playwright

# --- ตั้งค่า URL และ API หลัก ---
TARGET_URL = "https://www.dmc.tv/home/"
LINE_API = "https://api.line.me/v2/bot/message/push"

LINE_TOKEN = os.environ.get("LINE_TOKEN")
LINE_TARGET_ID = os.environ.get("LINE_TARGET_ID")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

def ask_gemini_to_summarize(raw_web_data):
    if not GEMINI_API_KEY:
        return "⚠️ ไม่ได้ตั้งค่า GEMINI_API_KEY ใน GitHub Secrets"
        
    model_name = 'gemini-2.5-flash'
    url = f"https://generativelanguage.googleapis.com/v1/models/{model_name}:generateContent?key={GEMINI_API_KEY}"
    
    # 🧠 บรีฟย่นย่อเนื้อหาธรรมะและความรู้ให้จบใน LINE ตามที่คุณต้องการ
    prompt = f"""
    คุณคือนักข่าวสายบุญและบรรณาธิการอัจฉริยะ หน้าที่ของคุณคืออ่านข้อมูลตัวอักษรและลิงก์ดิบจากเว็บ DMC.tv
    แล้วนำมาคัดสรร เรียบเรียง และเขียนสรุปข่าวขึ้นมาใหม่ด้วยภาษาที่ไพเราะ สละสลวย นุ่มนวล ชวนให้อนุโมทนาบุญ 
    
    [กฎเหล็กในการคัดกรองเนื้อหา]
    1. ตรวจสอบวันเวลาให้ดี: คัดข้อมูลที่เป็นอดีตหรือปีเก่าๆ ทิ้งไป ให้เลือกเฉพาะกิจกรรมที่จะเกิดขึ้นในเดือนนี้ (มิถุนายน 2569) และเดือนหน้าเท่านั้น
    2. ห้ามคัดลอกข้อความดิบแหว่งๆ มาแปะดื้อๆ ให้ใช้อิสระในการเรียบเรียงประโยคขึ้นมาใหม่ให้อ่านง่าย มีที่มาที่ไป ชวนติดตาม
    3. ข้อมูลตัวเลข ลิงก์ และวันที่จัดงาน ห้ามแต่งแต่งเติมหรือเดาเด็ดขาด ต้องตรงกับข้อมูลดิบเป๊ะๆ

    ข้อมูลดิบจากหน้าเว็บ:
    \"\"\"{raw_web_data}\"\"\"

    จงเรียบเรียงข้อความเพื่อส่งเข้า LINE ตามโครงสร้างนี้เท่านั้น (ห้ามมีคำเกริ่นนำของ AI):

    ✨ สรุปข่าวสารและสาระงานบุญดีเอ็มซีประจำวัน ✨

    🙏 [ธรรมะสอนใจ ประจำวัน]
    • (จากข้อมูลดิบ ให้เจาะจงค้นหาโอวาทคุณครูไม่ใหญ่, คำสอนคุณยายอาจารย์ หรือหลวงปู่พระมงคลเทพมุนี แล้ว "ดึงเนื้อหาคำสอนหรือแง่คิดสั้นๆ คมๆ" ออกมาเขียนให้ผู้อ่านได้อ่านเนื้อหาธรรมะนั้นทันทีใน LINE 1-2 ข้อคิด โดยไม่ต้องกดลิงก์เข้าไปอ่านอีก แล้วตบท้ายด้วยการบอกที่มาสั้นๆ เช่น [ที่มา: โอวาทคุณครูไม่ใหญ่ - ลิงก์...])

    🧡 [ข่าวโครงการบวช & อบรมเยาวชน]
    • (เขียนแนะนำโครงการอบรมหรือบวชที่กำลังเปิดรับสมัคร ชี้ให้เห็นความน่าสนใจและประโยชน์ที่จะได้รับ พร้อมแนบลิงก์รายละเอียด)

    💰 [ข่าวสารงานบุญสร้างบารมี & กิจกรรมเร็วๆ นี้]
    • (เรียบเรียงข่าวเชิญชวนทอดผ้าป่า ตอกเสาเข็ม บูชาข้าวพระ กิจกรรม Big Cleaning โดยเขียนอธิบายให้เห็นภาพความสำคัญของบุญนั้นๆ และบอกวันที่จัดงานให้ชัดเจน จัดมา 4-6 งานบุญเด่นๆ พร้อมลิงก์ร่วมบุญ)

    💡 [หมวดธรรมะน่าสนใจ & คลังความรู้]
    • (จากข้อมูลคลังความรู้หรือวันสำคัญ ให้ทำการ "สรุปสาระสำคัญเนื้อๆ เน้นๆ" นำแก่นความรู้มาเขียนอธิบายย่นย่อให้อ่านแล้วเข้าใจ ได้ความรู้ประดับสติปัญญาทันทีใน LINE โดยไม่ต้องกดลิงก์ไปอ่านเพิ่มยาวๆ แล้วตบท้ายด้วยชื่อหัวข้อและลิงก์สั้นๆ เท่านั้น เช่น [คลังความรู้: วันเข้าพรรษาคืออะไร - ลิงก์...])

    🎉 [บันทึกประมวลภาพงานบุญน่าอนุโมทนา]
    • (สรุปงานบุญเด่นๆ ที่เพิ่งจัดผ่านพ้นไป ยุบรวมเป็นก้อนเดียว ชวนให้ร่วมอนุโมทนาย้อนหลังอย่างมีความสุข ไม่เกิน 3 รายการ พร้อมแนบลิงก์รวมรูปภาพ)
    """
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    headers = {"Content-Type": "application/json"}
    
    # 🔄 เพิ่มรอบตื๊อเป็น 5 รอบ และใช้สูตรขยับเวลาหนีรถติด (15, 30, 45, 60 วินาที)
    for attempt in range(5):
        try:
            print(f"📡 กำลังส่งข้อมูลก้อนกระชับไปที่รุ่น: {model_name} (รอบที่ {attempt + 1}/5)...")
            res = requests.post(url, headers=headers, json=payload, timeout=30)
            result_json = res.json()
            
            if res.status_code == 200 and 'candidates' in result_json:
                ai_response = result_json['candidates'][0]['content']['parts'][0]['text']
                print(f"🎉 สำเร็จแล้วในรอบที่ {attempt + 1}!")
                return ai_response.strip()
                
            elif res.status_code in [503, 429]:
                wait_time = (attempt + 1) * 15  # เพิ่มเวลาพักรอรอบถัดไปเรื่อยๆ เพื่อหลบช่วงคนแน่น
                print(f"⏳ เจอสถานะ {res.status_code} คนแน่นคิวเต็ม ขอเว้นระยะ {wait_time} วินาทีแล้วลองใหม่...")
                time.sleep(wait_time)
                continue
            else:
                print(f"❌ ปฏิเสธการทำงาน รหัส: {res.status_code} | ข้อความ: {result_json}")
                break
        except Exception as e:
            print(f"⚠️ เกิดข้อผิดพลาดทางเทคนิค: {e}")
            time.sleep(10)
            
    return "❌ บอทกูเกิลติดขัดเนื่องจากคนใช้งานหนาแน่นมากเกินไปจริงๆ โปรดกดรันใหม่อีกครั้งในภายหลังครับจ้ะ"

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
    print("🚀 บอทสายบุญอัจฉริยะ (เวอร์ชัน Diet ข้อมูล + เพิ่มพลังตื๊อ 5 รอบ) เริ่มรัน...")
    
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
                    
            # 🎯 [จุดสำคัญ] ลดขนาดข้อมูลเหลือ 50 รายการแรก เพื่อให้ประมวลผลง่าย คิวผ่านฉลุย
            raw_web_data = "\n".join(web_data_list[:50])
            browser.close()
            
            print("🧠 ส่งต่อข้อมูลดิบเข้าสู่ระบบคัดกรองแก่นธรรม...")
            final_report = ask_gemini_to_summarize(raw_web_data)
            
            print("\n=== ผลลัพธ์สุดท้าย ===")
            print(final_report)
            
            # ยิงผลลัพธ์เข้า LINE
            send_line_message(final_report)

        except Exception as e:
            print(f"❌ ระบบภายนอกพังเนื่องจาก: {e}")
            if 'browser' in locals():
                browser.close()

if __name__ == "__main__":
    main()
