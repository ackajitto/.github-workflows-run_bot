import os
import requests
from playwright.sync_api import sync_playwright

# --- ตั้งค่า URL และ API หลัก ---
TARGET_URL = "https://www.dmc.tv/home/"
LINE_API = "https://api.line.me/v2/bot/message/push"

LINE_TOKEN = os.environ.get("LINE_TOKEN")
LINE_TARGET_ID = os.environ.get("LINE_TARGET_ID")

def filter_and_format_merit_news(web_data_list):
    # 🎯 คีย์เวิร์ดคัดกรองงานบุญและโครงการช่วงเดือน มิ.ย. - ก.ค.
    merit_keywords = ['บุญ', 'ผ้าป่า', 'บวช', 'อุปสมบท', 'อบรม', 'บูชาข้าวพระ', 'หล่อพระ', 'เสาเข็ม', 'ปฏิบัติธรรม', 'มิ.ย.', 'ก.ค.', 'มิถุนายน', 'กรกฎาคม']
    
    merit_events = []
    ordination_events = []
    seen_titles = set()
    
    for title, href in web_data_list:
        title_lower = title.lower()
        
        # กรองเฉพาะหัวข้อที่มีคีย์เวิร์ดงานบุญ
        if any(kw in title_lower for kw in merit_keywords):
            if title in seen_titles:
                continue
            seen_titles.add(title)
            
            # 🧡 แยกเข้าหมวดโครงการบวช / อบรม
            if any(kw in title_lower for kw in ['บวช', 'อุปสมบท', 'อบรม', 'เยาวชน']):
                ordination_events.append(f"• {title}\n  [รายละเอียด: {href}]")
            # 💰 แยกเข้าหมวดงานบุญสร้างบารมีทั่วไป
            else:
                merit_events.append(f"• {title}\n  [ร่วมบุญ: {href}]")
                
    # คัดเลือกมาแสดงหมวดละ 4-5 รายการแรกที่สดใหม่ที่สุดเพื่อความกระชับ
    merit_text = "\n".join(merit_events[:5]) if merit_events else "• ติดตามข่าวสารงานบุญเพิ่มเติมได้ที่หน้าเว็บไซต์จ้ะ"
    ordination_text = "\n".join(ordination_events[:3]) if ordination_events else "• ติดตามโครงการบวชประจำปีได้ที่หน้าเว็บไซต์จ้ะ"
    
    # ประกอบร่างข้อความมินิมอลส่งเข้า LINE
    message = f"""✨ ปฏิทินงานบุญสร้างบารมี DMC (ระบบตรง ไม่ใช้ AI) ✨

💰 [ข่าวสารงานบุญเชิญชวนร่วมทำบุญ]
{merit_text}

🧡 [โครงการบวช & อบรมเยาวชน]
{ordination_text}

(ข้อมูลส่งตรงจากหน้าแรกเว็บ อ่านง่าย ลิงก์ตรงเป๊ะ 100% ครับจ้ะ)"""
    return message

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
    print("🚀 บอทสายบุญระบบตรง (เสถียรภาพสูงสุด 100%) เริ่มรัน...")
    
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
                # คัดกรองลิงก์ของ dmc ที่มีความยาวหัวข้อเหมาะสม
                if t and len(t) > 12 and h and h.startswith("http") and "dmc.tv" in h:
                    web_data_list.append((t, h))
                    
            browser.close()
            
            print("🧠 กำลังประมวลผลจัดหมวดหมู่ด้วยระบบรหัส...")
            final_report = filter_and_format_merit_news(web_data_list)
            
            print("\n=== ผลลัพธ์สุดท้าย ===")
            print(final_report)
            
            # ส่งตรงเข้า LINE ทันที
            send_line_message(final_report)

        except Exception as e:
            print(f"❌ ระบบภายนอกพังเนื่องจาก: {e}")
            if 'browser' in locals():
                browser.close()

if __name__ == "__main__":
    main()
