import os
import requests
from playwright.sync_api import sync_playwright
from google import genai
from google.genai import types

# --- ตั้งค่า URL และ API หลัก ---
TARGET_URL = "https://www.dmc.tv/home/"
LINE_API = "https://api.line.me/v2/bot/message/push"

LINE_TOKEN = os.environ.get("LINE_TOKEN")
LINE_TARGET_ID = os.environ.get("LINE_TARGET_ID")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

def ask_gemini_to_summarize(raw_web_data):
    if not GEMINI_API_KEY:
        return "⚠️ ไม่ได้ตั้งค่า GEMINI_API_KEY ใน GitHub Secrets"
        
    try:
        # ใช้เครื่องมือมาตรฐานของ Google ในการส่งข้อมูล ปลอดภัยและเสถียรที่สุด
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        # 🧠 บรีฟแบบให้เสรีภาพ AI เต็มที่ในการเรียบเรียงภาษาให้งดงามและเกิดประโยชน์สูงสุด
        prompt = f"""
        คุณคือนักข่าวสายบุญและบรรณาธิการอัจฉริยะ หน้าที่ของคุณคืออ่านข้อมูลตัวอักษรและลิงก์ดิบจากเว็บ DMC.tv
        แล้วนำมาคัดสรร เรียบเรียง และเขียนสรุปข่าวขึ้นมาใหม่ด้วยภาษาที่ไพเราะ สละสลวย นุ่มนวล ชวนให้อนุโมทนาบุญ 
        
        [กฎเหล็กในการคัดกรองเนื้อหา]
        1. ตรวจสอบวันเวลาให้ดี: คัดข้อมูลที่เป็นอดีตหรือปีเก่าๆ ทิ้งไป ให้เลือกเฉพาะกิจกรรมที่จะเกิดขึ้นในเดือนนี้ (มิถุนายน 2569) และเดือนหน้าเท่านั้น
        2. ห้ามคัดลอกข้อความดิบแหว่งๆ มาแปะดื้อๆ ให้ใช้อิสระในการเรียบเรียงประโยคขึ้นมาใหม่ให้อ่านง่าย มีที่มาที่ไป ชวนติดตาม และสรุปแง่คิดธรรมะออกมาให้ผู้อ่านเข้าใจได้ทันที
        3. ข้อมูลตัวเลข ลิงก์ และวันที่จัดงาน ห้ามแต่งแต่งเติมหรือเดาเด็ดขาด ต้องตรงกับข้อมูลดิบเป๊ะๆ

        ข้อมูลดิบจากหน้าเว็บ:
        \"\"\"{raw_web_data}\"\"\"

        จงเรียบเรียงข้อความเพื่อส่งเข้า LINE ตามโครงสร้างนี้เท่านั้น (ห้ามมีคำเกริ่นนำของ AI):

        ✨ สรุปข่าวสารและสาระงานบุญดีเอ็มซีประจำวัน ✨

        🙏 [ธรรมะสอนใจ สรุปจากโอวาทและคลังความรู้]
        • (รวมบทความธรรมะและโอวาทหลวงพ่อ มาร้อยเรียงใหม่เป็น "ข้อคิดสั้นๆ ประจำวัน" 1-2 ข้อคิด ที่อ่านแล้วได้ปัญญาทันที พร้อมแนบลิงก์อ่านต่อ)

        🧡 [ข่าวโครงการบวช & อบรมเยาวชน]
        • (เขียนแนะนำโครงการอบรมหรือบวชที่กำลังเปิดรับสมัคร ชี้ให้เห็นความน่าสนใจและประโยชน์ที่จะได้รับ พร้อมแนบลิงก์รายละเอียด)

        💰 [ข่าวสารงานบุญสร้างบารมี & กิจกรรมเร็วๆ นี้]
        • (เรียบเรียงข่าวเชิญชวนทอดผ้าป่า ตอกเสาเข็ม บูชาข้าวพระ กิจกรรม Big Cleaning โดยเขียนอธิบายให้เห็นภาพความสำคัญของบุญนั้นๆ และบอกวันที่จัดงานให้ชัดเจน จัดมา 4-6 งานบุญเด่นๆ พร้อมลิงก์ร่วมบุญ)

        💡 [หมวดธรรมะน่าสนใจ & คลังความรู้]
        • (สรุปความรู้หรือบทความวันสำคัญ เช่น วันเข้าพรรษา โดยสรุปเนื้อหาสั้นๆ ให้ได้ความรู้เลย พร้อมลิงก์)

        🎉 [บันทึกประมวลภาพงานบุญน่าอนุโมทนา]
        • (สรุปงานบุญเด่นๆ ที่เพิ่งจัดผ่านพ้นไป ยุบรวมเป็นก้อนเดียว ชวนให้ร่วมอนุโมทนาย้อนหลังอย่างมีความสุข ไม่เกิน 3 รายการ พร้อมแนบลิงก์รวมรูปภาพ)
        """
        
        # เรียกใช้งานผ่าน gemini-1.5-flash ในระบบโครงสร้างทางการ
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=prompt
        )
        return response.text.strip()
        
    except Exception as e:
        return f"❌ เกิดข้อผิดพลาดในการประมวลผลด้วย Google AI: {e}"

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
    print("🚀 บอทสายบุญระบบสมองกล (เวอร์ชันใช้ Library ทางการ) กำลังเตรียมการ...")
    
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
            
            print("🧠 กำลังส่งต่อข้อมูลให้ AI เรียบเรียงภาษาให้งดงาม...")
            final_report = ask_gemini_to_summarize(raw_web_data)
            
            print("\n=== ผลลัพธ์จาก AI ===")
            print(final_report)
            send_line_message(final_report)

        except Exception as e:
            print(f"❌ พังเนื่องจาก: {e}")
            if 'browser' in locals():
                browser.close()

if __name__ == "__main__":
    main()
