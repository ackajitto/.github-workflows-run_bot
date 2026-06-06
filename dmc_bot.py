import os
import requests
from playwright.sync_api import sync_playwright

# --- ตั้งค่า URL และ API ---
TARGET_URL = "https://www.dmc.tv/home/"
LINE_API = "https://api.line.me/v2/bot/message/push"
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

LINE_TOKEN = os.environ.get("LINE_TOKEN")
LINE_TARGET_ID = os.environ.get("LINE_TARGET_ID")

def ask_gemini_to_summarize(raw_web_data):
    if not GEMINI_API_KEY:
        return "⚠️ ไม่ได้ตั้งค่า GEMINI_API_KEY ใน GitHub Secrets"
        
    # 🎯 แก้ไข URL ให้ตรงตามมาตรฐานของ Google AI Studio เปรี้ยงเดียวหายพังครับ
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    # 🧠 บรีฟแบบให้เสรีภาพ AI ในการเรียบเรียงคำสอนและสรุปภาษาพูดให้สละสลวย
    prompt = f"""
    คุณคือนักข่าวสายบุญและบรรณาธิการอัจฉริยะ หน้าที่ของคุณคืออ่านข้อมูลตัวอักษรและลิงก์ดิบจากเว็บ DMC.tv
    แล้วนำมาคัดสรร เรียบเรียง และเขียนข่าวขึ้นมาใหม่ด้วยภาษาที่ไพเราะ สละสลวย นุ่มนวล ชวนให้อนุโมทนาบุญ 
    
    [กฎเหล็กในการคัดกรองเนื้อหา]
    1. ตรวจสอบวันเวลาให้ดี: คัดข้อมูลที่เป็นอดีตหรือปีเก่าๆ ทิ้งไป ให้เลือกเฉพาะกิจกรรมที่จะเกิดขึ้นในเดือนนี้ (มิถุนายน 2569) และเดือนหน้าเท่านั้น
    2. ห้ามคัดลอกข้อความแหว่งๆ มาแปะดื้อๆ ให้ใช้อิสระในการเรียบเรียงประโยคขึ้นมาใหม่ให้อ่านง่าย มีที่มาที่ไป ชวนติดตาม
    3. ข้อมูลตัวเลข ลิงก์ และวันที่จัดงาน ห้ามแต่งแต่งเติมหรือเดาเด็ดขาด ต้องตรงกับข้อมูลดิบเป๊ะๆ

    ข้อมูลดิบจากหน้าเว็บ:
    \"\"\"{raw_web_data}\"\"\"

    จงเรียบเรียงข้อความเพื่อส่งเข้า LINE ตามโครงสร้างนี้เท่านั้น (ห้ามมีคำเกริ่นนำของ AI):

    ✨ สรุปข่าวสารและสาระงานบุญดีเอ็มซีประจำวัน ✨

    🙏 [ธรรมะสอนใจ สรุปจากโอวาทและคลังความรู้]
    • (รวมบทความธรรมะและโอวาทหลวงพ่อ มาร้อยเรียงใหม่เป็น "ข้อคิดสั้นๆ ประจำวัน" 1-2 ข้อคิด ที่อ่านแล้วได้ปัญญา ทันที พร้อมแนบลิงก์อ่านต่อ)

    🧡 [ข่าวโครงการบวช & อบรมเยาวชน]
    • (เขียนแนะนำโครงการอบรมหรือบวชที่กำลังเปิดรับสมัคร ชี้ให้เห็นความน่าสนใจและประโยชน์ที่จะได้รับ พร้อมแนบลิงก์รายละเอียด)

    💰 [ข่าวสารงานบุญสร้างบารมี & กิจกรรมเร็วๆ นี้]
    • (เรียบเรียงข่าวเชิญชวนทอดผ้าป่า ตอกเสาเข็ม บูชาข้าวพระ กิจกรรม Big Cleaning โดยเขียนอธิบายให้เห็นภาพความสำคัญของบุญนั้นๆ และบอกวันที่จัดงานให้ชัดเจน จัดมา 4-6 งานบุญเด่นๆ พร้อมลิงก์ร่วมบุญ)

    💡 [หมวดธรรมะน่าสนใจ & คลังความรู้]
    • (สรุปความรู้หรือบทความวันสำคัญ เช่น วันเข้าพรรษา โดยสรุปเนื้อหาสั้นๆ ให้ได้ความรู้เลย พร้อมลิงก์)

    🎉 [บันทึกประมวลภาพงานบุญน่าอนุโมทนา]
    • (สรุปงานบุญเด่นๆ ที่เพิ่งจัดผ่านพ้นไป ยุบรวมเป็นก้อนเดียว ชวนให้ร่วมอนุโมทนาย้อนหลังอย่างมีความสุข ไม่เกิน 3 รายการ พร้อมแนบลิงก์รวมรูปภาพ)
    """
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ]
    }
    
    headers = {"Content-Type": "application/json"}
    
    try:
        res = requests.post(url, headers=headers, json=payload)
        result_json = res.json()
        
        if 'error' in result_json:
            return f"❌ Google AI แจ้งข้อผิดพลาด: {result_json['error']['message']}"
            
        ai_response = result_json['candidates'][0]['content']['parts'][0]['text']
        return ai_response.strip()
    except Exception as e:
        return f"❌ ระบบขัดข้องขณะประมวลผล AI: {e}\nResponse ดิบ: {res.text[:200]}"

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
        print(f"📲 Status LINE: {res.status_code}")
    except Exception as e:
        print(f"❌ ส่ง LINE ไม่สำเร็จ: {e}")

def main():
    print("🚀 บอทสายบุญ AI (ฉบับอัปเดต URL โมเดล) กำลังรัน...")
    
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
                    web_data_list.append(f"หัวข้อ: {t} | ลิงก์รายละเอียด: {h}")
                    
            raw_web_data = "\n".join(web_data_list[:150])
            browser.close()
            
            print("🧠 ส่งต่อข้อมูลให้ AI เรียบเรียงแบบสละสลวย...")
            final_report = ask_gemini_to_summarize(raw_web_data)
            
            print("\n=== ผลลัพธ์จากการเรียบเรียง ===")
            print(final_report)
            send_line_message(final_report)

        except Exception as e:
            print(f"❌ พังเนื่องจาก: {e}")
            if 'browser' in locals():
                browser.close()

if __name__ == "__main__":
    main()
