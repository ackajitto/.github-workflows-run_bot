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
    
    # 🧠 บรีฟแบบมินิมอล: เน้นเนื้อๆ กระชับ ได้ใจความ อ่านจบไวในหน้าจอเดียว
    prompt = f"""
    คุณคือนักข่าวสายบุญ ทำหน้าที่ย่อสรุปข้อมูลจาก DMC.tv ให้สั้น กระชับ มีเสน่ห์ ชวนอนุโมทนาบุญ 
    (เน้นเนื้อๆ ไม่ออกน้ำ แต่ละข้อห้ามเขียนยาวเกิน 2 บรรทัด)
    
    [กฎคัดกรอง]
    - เลือกเฉพาะกิจกรรมเดือนนี้ (มิถุนายน 2569) และเดือนหน้าเท่านั้น
    - ข้อมูล ลิงก์ และวันที่ ต้องตรงกับข้อมูลดิบ ห้ามเดา

    ข้อมูลดิบ:
    \"\"\"{raw_web_data}\"\"\"

    เขียนสรุปส่งเข้า LINE ตามโครงสร้างนี้เท่านั้น (ห้ามมีคำเกริ่นนำของ AI):

    ✨ สรุปงานบุญดีเอ็มซีประจำวัน ✨

    🙏 [ธรรมะสอนใจ]
    • (ดึงโอวาทคมๆ สั้นๆ มาเขียนให้อ่านจบใน 1 ประโยค [ที่มา: ลิงก์])

    🧡 [โครงการบวช]
    • (สรุปชื่อโครงการบวช/อบรมที่กำลังเปิดรับสมัครแบบกระชับ + [รายละเอียด: ลิงก์])

    💰 [กิจกรรมบุญเร็วๆ นี้]
    • (สรุปงานบุญทอดผ้าป่า/บูชาข้าวพระ/งานเด่นๆ 3-4 งาน สรุปสั้นๆ บอกวันที่ชัดเจน + [ร่วมบุญ: ลิงก์])

    💡 [คลังความรู้]
    • (ย่อแก่นความรู้ของวันสำคัญหรือนิทรรศการให้เข้าใจทันทีใน 1-2 บรรทัด ไม่ต้องกดลิงก์เพิ่ม + [ความรู้: ลิงก์])

    🎉 [ภาพงานบุญ]
    • (สรุปงานบุญที่เพิ่งผ่านไปสั้นๆ ชวนอนุโมทนาย้อนหลัง 1-2 งาน + [รวมรูป: ลิงก์])
    """
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    headers = {"Content-Type": "application/json"}
    
    # ระบบตื๊อ 3 รอบ เผื่อเจอจังหวะคนแน่นคิวสั้น
    for attempt in range(3):
        try:
            print(f"📡 ส่งข้อมูลฉบับมินิมอลไปที่รุ่น: {model_name} (รอบที่ {attempt + 1}/3)...")
            res = requests.post(url, headers=headers, json=payload, timeout=30)
            result_json = res.json()
            
            if res.status_code == 200 and 'candidates' in result_json:
                ai_response = result_json['candidates'][0]['content']['parts'][0]['text']
                print("🎉 ประมวลผลสำเร็จ!")
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
    print("🚀 บอทสายบุญมินิมอล (ฉบับโหลดไว อ่านง่าย) เริ่มรัน...")
    
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
                    
            # 🎯 [ปรับลด] คัดเลือกมาเพียง 25 รายการแรก ข้อมูลเบาสบาย ไม่ติดคิวแน่นอน
            raw_web_data = "\n".join(web_data_list[:25])
            browser.close()
            
            print("🧠 ส่งต่อข้อมูลดิบเข้าสู่ระบบคัดกรองแก่นธรรม...")
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
