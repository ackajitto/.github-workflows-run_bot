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
    
    # 🧠 บรีฟระดับไฮเปอร์โฟกัส: เจาะจงเฉพาะงานบุญอนาคตในเดือนนี้และเดือนหน้าเท่านั้น
    prompt = f"""
    คุณคือนักข่าวสายบุญ หน้าที่หลักคือ "คัดสรรและเรียบเรียงข่าวสารงานบุญที่จะเกิดขึ้นในเดือนนี้ (มิถุนายน 2569) และเดือนหน้า (กรกฎาคม 2569)" จากข้อมูลเว็บ DMC.tv
    เรียบเรียงให้ออกมาสั้น กระชับ ได้ใจความชวนเชิญชวนร่วมสร้างบารมี (แต่ละข้อห้ามยาวเกิน 2 บรรทัด)
    
    [กฎเหล็กเรื่องลิงก์และความแม่นยำ]
    1. ห้ามคิด ลิงก์ ขึ้นมาเองเด็ดขาด! ลิงก์ในวงเล็บต้องเป็นลิงก์ที่อยู่ต่อท้าย "หัวข้อ" นั้นๆ ในข้อมูลดิบเป๊ะๆ 
    2. คัดเลือกเฉพาะกิจกรรมทำบุญสร้างบารมีที่กำลังจะเกิดขึ้น (เช่น ทอดผ้าป่า, บูชาข้าวพระ, หล่อพระ, ตอกเสาเข็ม, บุญวันอาทิตย์)

    ข้อมูลดิบจากหน้าเว็บ:
    \"\"\"{raw_web_data}\"\"\"

    เขียนสรุปส่งเข้า LINE ตามโครงสร้างนี้เท่านั้น (ห้ามมีคำเกริ่นนำหรือคำสรุปของ AI):

    ✨ ปฏิทินข่าวสารงานบุญสร้างบารมี DMC ✨

    💰 [ข่าวสารงานบุญเชิญชวนร่วมทำบุญ (มิ.ย. - ก.ค. 69)]
    • (ค้นหาและสรุปงานบุญที่จะจัดขึ้น คัดเด่นๆ มา 4-6 งาน บอกชื่อบุญ วันเวลาจัดงานให้สั้นและชัดเจนที่สุด + [ร่วมบุญ: ลิงก์ตรงจากข้อมูลดิบ])

    🙏 [โอวาทธรรมนำทางใจประจำวัน]
    • (ดึงข้อคิดหรือโอวาทสั้นๆ คมๆ จากข้อมูลดิบมา 1 ข้อคิด สำหรับสร้างกำลังใจ + [ที่มา: ลิงก์ตรง])

    🧡 [โครงการบวชเข้าพรรษา]
    • (สรุปโครงการบวชหรืออบรมเยาวชนช่วงเข้าพรรษาที่กำลังเปิดรับสมัครแบบย่อที่สุด 1 ข้อ + [รายละเอียด: ลิงก์ตรง])
    """
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    headers = {"Content-Type": "application/json"}
    
    for attempt in range(3):
        try:
            print(f"📡 ส่งข้อมูลไฮเปอร์โฟกัสไปที่รุ่น: {model_name} (รอบที่ {attempt + 1}/3)...")
            res = requests.post(url, headers=headers, json=payload, timeout=30)
            result_json = res.json()
            
            if res.status_code == 200 and 'candidates' in result_json:
                ai_response = result_json['candidates'][0]['content']['parts'][0]['text']
                print("🎉 AI เรียบเรียงงานบุญอนาคตสำเร็จ!")
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
    print("🚀 บอทสายบุญไฮเปอร์โฟกัส (เน้นเฉพาะงานบุญที่จะถึงนี้) เริ่มรัน...")
    
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
                    
            # คัดเลือกมา 50 รายการแรก เพื่อให้ครอบคลุมงานบุญบนหน้าแรกทั้งหมด ดาต้ากำลังเพรียวลม
            raw_web_data = "\n".join(web_data_list[:50])
            browser.close()
            
            print("🧠 ส่งต่อข้อมูลดิบเข้าสู่ระบบคัดกรองปฏิทินงานบุญ...")
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
