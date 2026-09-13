import os
import json
import requests
from playwright.sync_api import sync_playwright

# ==========================================
# 1. ตั้งค่า URL (แก้ไขโดเมนให้ตรงกันแล้ว)
# ==========================================
LOGIN_URL = "https://hr.dkcmain.org:9000/login.php" # (แก้เป็น URL หน้า Login ของคุณถ้าไม่ใช่ชื่อนี้)
MEMO_URL = "https://hr.dkcmain.org:9000/meditation/memo.php" # โดเมนเดียวกับหน้า Login

# ==========================================
# 2. อ่านค่าจาก Environment Variables
# ==========================================
USERS_JSON = os.environ.get("USERS_JSON", "[]")
LINE_TOKEN = os.environ.get("LINE_TOKEN", "")
LINE_TARGET_ID = os.environ.get("LINE_TARGET_ID", "")

def send_line_notify(message):
    if not LINE_TOKEN:
        return
    headers = {"Authorization": f"Bearer {LINE_TOKEN}"}
    payload = {"message": message}
    try:
        response = requests.post("https://notify-api.line.me/api/notify", headers=headers, data=payload)
        print(f"📲 สถานะการส่ง LINE: {response.status_code}")
    except Exception as e:
        print(f"❌ ส่ง LINE ไม่สำเร็จ: {e}")

def main():
    try:
        users = json.loads(USERS_JSON)
    except json.JSONDecodeError:
        print("⚠️ ระบบหยุดทำงาน: ข้อมูล USERS_JSON ผิดพลาด")
        return

    if not len(users):
        print("⚠️ ไม่มีรายชื่อผู้ใช้ให้ดำเนินการ")
        return

    summary_success = []
    summary_failed = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        
        for user_data in users:
            name = user_data.get("name", "Unknown")
            print(f"\nกำลังดำเนินการให้: {name}...")
            
            success = False
            for attempt in range(3):
                # เปิดหน้าต่างใหม่ทุกครั้งที่ลองใหม่ เพื่อเคลียร์คุกกี้/สถานะเก่า
                context = browser.new_context()
                page = context.new_page()
                
                try:
                    # ==========================================
                    # จุดที่ 1: โค้ดสำหรับ Login (นำโค้ดเดิมของคุณมาใส่ตรงนี้)
                    # ==========================================
                    # ตัวอย่าง:
                    # page.goto(LOGIN_URL)
                    # page.fill('input[name="username"]', user_data['username'])
                    # page.fill('input[name="password"]', user_data['password'])
                    # page.click('button[type="submit"]')
                    # page.wait_for_load_state('networkidle')
                    
                    
                    # ==========================================
                    # จุดที่ 2: เข้าหน้าบันทึกสมาธิ (ใช้ URL ที่แก้แล้ว)
                    # ==========================================
                    page.goto(MEMO_URL)
                    
                    # รอให้ช่องกรอกข้อมูลปรากฏ (รอสูงสุด 15 วินาที)
                    page.wait_for_selector('input[id^="hour_"]', timeout=15000)
                    
                    
                    # ==========================================
                    # จุดที่ 3: โค้ดสำหรับกรอกข้อมูลและบันทึก (นำโค้ดเดิมของคุณมาใส่ตรงนี้)
                    # ==========================================
                    # ตัวอย่าง:
                    # page.fill('input[id^="hour_"]', str(user_data['hours']))
                    # page.click('button[id="save_btn"]') # เปลี่ยนเป็นปุ่มบันทึกของคุณ
                    # page.wait_for_load_state('networkidle')
                    

                    success = True
                    summary_success.append(name)
                    print(f"✅ บันทึกของ {name} สำเร็จ")
                    context.close()
                    break # หากทำสำเร็จ ให้หยุดการลองใหม่ แล้วข้ามไปคนต่อไป
                    
                except Exception as e:
                    # ✅ ระบบถ่ายรูปหน้าจออัตโนมัติเมื่อเกิด Error
                    error_img = f"error_{name}_attempt_{attempt+1}.png"
                    page.screenshot(path=error_img)
                    
                    # ดึงข้อความ Error บรรทัดแรกมาแสดงให้ดูง่ายๆ
                    error_msg = str(e).split('\n')[0] 
                    print(f"⚠️ พลาดรอบที่ {attempt + 1}/3 ของ {name}: {error_msg}")
                    
                    context.close()
                    
                    if attempt < 2:
                        print("🔄 กำลังลองใหม่...")
                    
            if not success:
                print(f"❌ หมดโควต้า! ข้ามการทำรายการของ {name}")
                summary_failed.append(f"{name} (พลาด 3 รอบรวด: {error_msg})")

        browser.close()

    # ==========================================
    # สรุปผลส่งเข้า LINE
    # ==========================================
    report_msg = "\n🙏 อัปเดตการกรอกชั่วโมงนั่งสมาธิ:\n"
    
    if summary_success:
        report_msg += "\n✅ สถานะสำเร็จ:\n- " + "\n- ".join(summary_success)
        
    if summary_failed:
        report_msg += "\n\n❌ สถานะผิดพลาด (ลองซ้ำ 3 รอบแล้วก็ไม่ผ่าน):\n- " + "\n- ".join(summary_failed)

    send_line_notify(report_msg)

if __name__ == "__main__":
    main()
