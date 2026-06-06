import os
import re
import requests
from playwright.sync_api import sync_playwright

# --- ตั้งค่า URL และ LINE API ---
TARGET_URL = "https://www.dmc.tv/home/"
LINE_API = "https://api.line.me/v2/bot/message/push"

LINE_TOKEN = os.environ.get("LINE_TOKEN")
LINE_TARGET_ID = os.environ.get("LINE_TARGET_ID")

def clean_text(text):
    """ฟังก์ชันทำความสะอาดข้อความ ลบการเคาะเว้นวรรคแปลกๆ และลบวันที่ห้อยท้าย"""
    if not text:
        return ""
    # ยุบช่องว่าง/การขึ้นบรรทัดใหม่ที่ติดมาให้เหลือเว้นวรรคช่องเดียว
    text = re.sub(r'[\s\r\n]+', ' ', text).strip()
    # ตัดพวกวันที่ห้อยท้ายออก (เช่น 6 มิ.ย. 2569 หรือ 6 มิ.ย. 69) เพื่อให้ชื่อข่าวสั้นกระชับ
    text = re.sub(r'\s*\d{1,2}\s*[ก-๙]+\.?(?:\s*\d{2,4})?$', '', text).strip()
    return text

def send_line_message(msg):
    if not LINE_TOKEN or not LINE_TARGET_ID:
        print("⚠️ ไม่ได้ตั้งค่า LINE ให้ถูกต้อง (ระบบจะพิมพ์ข้อความลง Log แทน)")
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
    print("🚀 บอทสายบุญเวอร์ชั่นอัปเกรด กำลังเดินทางไปที่ dmc.tv...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            page.goto(TARGET_URL, timeout=30000)
            page.wait_for_load_state("networkidle")
            print("📥 โหลดหน้าเว็บสำเร็จ กำลังกรองหมวดหมู่เนื้อหา...")

            all_news = []
            links = page.locator('a').all()
            for link in links:
                text = clean_text(link.inner_text())
                href = link.get_attribute("href")
                
                if text and len(text) > 12 and href and href.startswith("http"):
                    # ป้องกันการดึงเมนูซ้ำๆ หรือลิงก์ที่ไม่ใช่ข่าว
                    if "facebook" in href or "twitter" in href or "youtube" in href:
                        continue
                    if {"title": text, "url": href} not in all_news:
                        all_news.append({"title": text, "url": href})

            browser.close()

            # --- ตรรกะแยกหมวดหมู่ตามบรีฟใหม่ของคุณ ---
            cat_ordination = []  # 1. ข่าวงานบวช/โครงการอบรม
            cat_upcoming = []    # 2. ข่าวกิจกรรม/เชิญชวนทำบุญช่วงนี้ (Future/Present)
            cat_done_th = []     # 3. งานบุญที่จัดไปแล้ว (ในประเทศ)
            cat_done_inter = []  # 4. งานบุญที่จัดไปแล้ว (ต่างประเทศ)

            for news in all_news:
                t = news["title"]
                u = news["url"]
                item_str = f"• {t}\n🔗 {u}"

                # 1. คัดกรองหมวดงานบวช (เน้นคำเฉพาะเจาะจง)
                if any(k in t for k in ["บวช", "บรรพชา", "อุปสมบท", "ธรรมทายาท", "นาคหลวง"]):
                    if item_str not in cat_ordination:
                        cat_ordination.append(item_str)
                    continue

                # 2. คัดกรองงานเชิญชวนทำบุญ/กิจกรรมที่กำลังจะเกิด (มักมีคำว่า โครงการ, เชิญร่วม, ขอเชิญ, นิทรรศการ)
                if any(k in t for k in ["โครงการ", "เชิญร่วม", "ขอเชิญ", "นิทรรศการ", "ตารางกิจกรรม", "เปิดรับสมัคร"]):
                    if item_str not in cat_upcoming:
                        cat_upcoming.append(item_str)
                    continue

                # 3 & 4. งานบุญที่จัดไปแล้ว (ดูจากคำว่า "จัดงาน", "จัดพิธี", "ถวายแล้ว")
                if any(k in t for k in ["จัดพิธี", "จัดงานบุญ", "ถวาย", "ต้อนรับ", "สัมมนา"]):
                    # แยกต่างประเทศ (ดูจากชื่อวัดต่างประเทศ หรือคำว่า วัดพระธรรมกายตามด้วยชื่อเมือง)
                    if any(k in t for k in ["โอ๊คแลนด์", "ลอนดอน", "ต่างประเทศ", "เยอรมนี", "อเมริกา", "ญี่ปุ่น", "สิงคโปร์"]) or ( "วัดพระธรรมกาย" in t and not t.endswith("วัดพระธรรมกาย")):
                        if item_str not in cat_done_inter:
                            cat_done_inter.append(item_str)
                    else:
                        if item_str not in cat_done_th:
                            cat_done_th.append(item_str)

            # --- ประกอบร่างข้อความรายงานส่งเข้า LINE ---
            report = "✨ สรุปข่าวสารงานบุญดีเอ็มซีประจำวัน ✨\n\n"
            
            # หมวดที่ 1: งานบวช (คุณชอบเป็นพิเศษ ดันขึ้นบนสุด)
            report += "🧡 [ไฮไลท์: ข่าวงานบวช & โครงการอบรม]\n"
            report += "\n".join(cat_ordination[:3]) if cat_ordination else "• ไม่มีอัปเดตโครงการบวชใหม่ในวันนี้\n"
            report += "\n\n"

            # หมวดที่ 2: งานทำบุญ/กิจกรรมช่วงนี้
            report += "📢 [ขอเชิญร่วมบุญ & กิจกรรมช่วงนี้]\n"
            report += "\n".join(cat_upcoming[:3]) if cat_upcoming else "• ไม่มีอัปเดตกิจกรรมเชิญชวนในวันนี้\n"
            report += "\n\n"

            # หมวดที่ 3: จัดไปแล้ว ในประเทศ (จำกัดเอาแค่ 2 ข่าวพอตามบรีฟ)
            report += "🇹🇭 [ทบทวนบุญที่จัดไปแล้ว: ในประเทศ]\n"
            report += "\n".join(cat_done_th[:2]) if cat_done_th else "• ไม่มีข่าวทบทวนบุญในประเทศวันนี้\n"
            report += "\n\n"

            # หมวดที่ 4: จัดไปแล้ว ต่างประเทศ (จำกัดเอาแค่ 2 ข่าวพอตามบรีฟ)
            report += "🇺🇸 [ทบทวนบุญที่จัดไปแล้ว: ต่างประเทศ]\n"
            report += "\n".join(cat_done_inter[:2]) if cat_done_inter else "• ไม่มีข่าวทบทวนบุญต่างประเทศวันนี้\n"

            # พิมพ์ตรวจสอบในหน้า Log
            print("\n=== ข้อความที่จัดระเบียบใหม่แล้ว ===")
            print(report)
            print("===================================\n")
            
            # ส่งข้อความเข้า LINE
            send_line_message(report.strip())

        except Exception as e:
            print(f"❌ บอททำงานพลาดเนื่องจาก: {e}")
            if 'browser' in locals():
                browser.close()

if __name__ == "__main__":
    main()
