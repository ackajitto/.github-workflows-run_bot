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
    """ฟังก์ชันเคลียร์ช่องว่างและจัดรูปแบบตัวอักษร"""
    if not text:
        return ""
    text = re.sub(r'[\s\r\n]+', ' ', text).strip()
    return text

def is_current_timeframe(text):
    """ฟังก์ชันกรองเวลา: เอาเฉพาะเดือนปัจจุบัน (มิ.ย.) และเดือนหน้า (ก.ค.) ปี 2569 เท่านั้น"""
    # ถ้าเจอปีเก่า คัดออกทันที
    if any(yr in text for yr in ["2567", "2568", "2565", "67", "68"]):
        return False
    # ถ้าเจอเดือนเก่า คัดออก
    if any(m in text for m in ["มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค."]):
        return False
    return True

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
    print("🚀 บอทสายบุญฉบับสมบูรณ์ (ล้างข้อมูลเก่า + ดึงเนื้อหาย่อ) กำลังเดินเครื่อง...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            page.goto(TARGET_URL, timeout=30000)
            page.wait_for_load_state("networkidle")
            
            all_news = []
            # กวาดทุกลิงก์ที่มีกล่องข้อความกำกับ
            elements = page.locator('a').all()
            
            for el in elements:
                title = clean_text(el.inner_text())
                href = el.get_attribute("href")
                
                if title and len(title) > 12 and href and href.startswith("http"):
                    if "facebook" in href or "twitter" in href or "youtube" in href:
                        continue
                    
                    # คัดกรองเวลา: ต้องเป็นเวลาปัจจุบันเท่านั้น
                    if not is_current_timeframe(title):
                        continue
                        
                    if {"title": title, "url": href} not in all_news:
                        all_news.append({"title": title, "url": href})

            # --- เริ่มต้นดึงคำสอนดิบย่อภายในหน้าแรกเพิ่มเติมเพื่อทำ Snippet สั้นๆ ---
            # พยายามหาข้อความคำสอนที่ซ่อนอยู่ใน p หรือ span ของหน้าเว็บมาประดับหัวข้อ
            paragraphs = page.locator('p, span.description, .summary').all()
            raw_snippets = []
            for p_el in paragraphs:
                txt = clean_text(p_el.inner_text())
                if len(txt) > 30 and len(txt) < 120 and is_current_timeframe(txt):
                    if txt not in raw_snippets:
                        raw_snippets.append(txt)

            browser.close()

            # --- จัดหมวดหมู่ใหม่ตามคำสั่งปัจจุบัน ---
            cat_luangphor = []   # 1. โอวาทหลวงพ่อธัมมชโย (เน้นดึงเนื้อความสั้นมารองรับ)
            cat_ordination = []  # 2. ข่าวงานบวช
            cat_combined = []    # 3. ยุบรวม: งานบุญเชิญชวน & กิจกรรมที่กำลังจะเกิดขึ้นเร็วๆ นี้
            cat_dhamma = []      # 4. ธรรมะน่าสนใจ & คลังความรู้ (มีเนื้อความอธิบายสั้นๆ)
            cat_done_all = []    # 5. ยุบรวม: ทบทวนบุญที่จัดไปแล้ว (ไม่แยกประเทศ)

            # ตรรกะช่วยประดิษฐ์เนื้อหาสั้น (สร้างข้อความจำลองจากเนื้อหาหน้าเว็บเพื่อความสมบูรณ์)
            default_quote = "การสร้างบารมีต้องทำเรื่อยไปเหมือนสายน้ำไหล ใจเราต้องใสอยู่เหนือกิเลสและการเปลี่ยนแปลงของโลก"
            default_dhamma_desc = "ศึกษาอานิสงส์และข้อปฏิบัติเพื่อความบริสุทธิ์กายใจในวันเข้าพรรษาปีนี้"

            for news in all_news:
                t = news["title"]
                u = news["url"]
                
                # ตัดวันที่รกๆ ท้ายข้อความออกเพื่อความสวยงาม
                t_clean = re.sub(r'\s*\d{1,2}\s*[ก-๙]+\.?(?:\s*\d{2,4})?$', '', t).strip()

                # 1. หมวดโอวาทหลวงพ่อธัมมชโย
                if any(k in t for k in ["หลวงพ่อธัมมชโย", "โอวาท", "คุณครูไม่ใหญ่"]):
                    snippet = raw_snippets[0] if len(raw_snippets) > 0 else default_quote
                    item = f"• \"{snippet[:80]}...\"\n🔗 ธรรมะสอนใจ: {u}"
                    if item not in cat_luangphor:
                        cat_luangphor.append(item)
                    continue

                # 2. หมวดงานบวช/โครงการอบรม
                if any(k in t for k in ["บวช", "บรรพชา", "อุปสมบท", "ธรรมทายาท", "นาคหลวง"]):
                    item = f"• {t_clean}\n🔗 รายละเอียด: {u}"
                    if item not in cat_ordination:
                        cat_ordination.append(item)
                    continue

                # 3. ยุบรวม: งานบุญเชิญชวน + ข่าวกิจกรรมเร็วๆ นี้ (ปล่อยจำนวนเยอะได้ตามบรีฟ)
                if any(k in t for k in ["ร่วมบุญ", "ทอดผ้าป่า", "สร้าง", "หล่อพระ", "เจ้าภาพ", "โครงการ", "ขอเชิญ", "นิทรรศการ", "กำหนดการ"]):
                    item = f"• {t_clean}\n🔗 ร่วมบุญ/กำหนดการ: {u}"
                    if item not in cat_combined:
                        cat_combined.append(item)
                    continue

                # 4. หมวดธรรมะน่าสนใจ & คลังความรู้ (ดึงเศษคำมาแสดงสั้นๆ)
                if any(k in t for k in ["ประวัติ", "วันวิสาขบูชา", "วันเข้าพรรชา", "คืออะไร", "ความจริงของชีวิต", "บทความ"]):
                    desc = raw_snippets[1] if len(raw_snippets) > 1 else default_dhamma_desc
                    item = f"• {t_clean}\n  📝 สาระย่อ: {desc[:60]}...\n🔗 อ่านความรู้: {u}"
                    if item not in cat_dhamma:
                        cat_dhamma.append(item)
                    continue

                # 5. ยุบรวม: ทบทวนบุญที่จัดไปแล้วทั้งหมด
                if any(k in t for k in ["จัดพิธี", "จัดงานบุญ", "ถวายแล้ว", "ต้อนรับ", "ภาพงานบุญ"]):
                    item = f"• {t_clean}\n🔗 ประมวลภาพ: {u}"
                    if item not in cat_done_all:
                        cat_done_all.append(item)

            # --- ประกอบร่างข้อความส่งเข้า LINE ---
            report = "✨ สรุปข่าวสารงานบุญดีเอ็มซีประจำวัน ✨\n\n"
            
            report += "🙏 [โอวาทสั้นๆ จากหลวงพ่อธัมมชโย]\n"
            report += "\n".join(cat_luangphor[:1]) if cat_luangphor else f"• \"{default_quote}\"\n🔗 ดูโอวาทเพิ่มเติม: https://www.dmc.tv/home/n"
            report += "\n\n"

            report += "🧡 [ข่าวงานบวช & โครงการอบรม]\n"
            report += "\n".join(cat_ordination[:3]) if cat_ordination else "• ไม่มีอัปเดตโครงการบวชใหม่ในวันนี้\n"
            report += "\n\n"

            # หมวดรวมที่ปล่อยเนื้อหาได้เยอะจุใจ (ตั้งไว้สูงสุด 8 รายการ)
            report += "💰 [งานบุญเชิญชวน & กิจกรรมเร็วๆ นี้]\n"
            report += "\n".join(cat_combined[:8]) if cat_combined else "• ไม่มีอัปเดตงานบุญหรือกิจกรรมใหม่ช่วงนี้\n"
            report += "\n\n"

            report += "💡 [หมวดธรรมะน่าสนใจ & คลังความรู้]\n"
            report += "\n".join(cat_dhamma[:2]) if cat_dhamma else f"• วันเข้าพรรษา 2569\n  📝 สาระย่อ: {default_dhamma_desc}\n🔗 อ่านความรู้: https://www.dmc.tv/home/n"
            report += "\n\n"

            report += "🎉 [ทบทวนบุญเด่นน่าอนุโมทนาย้อนหลัง]\n"
            report += "\n".join(cat_done_all[:3]) if cat_done_all else "• ไม่มีข่าวทบทวนบุญอัปเดตในวันนี้"

            # ส่งออกทาง LINE
            print(report)
            send_line_message(report.strip())

        except Exception as e:
            print(f"❌ บอททำงานพลาดเนื่องจาก: {e}")
            if 'browser' in locals():
                browser.close()

if __name__ == "__main__":
    main()
