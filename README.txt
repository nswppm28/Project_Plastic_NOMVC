ระบบร้านรับซื้อพลาสติก (Flask Monolith / NOMVC)

โปรเจกต์นี้เป็นเว็บแอปสำหรับจัดการร้านรับซื้อพลาสติก พัฒนาด้วย Python Flask + MySQL + HTML/CSS/JavaScript แบบรวม backend หลักไว้ใน app.py

โครงสร้างโปรเจกต์
- app.py                    Flask backend รวม route/service/database helper
- templates/                ไฟล์ Jinja/HTML
- static/css/               CSS แยกตามหน้า
- static/js/main.js          JavaScript ส่วนกลาง
- sql/                      ไฟล์สร้างฐานข้อมูล trigger seed และ query
- docs/                     เอกสารประกอบฐานข้อมูล
- requirements.txt          รายการ package ที่ต้องติดตั้ง
- .env.example              ตัวอย่าง Environment Variables

วิธีติดตั้งและรัน

1) เข้าโฟลเดอร์โปรเจกต์
   cd Project_Plastic_NOMVC-main

2) สร้างและเปิด virtual environment
   python -m venv .venv
   .venv\Scriptsctivate

3) ติดตั้ง package
   pip install -r requirements.txt

   ถ้าจะใช้ AI model จริง ให้ติดตั้ง TensorFlow เพิ่ม โดยแนะนำใช้ Python 3.10 หรือ 3.11
   pip install tensorflow==2.17.1

4) ตั้งค่า MySQL ผ่าน Environment Variable หรือไฟล์ .env
   คัดลอก .env.example เป็น .env แล้วแก้ค่า DB_PASSWORD ให้ตรงกับเครื่อง

   ตัวอย่างค่า:
   DB_HOST=localhost
   DB_USER=root
   DB_PASSWORD=รหัสผ่าน MySQL ของเครื่อง
   DB_NAME=plastic_buyback_db

5) สร้างฐานข้อมูล
   เปิด MySQL แล้วรันไฟล์ตามลำดับนี้เท่านั้น

   SOURCE sql/01_schema.sql;
   SOURCE sql/03_seed.sql;
   SOURCE sql/02_triggers.sql;
   SOURCE sql/05_stock_export.sql;
   SOURCE sql/06_fix_stability.sql;

   หมายเหตุ:
   - 01_schema.sql สร้าง table หลักทั้งหมด รวมถึง stock export
   - 03_seed.sql ใส่ข้อมูลตัวอย่างและ rebuild stock ให้ตรงกับรายการซื้อ
   - 02_triggers.sql สร้าง trigger สำหรับรับซื้อเข้าคลัง
   - 05_stock_export.sql สร้าง trigger/ข้อมูลตัวอย่างสำหรับจำหน่ายออก
   - 06_fix_stability.sql เป็นไฟล์ safety migration สำหรับฐานข้อมูลเก่า

6) รันเว็บ
   python app.py

7) เปิดใช้งาน
   http://127.0.0.1:5000/login

บัญชีทดสอบจาก seed data
- admin / admin123
- staff01 / staff123

Route หลัก
- /login
- /logout
- /dashboard
- /customers
- /plastic-types
- /purchase
- /stock
- /stock-export
- /stock-export-history
- /receipt-history
- /receipt
- /ai-detection
- /api/ai_status
- /api/predict_plastic

หมายเหตุเกี่ยวกับ AI
- ถ้าไม่มี TensorFlow หรือไม่มีไฟล์ plastic_model.h5 เว็บส่วนอื่นยังรันได้
- หน้า AI จะแสดงสถานะว่าโมเดลยังไม่พร้อมใช้งาน
- ถ้าต้องใช้โมเดลจริง ให้วางไฟล์โมเดลไว้ตาม MODEL_PATH และตรวจ class order ให้ตรงกับ CLASS_NAMES ใน app.py

คำสั่งตรวจสอบหลังติดตั้ง

SHOW TABLES;
SELECT COUNT(*) FROM customers WHERE is_active = 1;
SELECT * FROM stock_summary;
SELECT * FROM stock_buyers;
SELECT TRIGGER_NAME FROM information_schema.TRIGGERS WHERE TRIGGER_SCHEMA = 'plastic_buyback_db';
