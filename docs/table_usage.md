## `docs/table_usage.md`

```md
# รายชื่อตารางและหน้าที่การใช้งาน

## 1) รายชื่อตารางทั้งหมด

1. `users`
2. `customers`
3. `plastic_types`
4. `plastic_subtypes`
5. `purchase_prices`
6. `purchases`
7. `purchase_items`
8. `receipts`
9. `stock_summary`
10. `stock_movements`
11. `ai_predictions`

---

## 2) ตารางที่ใช้กับแต่ละฟังก์ชัน

### จัดการข้อมูลลูกค้า
ใช้ตาราง:
- `customers`

### จัดการประเภทพลาสติก
ใช้ตาราง:
- `plastic_types`
- `plastic_subtypes`

### ปรับปรุงราคารับซื้อ
ใช้ตาราง:
- `purchase_prices`

### บันทึกรายรับซื้อ
ใช้ตาราง:
- `purchases`
- `purchase_items`

### คำนวณราคารับซื้อ
ใช้ตาราง:
- `purchase_prices`
- `purchase_items`

แนวคิด:
- ดึงราคา current ของ `subtype_id` จาก `purchase_prices`
- นำ `unit_price × weight_kg` ไปเก็บใน `purchase_items.amount`

### พิมพ์ใบเสร็จรับซื้อ
ใช้ตาราง:
- `receipts`
- `purchases`
- `purchase_items`
- `customers`
- `plastic_subtypes`

### ตรวจสอบสต๊อก
ใช้ตาราง:
- `stock_summary`
- `stock_movements`
- `plastic_subtypes`
- `plastic_types`

### Dashboard รายวัน / รายเดือน / ยอดรวม / ประเภทยอดนิยม / ลูกค้าขายบ่อย
ใช้ตาราง:
- `purchases`
- `purchase_items`
- `customers`
- `plastic_subtypes`
- `plastic_types`

### AI prediction
ใช้ตาราง:
- `ai_predictions`
- `purchase_items`
- `plastic_types`
- `plastic_subtypes`

---

## 3) สรุปว่าแต่ละตารางทำหน้าที่อะไร

### `users`
เก็บข้อมูลผู้ใช้งานระบบ เช่น ผู้ดูแลหรือพนักงาน

### `customers`
เก็บข้อมูลลูกค้า

### `plastic_types`
เก็บชนิดหลักของพลาสติก

### `plastic_subtypes`
เก็บประเภทย่อยของพลาสติกตามที่ร้านรับซื้อจริง

### `purchase_prices`
เก็บราคารับซื้อรายประเภทย่อย พร้อมประวัติราคา

### `purchases`
เก็บหัวเอกสารรายการรับซื้อ

### `purchase_items`
เก็บรายการย่อยในเอกสารรับซื้อ

### `receipts`
เก็บข้อมูลใบเสร็จที่อ้างอิงจากรายการรับซื้อ

### `stock_summary`
เก็บยอด stock สะสมต่อประเภทย่อย

### `stock_movements`
เก็บประวัติการเคลื่อนไหวของ stock

### `ai_predictions`
เก็บผลทำนายจากโมเดล AI เพื่อเชื่อมต่อกับระบบในอนาคต