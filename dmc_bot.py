import os
import requests
from playwright.sync_api import sync_playwright
from google import genai

# --- ตั้งค่า URL และ API หลัก ---
TARGET_URL = "https://www.dmc.tv/home/"
LINE_API = "https://api.line.me/v2/bot/message/push"

LINE_TOKEN = os.environ.get("LINE_TOKEN")
LINE_TARGET_ID = os.environ.get("LINE_TARGET_ID")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

def ask_gemini_to_summarize(raw_web_data):
    if not GEMINI_API_KEY:
        return "⚠️ ไม่ได้ตั้งค่า GEMINI_API_KEY ใน GitHub Secrets"
        
    models_to_try = [
        'gemini-2.5-flash', 
        'gemini-2.0-flash', 
        'gemini-1.5-flash-latest',
        'gemini-1.5-flash'
    ]
    
    # 🧠 ปรับปรุงบรีฟ: ย่นย่อเนื้อหาความรู้ให้จบใน LINE ไม่ทิ้งลิงก์รกตา
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
    • (จากข้อมูลคลังความรู้หรือวันสำคัญ เช่น วันเข้าพรรษา/นิทรรศการ ให้ทำการ "สรุปสาระสำคัญเนื้อๆ เน้นๆ" นำแก่นความรู้มาเขียนอธิบายย่นย่อให้อ่านแล้วเข้าใจ ได้ความรู้ประดับสติปัญญาทันทีใน LINE โดยไม่ต้องกดลิงก์ไปอ่านเพิ่มยาวๆ แล้วตบท้ายด้วยชื่อหัวข้อและลิงก์สั้นๆ เท่านั้น เช่น [คลังความรู้: วันเข้าพรรษาคืออะไร - ลิงก์...])

    🎉 [บันทึกประมวลภาพงานบุญน่าอนุโมทนา]
    • (สรุปงานบุญเด่นๆ ที่เพิ่งจัดผ่านพ้นไป ยุบรวมเป็นก้อนเดียว ชวนให้ร่วมอนุโมทนาย้อนหลังอย่างมีความสุข ไม่เกิน 3 รายการ พร้อมแนบลิงก์รวมรูปภาพ)
    """
    
    client = genai.Client(api_key=GEMINI_API_KEY)
    last_error = ""
    
    for model_name in models_to_try:
        try:
            print(f"🤖 กำลังทดลองเชื่อมต่อด้วยโมเดล: {model_name}...")
            response = client.models.generate_content(
                model=model_name,
                contents=prompt
            )
            print(f"✅ เชื่อมต่อสำเร็จ! ระบบเลือกใช้รุ่น: {model_name}")
            return response.text.strip()
        except Exception as e:
            last_error = str(e)
            print(f"⚠️ รุ่น {model_name} ไม่ตอบรับ (ระบบกำลังข้ามไปลองรุ่นถัดไป...)")
            continue
            
    return f"❌ ทดลองเชื่อมต่อครบทุกโมเดลแล้วแต่ยังเข้าไม่ได้ ข้อผิดพลาดล่าสุด: {last_error}"

def send_line_message(msg):
    if not LINE_TOKEN or not LINE_TARGET_ID:
        print("⚠️ ไม่ได้ตั้งค่า LINE ให้ถูกต้อง")
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
    print("🚀 บอทสายบุญระบบสมองกล (เวอร์ชันย่นย่อความรู้คลังธรรม) กำลังเริ่มงาน...")
    
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
                    
            raw_web_data = "\n".join(web_data_list[:150])
            browser.close()
            
            print("🧠 ส่งต่อข้อมูลให้ AI เรียบเรียงสรุปแก่นธรรม...")
            final_report = ask_gemini_to_summarize(raw_web_data)
            
            print("\n=== ผลลัพธ์จากบอท ===")
            print(final_report)
            send_line_message(final_report)

        except Exception as e:
            print(f"❌ ระบบภายนอกพังเนื่องจาก: {e}")
            if 'browser' in locals():
                browser.close()

if __name__ == "__main__":
    main()
