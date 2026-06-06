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
    text = re.sub(r'[\s\r\n]+', ' ', text).strip()
    # ลบวันเดือนปีห้อยท้ายออก (เช่น 6 มิ.ย. 2569 หรือ 6 มิ.ย. 69)
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
    print("🚀 บอทสายบุญเวอร์ชั่น Custom Categories กำลังเดินทางไปที่ dmc.tv...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            page.goto(TARGET_URL, timeout=30000)
            page.wait_for_load_state("networkidle")
            print("📥 โหลดหน้าเว็บสำเร็จ กำลังทำการกรองแบบเจาะลึก...")

            all_news = []
            links = page.locator('a').all()
            for link in links:
                text = clean_text(link.inner_text())
                href = link.get_attribute("href")
                
                if text and len(text) > 12 and href and href.startswith("http"):
                    if "facebook" in href or "twitter" in href or "youtube" in href:
                        continue
                    if {"title": text, "url": href} not in all_news:
                        all_news.append({"title": text, "url": href})

            browser.close()

            # --- ประกาศหมวดหมู่ตามบรีฟใหม่ ---
            cat_ordination = []   # 1. ไฮไลท์งานบวช
            cat_donation = []     # 2. งานบุญที่กำลังจะเกิดขึ้น (ทำบุญ/สร้าง/ทอดผ้าป่า) - ใส่ได้เยอะ
            cat_activity = []     # 3. ข่าวกิจกรรมที่กำลังจะเกิดขึ้น (ตารางงาน/นิทรรศการ/อบรม) - ใส่ได้เยอะ
            cat_luangphor = []    # 4. โอวาทหลวงพ่อธัมมชโย
            cat_dhamma_good = []  # 5. ธรรมะน่าสนใจ (ประวัติวันสำคัญ/ความรู้)
            cat_done_th = []      # 6. จัดไปแล้ว ในประเทศ (เน้นกระชับ)
            cat_done_inter = []   # 7. จัดไปแล้ว ต่างประเทศ (เน้นกระชับ)

            for news in all_news:
                t = news["title"]
                u = news["url"]
                item_str = f"• {t}\n🔗 {u}"

                # 1. หมวดโอวาทหลวงพ่อธัมมชโย (เช็กก่อนเพื่อน)
                if any(k in t for k in ["หลวงพ่อธัมมชโย", "โอวาท", "คุณครูไม่ใหญ่"]):
                    if item_str not in cat_luangphor:
                        cat_luangphor.append(item_str)
                    continue

                # 2. หมวดงานบวช/โครงการอบรมพระ
                if any(k in t for k in ["บวช", "บรรพชา", "อุปสมบท", "ธรรมทายาท", "นาคหลวง"]):
                    if item_str not in cat_ordination:
                        cat_ordination.append(item_str)
                    continue

                # 3. หมวดงานบุญที่กำลังจะเกิดขึ้น (เน้นชวนทำบุญ/สร้าง/ระดมทุน)
                if any(k in t for k in ["ขอเชิญร่วมบุญ", "เชิญร่วมบุญ", "ร่วมบุญ", "ทอดผ้าป่า", "สร้าง", "หล่อพระ", "เทคอนกรีต", "เจ้าภาพ"]):
                    if item_str not in cat_donation:
                        cat_donation.append(item_str)
                    continue

                # 4. หมวดข่าวกิจกรรมที่กำลังจะเกิดขึ้น (เน้นกำหนดการ/นิทรรศการ/วันสำคัญที่กำลังมาถึง)
                if any(k in t for k in ["โครงการ", "ขอเชิญ", "นิทรรศการ", "ตารางกิจกรรม", "เปิดรับสมัคร", "สัมมนา"]):
                    if item_str not in cat_activity:
                        cat_activity.append(item_str)
                    continue

                # 5. หมวดธรรมะน่าสนใจ/ความรู้บทความ
                if any(k in t for k in ["ประวัติ", "วันวิสาขบูชา", "วันมาฆบูชา", "วันอาสาฬหบูชา", "คืออะไร", "ความจริงของชีวิต", "เพลงธรรมะ", "อานิสงส์"]):
                    if item_str not in cat_dhamma_good:
                        cat_dhamma_good.append(item_str)
                    continue

                # 6. งานบุญที่จัดไปแล้ว (ในประเทศ/ต่างประเทศ)
                if any(k in t for k in ["จัดพิธี", "จัดงานบุญ", "ถวายแล้ว", "ต้อนรับ", "ตักบาตรแล้ว"]):
                    if any(k in t for k in ["โอ๊คแลนด์", "ลอนดอน", "ต่างประเทศ", "เยอรมนี", "อเมริกา", "ญี่ปุ่น", "สิงคโปร์"]):
                        if item_str not in cat_done_inter:
                            cat_done_inter.append(item_str)
                    else:
                        if item_str not in cat_done_th:
                            cat_done_th.append(item_str)

            # --- ประกอบร่างข้อความรายงานส่งเข้า LINE ---
            report = "✨ สรุปข่าวสารงานบุญดีเอ็มซีประจำวัน ✨\n\n"
            
            # 1. หมวดโอวาทหลวงพ่อธัมมชโย
            report += "🙏 [โอวาทหลวงพ่อธัมมชโย]\n"
            report += "\n".join(cat_luangphor[:2]) if cat_luangphor else "• ติดตามโอวาทธรรมได้ที่หน้าเว็บไซต์หลัก\n"
            report += "\n\n"

            # 2. ข่าวงานบวช
            report += "🧡 [ข่าวงานบวช & โครงการอบรม]\n"
            report += "\n".join(cat_ordination[:3]) if cat_ordination else "• ไม่มีอัปเดตโครงการบวชใหม่ในวันนี้\n"
            report += "\n\n"

            # 3. งานบุญที่กำลังจะเกิดขึ้น (ปล่อยเนื้อหาเยอะได้สูงสุด 5 ข่าว)
            report += "💰 [งานบุญที่กำลังจะเกิดขึ้น/เชิญร่วมบุญ]\n"
            report += "\n".join(cat_donation[:5]) if cat_donation else "• ไม่มีอัปเดตงานเชิญชวนทำบุญในวันนี้\n"
            report += "\n\n"

            # 4. ข่าวกิจกรรมที่กำลังจะเกิดขึ้น (ปล่อยเนื้อหาเยอะได้สูงสุด 5 ข่าว)
            report += "📅 [ข่าวกิจกรรม & กำหนดการเร็วๆ นี้]\n"
            report += "\n".join(cat_activity[:5]) if cat_activity else "• ไม่มีอัปเดตกิจกรรมใหม่ในวันนี้\n"
            report += "\n\n"

            # 5. ธรรมะน่าสนใจ
            report += "💡 [หมวดธรรมะน่าสนใจ & คลังความรู้]\n"
            report += "\n".join(cat_dhamma_good[:3]) if cat_dhamma_good else "• ไม่มีอัปเดตบทความธรรมะในวันนี้\n"
            report += "\n\n"

            # 6. จัดไปแล้ว ในประเทศ (เน้นกระชับ 2 ข่าว)
            report += "🇹🇭 [ทบทวนบุญที่จัดไปแล้ว: ในประเทศ]\n"
            report += "\n".join(cat_done_th[:2]) if cat_done_th else "• ไม่มีข่าวทบทวนบุญในประเทศวันนี้\n"
            report += "\n\n"

            # 7. จัดไปแล้ว ต่างประเทศ (เน้นกระชับ 2 ข่าว)
            report += "🇺🇸 [ทบทวนบุญที่จัดไปแล้ว: ต่างประเทศ]\n"
            report += "\n".join(cat_done_inter[:2]) if cat_done_inter else "• ไม่มีข่าวทบทวนบุญต่างประเทศวันนี้"

            # พิมพ์ตรวจสอบในหน้า Log และส่งหา LINE
            print(report)
            send_line_message(report.strip())

        except Exception as e:
            print(f"❌ บอททำงานพลาดเนื่องจาก: {e}")
            if 'browser' in locals():
                browser.close()

if __name__ == "__main__":
    main()
