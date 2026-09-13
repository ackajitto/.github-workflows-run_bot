import os
import json
import time
import requests
from playwright.sync_api import sync_playwright

BASE_URL = "https://hr.dkcmain.org:9000"
LOGIN_PATH = "/admin/login"
MEMO_URL = "https://hr2.dkcmain.org/meditation/memo.php" 
LINE_API = "https://api.line.me/v2/bot/message/push"

LINE_TOKEN = os.environ.get("LINE_TOKEN")
LINE_TARGET_ID = os.environ.get("LINE_TARGET_ID")
USERS_JSON_STR = os.environ.get("USERS_JSON", "[]")

try:
    users = json.loads(USERS_JSON_STR)
except Exception as e:
    users = []
    print(f"❌ รูปแบบ USERS_JSON ผิดพลาด: {e}")

def send_line_message(msg):
    if not LINE_TOKEN or not LINE_TARGET_ID:
        print("⚠️ ไม่ได้ตั้งค่า LINE ข้ามการแจ้งเตือน...")
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

def process_user(browser, person):
    my_hour = str(person.get("hours", 2))
    my_min = str(person.get("mins", 0))
    filled_dates = []

    context = browser.new_context(
        viewport={'width': 1280, 'height': 800},
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
    )
    
    page = context.new_page()

    try:
        # 1. เข้าสู่ระบบ
        page.goto(BASE_URL + LOGIN_PATH, wait_until='networkidle')
        page.fill('[id="data.login"]', person["user"])
        page.fill('[id="data.password"]', person["pass"])
        page.click('.fi-btn-label')
        
        page.wait_for_timeout(3000)
        page.wait_for_load_state('networkidle')

        # 2. เปิดหน้ากรอกชั่วโมง
        page.goto(MEMO_URL, wait_until='networkidle')
        page.wait_for_timeout(2000)

        # 3. ตรวจสอบช่องกรอกข้อมูล
        page.wait_for_selector('input[id^="hour_"]', timeout=15000)

        hour_fields = page.locator('input[id^="hour_"]').all()
        for h in hour_fields:
            if h.is_editable() and (h.input_value() == "0" or h.input_value() == ""):
                h.fill(my_hour)
                
                date_str = h.evaluate("""el => {
                    let curr = el.parentElement;
                    while(curr && curr !== document.body) {
                        if (curr.querySelectorAll('input[id^="hour_"]').length > 1) break;
                        let text = curr.innerText.replace(/[\\s\\r\\n]+/g, '');
                        let match = text.match(/(\\d{1,2}[ก-๙]+\\.[ก-๙]+\\.)/);
                        if (match) return match[1];
                        curr = curr.parentElement;
                    }
                    return 'ไม่ระบุ';
                }""")

                if date_str and date_str != 'ไม่ระบุ' and date_str not in filled_dates:
                    filled_dates.append(date_str)

        minute_fields = page.locator('input[id^="minute_"]').all()
        for m in minute_fields:
            if m.is_editable() and (m.input_value() == "0" or m.input_value() == ""):
                m.fill(my_min)

        # 4. กดบันทึก
        if filled_dates:
            save_btn = page.locator('button.btn-success:has-text("บันทึก")')
            if save_btn.is_visible():
                save_btn.click()
                page.wait_for_load_state('networkidle', timeout=10000) 
            else:
                raise Exception("หาปุ่มบันทึกไม่เจอ")

            time_text = f"{my_hour} ชม." if my_min == "0" else f"{my_hour} ชม. {my_min} นาที"
            dates_joined = ", ".join(filled_dates)
            return f"{person['name']} ➡️ {time_text}\n    📅 วันที่: {dates_joined}"
        else:
            return f"{person['name']} ➡️ ครบแล้ว ไม่มีช่องว่างให้กรอก ✨"

    except Exception as e:
        # ถ่ายรูปเก็บไว้ทุกกรณีเมื่อเกิด Error
        safe_filename = f"error_{person['name']}.png"
        page.screenshot(path=safe_filename, full_page=True)
        raise e
    finally:
        context.close()

def main():
    if not users:
        send_line_message("⚠️ ระบบหยุดทำงาน: ข้อมูล USERS_JSON ผิดพลาด หรือไม่มีรายชื่อ")
        return

    success_list = []
    fail_list = []
    MAX_RETRIES = 3

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True) 

        for person in users:
            print(f"\nกำลังดำเนินการให้: {person['name']}...")
            
            for attempt in range(1, MAX_RETRIES + 1):
                try:
                    result_msg = process_user(browser, person)
                    success_list.append(result_msg)
                    print(f"✅ สำเร็จในรอบที่ {attempt}")
                    break 
                
                except Exception as e:
                    print(f"⚠️ พลาดรอบที่ {attempt}/{MAX_RETRIES} ของ {person['name']}: {e}")
                    if attempt == MAX_RETRIES:
                        print(f"❌ หมดโควต้า! ข้ามการทำรายการของ {person['name']}")
                        fail_list.append(f"{person['name']} (พลาด 3 รอบรวด: {str(e)[:50]}...)")
                    else:
                        print("🔄 กำลังลองใหม่...")

        browser.close()

    report = "🙏 อัปเดตการกรอกชั่วโมงนั่งสมาธิ:\n"
    if success_list:
        report += "\n✅ สถานะสำเร็จ:\n" + "\n".join([f" - {n}" for n in success_list])
    if fail_list:
        report += "\n❌ สถานะผิดพลาด (ลองซ้ำ 3 รอบแล้วก็ไม่ผ่าน):\n" + "\n".join([f" - {n}" for n in fail_list])

    print("\n" + report)
    send_line_message(report.strip())

if __name__ == "__main__":
    main()
