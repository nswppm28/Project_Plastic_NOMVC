ระบบร้านรับซื้อพลาสติก (Backend รวมใน app.py)

โครงสร้างโปรเจกต์เวอร์ชันนี้
- app.py                    Backend Flask ทั้งหมดถูกรวมไว้ในไฟล์เดียว
- templates/                ไฟล์หน้าเว็บ Jinja/HTML
- static/                   CSS และ JavaScript
- sql/                      ไฟล์สร้างฐานข้อมูล, trigger, seed และ query
- docs/                     เอกสารประกอบฐานข้อมูล

ไฟล์/โฟลเดอร์ backend แบบแยก MVC ถูกลบออกแล้ว
- ไม่มี app_core/
- ไม่มี config.py
- ไม่มี app_old.py
- ไม่มี README_MVC_LIGHT.txt

วิธีรันระบบ
1) เข้าโฟลเดอร์โปรเจกต์
   cd Project_Plastic-main

2) ติดตั้ง package ที่จำเป็น
   pip install flask mysql-connector-python werkzeug pillow numpy

   ถ้าต้องใช้หน้า AI จริง ให้ติดตั้ง TensorFlow เพิ่ม
   pip install tensorflow

3) ตั้งค่าฐานข้อมูลใน app.py หรือกำหนดผ่าน Environment Variable
   DB_HOST=localhost
   DB_USER=root
   DB_PASSWORD=รหัสผ่าน MySQL ของเครื่อง
   DB_NAME=plastic_buyback_db

4) รันเว็บ
   python app.py

5) เปิดใช้งาน
   http://127.0.0.1:5000/login

บัญชีทดสอบจาก seed data
- admin / admin123
- staff01 / staff123

Route หลักที่มีใน app.py
- /login
- /logout
- /dashboard
- /customers
- /plastic-types
- /purchase
- /stock
- /receipt-history
- /receipt
- /ai-detection
- /stock-export
- /stock-export-history
- /api/ai_status
- /api/predict_plastic

หมายเหตุ
- templates และ static ยังใช้ชื่อเดิม จึงไม่กระทบ UI เดิม
- ถ้าเปลี่ยนรหัสผ่าน MySQL ให้แก้ DB_CONFIG ใน app.py
- ถ้าไม่มีไฟล์ plastic_model.h5 ระบบเว็บส่วนอื่นยังรันได้ แต่หน้า AI จะขึ้นข้อความว่าโมเดลยังไม่พร้อมใช้งาน
