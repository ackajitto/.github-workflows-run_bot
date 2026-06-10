import os
import requests
from playwright.sync_api import sync_playwright

# --- ตั้งค่า URL และ API หลัก ---
TARGET_URL = "https://www.dmc.tv/"
LINE_API = "https://api.line.me/v2/bot/message/push"

LINE_TOKEN = os.environ.get("LINE_TOKEN")
LINE_TARGET_ID = os.environ.get("LINE_TARGET_ID")

def filter_and_format_merit_news(web_data_list):
    # 🟢 คีย์เวิร์ดเฉพาะงานบุญอนาคต / การเชิญชวนร่วมบุญ / โครงการเปิดรับสมัคร
    merit_keywords = ['ผ้าป่า', 'บูชาข้าวพระ', 'หล่อพระ', 'ตอกเสาเข็ม', 'สร้างเจดีย์', 'เจ้าภาพ', 'ขอเชิญ', 'เชิญชวน', 'ร่วมสนับสนุน']
    study_keywords = ['บรรพชา', 'อุปสมบท', 'อบรม', 'รับสมัคร']
    
    # 🔴 คีย์เวิร์ดต้องห้าม
    banned_keywords = ['mv', 'official', 'เพลง', 'เกียรติบัตร', 'ประมวลภาพ', 'ภาพงานบุญ', 'ถวายแล้ว', 'ผ่านพ้น', 'ภาพข่าว']
    
    merit_events = []
    ordination_events = []
    seen_titles = set()
    
    for title, href in web_data_list:
        clean_title = " ".join(title.split())
        title_lower = clean_title.lower()
        
        if any(b_kw in title_lower for b_kw in banned_keywords):
            continue
            
        if clean_title in seen_titles:
            continue
            
        # 🎯 [ปรับแต่งที่นี่] ถอดวงเล็บ [] ออกทั้งหมด เพื่อไม่ให้ LINE แปลงลิงก์เพี้ยนเป็น %5D
        if any(kw in title_lower for kw in study_keywords):
            seen_titles.add(clean_title)
            ordination_events.append(f"• {clean_title}\n  🔗 รายละเอียด: {href}")
        elif any(kw in title_lower for kw in merit_keywords):
            seen_titles.add(clean_title)
            merit_events.append(f"• {clean_title}\n  🔗 ลิงก์ร่วมบุญ: {href}")
                
    merit_text = "\n".join(merit_events[:5]) if merit_events else "• ติดตามข่าวสารงานบุญเพิ่มเติมได้ที่หน้าเว็บไซต์จ้ะ"
    ordination_text = "\n".join(ordination_events[:3]) if ordination_events else "• ติดตามโครงการบวชประจำปีได้ที่หน้าเว็บไซต์จ้ะ"
    
    message = f"""✨ ปฏิทินงานบุญสร้างบารมี DMC ✨

💰 [ข่าวสารงานบุญเชิญชวนร่วมทำบุญ]
{merit_text}

🧡 [โครงการบวช & อบรมเยาวชน]
{ordination_text}

(ระบบปรับโครงสร้างลิงก์แบบอิสระ หมดปัญหา LINE อ่านลิงก์เพี้ยนแน่นอนครับจ้ะ)"""
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
    print("🚀 บอทสายบุญระบบตรง (เวอร์ชันแก้ปัญหา %5D) เริ่มรัน...")
    
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
                    
                    # เติม / ปิดท้ายลิงก์เพื่อความสมบูรณ์ของเว็บ DMC
                    if not h.endswith("/") and not any(h.endswith(ext) for ext in ['.html', '.htm', '.php', '.mp4', '.png', '.jpg']):
                        h = h + "/"
                        
                    web_data_list.append((t, h))
                    
            browser.close()
            
            print("🧠 กำลังสแกนหาแก่นบุญและเคลียร์ท้ายลิงก์ให้สะอาด...")
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
