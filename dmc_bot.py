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
    
    # 🧠 บรีฟคัดเฉพาะหัวขื้องานบุญอนาคต (มิ.ย. - ก.ค. 2569) กระชับขั้นสุด
    prompt = f"""
    คุณคือผู้ช่วยสรุปงานบุญ หน้าที่ของคุณคือคัดเลือกหัวข้อข่าวสารงานบุญที่จะเกิดขึ้นในเดือนนี้ (มิถุนายน 2569) และเดือนหน้า (กรกฎาคม 2569) จากรายชื่อหัวข้อที่กำหนดให้
    และจัดหมวดหมู่ให้ออกมาเป็นข้อความสั้นๆ กระชับ ได้ใจความชวนอนุโมทนาบุญ (แต่ละข้อห้ามเกิน 1-2 บรรทัด)
    
    [กฎเหล็กเรื่องลิงก์]
    - ห้ามเดาหรือคิดลิงก์ขึ้นมาเองเด็ดขาด ต้องใช้ลิงก์ที่ระบุอยู่ท้ายหัวข้อนั้นๆ ในข้อมูลดิบเท่านั้น

    ข้อมูลหัวข้อดิบจากหน้าเว็บ:
    \"\"\"{raw_web_data}\"\"\"

    เขียนสรุปส่งเข้า LINE ตามโครงสร้างนี้เท่านั้น (ห้ามมีคำเกริ่นนำหรือสรุปท้ายของ AI):

    ✨ ปฏิทินงานบุญสร้างบารมี DMC ✨

    💰 [ข่าวสารงานบุญเชิญชวนร่วมทำบุญ (มิ.ย. - ก.ค. 69)]
    • (คัดเลือกหัวข้อข่าวเชิญชวนทำบุญ ทอดผ้าป่า บูชาข้าวพระ หล่อพระ กิจกรรมที่จะถึงนี้ มา 3-5 งาน สรุปชื่อบุญและวันเวลาสั้นที่สุด + [ร่วมบุญ: ลิงก์ตรง])

    🙏 [โอวาทธรรมนำทางใจ]
    • (หากมีหัวข้อโอวาทหรือธรรมะ ให้สรุปข้อคิดสั้นๆ คมๆ 1 ข้อคิด + [ที่มา: ลิงก์ตรง])

    🧡 [โครงการบวชเข้าพรรษา]
    • (หากมีหัวข้อโครงการบวชหรืออบรมช่วงเข้าพรรษา สรุปสั้นๆ 1 ข้อ + [รายละเอียด: ลิงก์ตรง])
    """
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    headers = {"Content-Type": "application/json"}
    
    # ระบบตื๊อ 3 รอบ เผื่อเจอจังหวะคนแน่นคิวสั้น
    for attempt in range(3):
        try:
            print(f"📡 ส่งข้อมูลเฉพาะหัวข้อไปที่รุ่น: {model_name} (รอบที่ {attempt + 1}/3)...")
            res = requests.post(url, headers=headers, json=payload, timeout=30)
            result_json = res.json()
            
            if res.status_code == 200 and 'candidates' in result_json:
                ai_response = result_json['candidates'][0]['content']['parts'][0]['text']
                print("🎉 AI สรุปหัวข้อข่าวสารงานบุญสำเร็จ!")
                return ai_response.strip()
                
            elif res.status_code in [503, 429]:
                print(f"⏳ คิวแน่นชั่วคราว รอ 10 วินาที...")
                time.sleep(10)
                continue
            else:
                print(f"❌ ปฏิเสธด้วยรหัส: {res.status_code}")
                break
        except Exception as e:
            print(f"⚠️ ข้อผิดพลาดเทคนิค: {e}")
            time.sleep(5)
            
    return "❌ บอทกูเกิลติดขัดชั่วคราว โปรดรันใหม่อีกครั้งในภายหลังครับจ้ะ"

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
    print("🚀 บอทสายบุญเน้นหัวข้อ (มินิมอลดาต้า) เริ่มรัน...")
    
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
                    # เก็บรวบรวมในรูปแบบที่กระชับที่สุดเพื่อเซฟเนื้อที่ข้อมูล
                    web_data_list.append(f"หัวข้อ: {t} -> ลิงก์: {h}")
                    
            # 🎯 คัดเฉพาะหัวข้อยอดนิยม 35 อันดับแรกหน้าเว็บ ดาต้าเบาหวิวเหมือนปุยเมฆ
            raw_web_data = "\n".join(web_data_list[:35])
            browser.close()
            
            print("🧠 ส่งต่อหัวข้อข่าวเข้าสู่ระบบประมวลผล...")
            final_report = ask_gemini_to_summarize(raw_web_data)
            
            print("\n=== ผลลัพธ์สุดท้าย ===")
            print(final_report)
            
            # ส่งเข้า LINE 
            send_line_message(final_report)

        except Exception as e:
            print(f"❌ ระบบภายนอกพังเนื่องจาก: {e}")
            if 'browser' in locals():
                browser.close()

if __name__ == "__main__":
    main()
