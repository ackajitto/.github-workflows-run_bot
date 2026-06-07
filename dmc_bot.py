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
        
    # 🧠 บรีฟแบบมินิมอลขั้นสุด: คัดเน้นๆ เฉพาะหัวข้องานบุญอนาคตเดือนนี้และเดือนหน้า
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
    
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    headers = {"Content-Type": "application/json"}
    
    # 🎯 แผนจัดทัพท่อส่งและโมเดลแบบยืดหยุ่นสูง (ท่อ v1 และ v1beta)
    api_configs = [
        {"version": "v1beta", "model": "gemini-2.5-flash"}, # ท่อสำรอง v1beta รุ่นใหม่ (เสถียรสุดตอนนี้)
        {"version": "v1beta", "model": "gemini-1.5-flash"}, # ท่อสำรอง v1beta รุ่นพี่ใหญ่จอมอึด
        {"version": "v1", "model": "gemini-2.5-flash"}       # ท่อหลัก v1 รุ่นใหม่
    ]
    
    for config in api_configs:
        version = config["version"]
        model = config["model"]
        url = f"https://generativelanguage.googleapis.com/{version}/models/{model}:generateContent?key={GEMINI_API_KEY}"
        
        for attempt in range(2):  # ลองตื๊อเบิ้ล 2 รอบต่อหนึ่งโครงข่าย
            try:
                print(f"📡 กำลังเจาะท่อ {version} ใช้รุ่น: {model} (รอบที่ {attempt + 1}/2)...")
                res = requests.post(url, headers=headers, json=payload, timeout=30)
                result_json = res.json()
                
                if res.status_code == 200 and 'candidates' in result_json:
                    ai_response = result_json['candidates'][0]['content']['parts'][0]['text']
                    print(f"🎉 เจาะทะลวงสำเร็จด้วยท่อ {version} รุ่น {model}!")
                    return ai_response.strip()
                    
                elif res.status_code in [503, 429]:
                    print(f"⏳ ท่อติดขัดชั่วคราว (รหัส {res.status_code}) ขอพักหนีไฟวอลล์ 15 วินาที...")
                    time.sleep(15)
                    continue
                else:
                    print(f"⏩ ข้ามไปแผนสำรองถัดไป (เจอข้อความ: {result_json.get('error', {}).get('message', 'Unknown')})")
                    break
            except Exception as e:
                print(f"⚠️ เครือข่ายแกว่ง: {e}")
                time.sleep(5)
                
    return "❌ พญามารปิดกั้นทุกท่อส่งชั่วคราว โปรดกดรันใหม่อีกครั้งในภายหลังครับจ้ะ"

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
    print("🚀 บอทสายบุญมินิมอล (เวอร์ชันท่อส่งคู่ v1 + v1beta) เริ่มรัน...")
    
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
                    web_data_list.append(f"หัวข้อ: {t} -> ลิงก์: {h}")
                    
            # คัดมาแค่ 30 หัวข้อแรกหน้าเว็บ ข้อมูลเบาหวิวผ่านด่านตรวจง่ายแน่นอน
            raw_web_data = "\n".join(web_data_list[:30])
            browser.close()
            
            print("🧠 ส่งต่อหัวข้อข่าวเข้าสู่ระบบสับเปลี่ยนท่ออัจฉริยะ...")
            final_report = ask_gemini_to_summarize(raw_web_data)
            
            print("\n=== ผลลัพธ์สุดท้าย ===")
            print(final_report)
            
            send_line_message(final_report)

        except Exception as e:
            print(f"❌ ระบบภายนอกพังเนื่องจาก: {e}")
            if 'browser' in locals():
                browser.close()

if __name__ == "__main__":
    main()
