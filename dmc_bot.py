import os
import requests
from playwright.sync_api import sync_playwright

# --- ตั้งค่า URL และ API หลัก ---
TARGET_URL = "https://www.dmc.tv/home/"
LINE_API = "https://api.line.me/v2/bot/message/push"

LINE_TOKEN = os.environ.get("LINE_TOKEN")
LINE_TARGET_ID = os.environ.get("LINE_TARGET_ID")

def filter_and_format_merit_news(web_data_list):
    # 🟢 คีย์เวิร์ดเฉพาะงานบุญอนาคต / การเชิญชวนร่วมบุญ / โครงการเปิดรับสมัคร
    merit_keywords = ['ผ้าป่า', 'บูชาข้าวพระ', 'หล่อพระ', 'ตอกเสาเข็ม', 'สร้างเจดีย์', 'เจ้าภาพ', 'ขอเชิญ', 'เชิญชวน']
    study_keywords = ['บรรพชา', 'อุปสมบท', 'อบรม', 'รับสมัคร']
    
    # 🔴 คีย์เวิร์ดต้องห้าม (คัดทิ้งทันที: ข่าวอดีตที่ทำเสร็จแล้ว, สื่อบันเทิง, พิธีมอบรางวัล)
    banned_keywords = ['mv', 'official', 'เพลง', 'เกียรติบัตร', 'ประมวลภาพ', 'ภาพงานบุญ', 'ถวายแล้ว', 'ผ่านพ้น', 'ภาพข่าว']
    
    merit_events = []
    ordination_events = []
    seen_titles = set()
    
    for title, href in web_data_list:
        # ล้างเศษเว้นวรรคและการขึ้นบรรทัดใหม่แปลกๆ จากหน้าเว็บให้เรียบเนียน
        clean_title = " ".join(title.split())
        title_lower = clean_title.lower()
        
        # 1. ด่านแรก: ถ้ามีคำต้องห้าม ให้โยนทิ้งทันที
        if any(b_kw in title_lower for b_kw in banned_keywords):
            continue
            
        if clean_title in seen_titles:
            continue
            
        # 2. ด่านสอง: คัดกรองเข้าหมวดหมู่เฉพาะงานบุญที่ใช่จริงๆ
        if any(kw in title_lower for kw in study_keywords):
            seen_titles.add(clean_title)
            ordination_events.append(f"• {clean_title}\n  [รายละเอียด: {href}]")
        elif any(kw in title_lower for kw in merit_keywords):
            seen_titles.add(clean_title)
            merit_events.append(f"• {clean_title}\n  [ร่วมบุญ: {href}]")
                
    # เลือกแสดงเฉพาะตัวเด่นๆ หมวดละ 4-5 รายการเพื่อความกระชับ
    merit_text = "\n".join(merit_events[:5]) if merit_events else "• ติดตามข่าวสารงานบุญเพิ่มเติมได้ที่หน้าเว็บไซต์จ้ะ"
    ordination_text = "\n".join(ordination_events[:3]) if ordination_events else "• ติดตามโครงการบวชประจำปีได้ที่หน้าเว็บไซต์จ้ะ"
    
    # ประกอบร่างข้อความส่งเข้า LINE แบบคลีนๆ
    message = f"""✨ ปฏิทินงานบุญสร้างบารมี DMC ✨

💰 [ข่าวสารงานบุญเชิญชวนร่วมทำบุญ]
{merit_text}

🧡 [โครงการบวช & อบรมเยาวชน]
{ordination_text}

(ระบบคัดกรองเฉพาะงานบุญและโครงการเปิดรับสมัคร ลิงก์ตรงเป๊ะ 100% ครับจ้ะ)"""
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
    print("🚀 บอทสายบุญระบบตรง (เวอร์ชันกรองอัจฉริยะไร้คำมารบกวน) เริ่มรัน...")
    
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
                    web_data_list.append((t, h))
                    
            browser.close()
            
            print("🧠 กำลังสแกนหาเฉพาะเนื้อหาแก่นบุญ...")
            final_report = filter_and_format_merit_news(web_data_list)
            
            print("\n=== ผลลัพธ์สุดท้าย ===")
            print(final_report)
            
            send_line_message(final_report)

        except Exception as e:
            print(f"❌ ระบบภายนอกพังเนื่องจาก: {e}")
            if 'browser' in locals():
                browser.close()

if __name__ == "__main__":
    main()
