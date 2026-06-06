name: Meditation Auto Fill

on:
  schedule:
    # ⏰ สั่งให้รันอัตโนมัติทุกวัน (เวลาในนี้เป็น UTC ดังนั้น 13:00 UTC จะเท่ากับ 20:00 น. หรือสองทุ่มตรงของไทย)
    - cron: '0 13 * * *' 
  workflow_dispatch: # เปิดปุ่มให้เราสามารถกดสั่งรันมือเองได้ทุกเมื่อที่ต้องการ

jobs:
  run-bot:
    runs-on: ubuntu-latest # ใช้คอมจำลอง Linux ของ GitHub รันให้ฟรี
    steps:
    - name: 1. ดึงโค้ดจากโปรเจกต์มาเตรียมพร้อม
      uses: actions/checkout@v4

    - name: 2. ติดตั้ง Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.10'

    - name: 3. ติดตั้ง Library และเบราว์เซอร์สำหรับ Playwright
      run: |
        pip install playwright requests
        playwright install chromium

    - name: 4. สั่งรันสคริปต์พร้อมดึงค่าความลับมาใช้งาน
      env:
        LINE_TOKEN: ${{ secrets.LINE_TOKEN }}
        LINE_TARGET_ID: ${{ secrets.LINE_TARGET_ID }}
        USERS_JSON: ${{ secrets.USERS_JSON }}
      run: python meditation_bot.py
