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
    """ส่งข้อมูลเว็บดิบทั้งหมดไปให้ AI ของ Google ช่วยคัดกรองและเรียบเรียง"""
    if not GEMINI_API_KEY:
        return "⚠️ ไม่ได้ตั้งค่า GEMINI_API_KEY ใน GitHub Secrets ระบบจึงใช้ AI เรียบเรียงไม่ได้"
        
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    # 🎯 บรีฟคำสั่งภาษาไทย สั่งให้ AI จัดหมวดหมู่ตามที่คุณต้องการเป๊ะๆ
    prompt = f"""
    คุณคือนักข่าวสายบุญอัจฉริยะ หน้าที่ของคุณคืออ่านข้อมูลตัวอักษรดิบที่ได้จากการกวาดหน้าแรกของเว็บ DMC.tv 
    แล้วนำมาคัดสรร เรียบเรียงใหม่ให้ได้ประโยชน์สูงสุดตามหมวดหมู่ด้านล่างนี้ โดยมีเงื่อนไขสำคัญคือ:
    1. ห้ามเอาข้อมูลเก่าปีอื่นๆ (เช่น ปี 2567, 2568 หรือเดือนก่อนหน้า) คัดออกไปให้หมด เอาเฉพาะข้อมูลที่เป็นของเดือนปัจจุบัน (มิถุนายน 2569) และเดือนหน้า (กรกฎาคม 2569) เท่านั้น
    2. หมวดโอวาทและหมวดธรรมะน่าสนใจ ให้เรียบเรียงเนื้อหาสรุปย่อมาเป็นประโยคคำสอนสั้นๆ อ่านเข้าใจง่ายทันที ไม่เอาแค่ชื่อลิงก์แหว่งๆ
    3. หมวดทบทวนบุญ ให้ยุบรวมเป็นก้อนเดียว ไม่แยกในประเทศ/ต่างประเทศ คัดมาเฉพาะที่เด่นๆ น่าสนใจพอ

    ข้อมูลดิบจากหน้าเว็บ:
    \"\"\"{raw_web_data[:20000]}\"\"\"

    จงตอบกลับมาในรูปแบบข้อความเพื่อส่งเข้า LINE ตามโครงสร้างนี้เท่านั้น (ห้ามมีคำเกริ่นนำของ AI):

    ✨ สรุปข่าวสารงานบุญดีเอ็มซีประจำวัน ✨

    🙏 [โอวาทสั้นๆ จากหลวงพ่อธัมมชโย]
    • (เขียนสรุปเนื้อหาคำสอนสั้นๆ 2-3 บรรทัดให้อ่านแล้วได้แง่คิดทันที)
    🔗 อ่านธรรมะต่อที่: (ใส่ลิงก์ที่เกี่ยวข้องจากข้อมูลด้านบน ถ้าไม่มีให้ใส่เว็บหลัก dmc.tv)

    🧡 [ข่าวงานบวช & โครงการอบรม]
    • (รายชื่อโครงการบวชหรืออบรมที่อยู่ในช่วง มิ.ย. - ก.ค. 2569 พร้อมลิงก์)

    💰 [งานบุญเชิญชวน & กิจกรรมเร็วๆ นี้]
    • (รวมข่าวชวนทำบุญ ทอดผ้าป่า และกิจกรรมกำหนดการต่างๆ ที่กำลังจะเกิดขึ้น ปล่อยเนื้อหาได้เยอะจุใจ 5-8 รายการ พร้อมลิงก์)

    💡 [หมวดธรรมะน่าสนใจ & คลังความรู้]
    • (สรุปความรู้หรือบทความวันสำคัญ เช่น วันเข้าพรรษา โดยสรุปเนื้อหาสั้นๆ ให้ได้ความรู้เลย พร้อมลิงก์)

    🎉 [ทบทวนบุญเด่นน่าอนุโมทนาย้อนหลัง]
    • (สรุปงานบุญที่จัดผ่านไปแล้วรวมๆ กันแบบน่าสนใจ ไม่เกิน 3 รายการ พร้อมลิงก์)
    """
    
    headers = {"Content-Type": "application/json"}
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    try:
        res = requests.post(url, headers=headers, json=payload)
        result_json = res.json()
        ai_response = result_json['candidates'][0]['content']['parts'][0]['text']
        return ai_response.strip()
    except Exception as e:
        return f"❌ เกิดข้อผิดพลาดในการเชื่อมต่อ AI: {e}"

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
    print("🚀 บอทสายบุญระบบสมองกล AI กำลังเดินทางไปที่ dmc.tv...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            page.goto(TARGET_URL, timeout=30000)
            page.wait_for_load_state("networkidle")
            
            # กวาดตัวอักษรและลิงก์ทั้งหมดบนหน้าแรกมารวมกันเป็นเนื้อความดิบก้อนเดียว
            links = page.locator('a').all()
            web_data_list = []
            for link in links:
                t = link.inner_text().strip()
                h = link.get_attribute("href")
                if t and h and h.startswith("http"):
                    web_data_list.append(f"Content: {t} | Link: {h}")
                    
            raw_web_data = "\n".join(web_data_list)
            browser.close()
            
            # ส่งเนื้อหาทั้งหมดให้ AI สรุปตามบรีฟ
            print("🧠 กำลังส่งข้อมูลให้ AI ประมวลผลและคัดกรองวันเวลา...")
            final_report = ask_gemini_to_summarize(raw_web_data)
            
            # ส่งเข้า LINE
            print("\n=== ผลลัพธ์จาก AI ===")
            print(final_report)
            send_line_message(final_report)

        except Exception as e:
            print(f"❌ พังเนื่องจาก: {e}")
            if 'browser' in locals():
                browser.close()

if __name__ == "__main__":
    main()
