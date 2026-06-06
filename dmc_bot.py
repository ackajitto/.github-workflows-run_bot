import os
import requests
from playwright.sync_api import sync_playwright

# --- ตั้งค่า URL และ LINE API ---
TARGET_URL = "https://www.dmc.tv/home/"
LINE_API = "https://api.line.me/v2/bot/message/push"

# --- ดึงค่าความลับจาก GitHub Secrets ---
LINE_TOKEN = os.environ.get("LINE_TOKEN")
LINE_TARGET_ID = os.environ.get("LINE_TARGET_ID")

def send_line_message(msg):
    """ฟังก์ชันส่งข้อความเข้า LINE OA"""
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
    print("🚀 บอทสายบุญกำลังเริ่มเดินทางไปที่ dmc.tv...")
    
    with sync_playwright() as p:
        # เปิดเบราว์เซอร์แบบไร้หน้าต่าง (Headless)
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            # วิ่งไปยังหน้าเว็บเป้าหมาย และรอให้โหลดเสร็จ
            page.goto(TARGET_URL, timeout=30000)
            page.wait_for_load_state("networkidle")
            print("📥 โหลดหน้าเว็บสำเร็จ กำลังกวาดข้อมูล...")

            # 1. ดึงข้อมูลคติธรรม/สไลด์เด่นประจำวัน (แบนเนอร์ด้านบน)
            dhamma_quotes = []
            banners = page.locator('.swiper-slide img, .banner img, #slide img').all()
            for b in banners[:3]:  # เอามาเฉพาะ 3 รูปเด่นแรก
                title = b.get_attribute("alt") or b.get_attribute("title")
                if title and len(title.strip()) > 5:
                    dhamma_quotes.append(title.strip())

            # 2. ดึงหัวข้อข่าวสารทั้งหมดบนหน้าแรกเพื่อนำมาคัดแยก
            all_news = []
            links = page.locator('a').all()
            for link in links:
                text = link.inner_text().strip()
                href = link.get_attribute("href")
                
                # กรองเอาเฉพาะลิงก์ที่มีตัวหนังสือ และยาวพอจะเป็นหัวข้อข่าว ได้ไม่ซ้ำกัน
                if text and len(text) > 15 and href and href.startswith("http"):
                    if {"title": text, "url": href} not in all_news:
                        all_news.append({"title": text, "url": href})

            browser.close()

            # --- ตรรกะการคัดแยกหมวดหมู่ด้วยคำสำคัญ (Keywords) ---
            category_vihan = []  # หมวดสร้างโบสถ์/วิหารทาน
            category_boon = []   # หมวดงานบุญพิธี/ปฏิบัติธรรม
            category_education = [] # หมวดการศึกษา/ธรรมทาน
            category_general = [] # หมวดข่าวทั่วไป

            for news in all_news:
                t = news["title"]
                u = news["url"]
                item_str = f"• {t}\n🔗 {u}"

                if any(k in t for k in ["สร้าง", "หล่อพระ", "เจดีย์", "โบสถ์", "วิหาร", "กุฏิ"]):
                    category_vihan.append(item_str)
                elif any(k in t for k in ["พิธี", "บุญ", "บวช", "บรรพชา", "ปฏิบัติธรรม", "นั่งสมาธิ", "สวดมนต์"]):
                    category_boon.append(item_str)
                elif any(k in t for k in ["หนังสือ", "เรียน", "บาลี", "สอบ", "ศึกษา", "กฐิน"]):
                    category_education.append(item_str)
                else:
                    # ถ้ามีความยาวพอเหมาะและเข้าข่ายข่าวสารธรรมะทั่วไป
                    if len(category_general) < 3 and "dmc.tv" in u:
                        category_general.append(item_str)

            # --- ประกอบร่างข้อความรายงานส่งเข้า LINE ---
            report = "✨ สรุปข่าวบุญประจำวันจาก DMC.tv ✨\n\n"
            
            if dhamma_quotes:
                report += f"💡 [ข้อคิดธรรมะวันนี้]\n\"{dhamma_quotes[0]}\"\n\n"
            
            report += "🧱 [หมวดวิหารทาน/สร้างอาคาร]\n"
            report += "\n".join(category_vihan[:3]) if category_vihan else "• ไม่มีอัปเดตงานสร้างใหม่ในวันนี้\n"
            report += "\n\n"

            report += "🧘‍♂️ [หมวดปฏิบัติธรรม/งานบุญพิธี]\n"
            report += "\n".join(category_boon[:3]) if category_boon else "• ไม่มีอัปเดตงานบุญพิธีในวันนี้\n"
            report += "\n\n"

            report += "📖 [หมวดการศึกษา/ธรรมทาน]\n"
            report += "\n".join(category_education[:3]) if category_education else "• ไม่มีอัปเดตงานศึกษาในวันนี้\n"
            report += "\n\n"

            report += "📰 [ข่าวสารธรรมะน่าสนใจเพิ่มเติม]\n"
            report += "\n".join(category_general[:3]) if category_general else "• ไม่มีข่าวสารเพิ่มเติม\n"
            
            # พิมพ์สรุปดูในหน้า Log ของ GitHub ก่อน
            print("\n=== ข้อความที่เตรียมส่งเข้า LINE ===")
            print(report)
            print("===================================\n")
            
            # ส่งข้อความจริงเข้าสู่ LINE
            send_line_message(report.strip())

        except Exception as e:
            print(f"❌ บอททำงานพลาดเนื่องจาก: {e}")
            if 'browser' in locals():
                browser.close()

if __name__ == "__main__":
    main()
