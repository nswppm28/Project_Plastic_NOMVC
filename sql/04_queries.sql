USE plastic_buyback_db;

/* =========================================================
   1) Dashboard: สรุปรายวัน
   ========================================================= */
SELECT
    DATE(p.purchase_date) AS report_date,
    COUNT(DISTINCT p.purchase_id) AS purchase_count,
    COALESCE(SUM(p.total_amount), 0) AS total_amount
FROM purchases p
WHERE DATE(p.purchase_date) = CURDATE()
GROUP BY DATE(p.purchase_date);


/* =========================================================
   2) Dashboard: สรุปรายเดือน
   ========================================================= */
SELECT
    DATE_FORMAT(p.purchase_date, '%Y-%m') AS report_month,
    COUNT(DISTINCT p.purchase_id) AS purchase_count,
    COALESCE(SUM(p.total_amount), 0) AS total_amount
FROM purchases p
WHERE YEAR(p.purchase_date) = YEAR(CURDATE())
  AND MONTH(p.purchase_date) = MONTH(CURDATE())
GROUP BY DATE_FORMAT(p.purchase_date, '%Y-%m');


/* =========================================================
   3) Dashboard: ประเภทพลาสติกที่ร้านรับซื้อมากที่สุด
      วัดจากน้ำหนักรวม
   ========================================================= */
SELECT
    pt.type_code,
    pt.type_name_th,
    ROUND(SUM(pi.weight_kg), 3) AS total_weight_kg,
    ROUND(SUM(pi.amount), 2) AS total_amount
FROM purchase_items pi
INNER JOIN plastic_subtypes ps
    ON pi.subtype_id = ps.subtype_id
INNER JOIN plastic_types pt
    ON ps.type_id = pt.type_id
GROUP BY pt.type_id, pt.type_code, pt.type_name_th
ORDER BY total_weight_kg DESC, total_amount DESC
LIMIT 1;


/* =========================================================
   4) Dashboard: ลูกค้าขายบ่อยที่สุด
      วัดจากจำนวนครั้งของ purchase
   ========================================================= */
SELECT
    c.customer_id,
    c.customer_code,
    c.full_name,
    COUNT(DISTINCT p.purchase_id) AS purchase_count,
    ROUND(SUM(p.total_amount), 2) AS total_amount
FROM purchases p
INNER JOIN customers c
    ON p.customer_id = c.customer_id
GROUP BY c.customer_id, c.customer_code, c.full_name
ORDER BY purchase_count DESC, total_amount DESC
LIMIT 1;


/* =========================================================
   5) Dashboard: มูลค่ารวมทั้งหมด
   ========================================================= */
SELECT
    COUNT(*) AS total_purchase_documents,
    ROUND(SUM(total_amount), 2) AS grand_total_amount
FROM purchases;


/* =========================================================
   6) Dashboard: รายการรับซื้อล่าสุด
   ========================================================= */
SELECT
    p.purchase_id,
    p.purchase_no,
    p.purchase_date,
    c.customer_code,
    c.full_name AS customer_name,
    GROUP_CONCAT(
        CONCAT(pt.type_code, ' / ', ps.subtype_name, ' (', pi.weight_kg, ' กก.)')
        ORDER BY pi.item_id
        SEPARATOR ', '
    ) AS items_summary,
    p.total_amount
FROM purchases p
INNER JOIN customers c
    ON p.customer_id = c.customer_id
INNER JOIN purchase_items pi
    ON p.purchase_id = pi.purchase_id
INNER JOIN plastic_subtypes ps
    ON pi.subtype_id = ps.subtype_id
INNER JOIN plastic_types pt
    ON ps.type_id = pt.type_id
GROUP BY
    p.purchase_id,
    p.purchase_no,
    p.purchase_date,
    c.customer_code,
    c.full_name,
    p.total_amount
ORDER BY p.purchase_date DESC
LIMIT 10;


/* =========================================================
   7) Query ดึงราคาปัจจุบันจาก subtype
      ใช้สำหรับหน้าบันทึกรายรับซื้อ
   ========================================================= */
SET @subtype_id = 6;

SELECT
    pp.price_id,
    ps.subtype_code,
    ps.subtype_name,
    pp.unit_price,
    pp.unit_name,
    pp.effective_start_date
FROM purchase_prices pp
INNER JOIN plastic_subtypes ps
    ON pp.subtype_id = ps.subtype_id
WHERE pp.subtype_id = @subtype_id
  AND pp.is_current = 1
  AND (pp.effective_end_date IS NULL OR pp.effective_end_date >= CURDATE())
ORDER BY pp.effective_start_date DESC
LIMIT 1;


/* =========================================================
   8) Query ใบเสร็จ: header
   ========================================================= */
SET @purchase_id = 1;

SELECT
    r.receipt_no,
    r.printed_at,
    p.purchase_no,
    p.purchase_date,
    c.customer_code,
    c.full_name AS customer_name,
    c.phone,
    c.address,
    p.total_amount
FROM receipts r
INNER JOIN purchases p
    ON r.purchase_id = p.purchase_id
INNER JOIN customers c
    ON p.customer_id = c.customer_id
WHERE p.purchase_id = @purchase_id;


/* =========================================================
   9) Query ใบเสร็จ: items
   ========================================================= */
SELECT
    pi.item_id,
    pt.type_code,
    ps.subtype_name,
    pi.weight_kg,
    pi.unit_price,
    pi.amount
FROM purchase_items pi
INNER JOIN plastic_subtypes ps
    ON pi.subtype_id = ps.subtype_id
INNER JOIN plastic_types pt
    ON ps.type_id = pt.type_id
WHERE pi.purchase_id = @purchase_id
ORDER BY pi.item_id;


/* =========================================================
   10) Query ตรวจสอบ stock summary
   ========================================================= */
SELECT
    pt.type_code,
    ps.subtype_code,
    ps.subtype_name,
    ss.total_weight_kg,
    ss.last_in_datetime,
    ss.updated_at
FROM stock_summary ss
INNER JOIN plastic_subtypes ps
    ON ss.subtype_id = ps.subtype_id
INNER JOIN plastic_types pt
    ON ps.type_id = pt.type_id
ORDER BY pt.type_code, ps.subtype_name;


/* =========================================================
   11) Query ดูประวัติ stock movements
   ========================================================= */
SELECT
    sm.movement_id,
    pt.type_code,
    ps.subtype_name,
    sm.purchase_item_id,
    sm.movement_type,
    sm.quantity_kg,
    sm.balance_after_kg,
    sm.note,
    sm.created_at
FROM stock_movements sm
INNER JOIN plastic_subtypes ps
    ON sm.subtype_id = ps.subtype_id
INNER JOIN plastic_types pt
    ON ps.type_id = pt.type_id
ORDER BY sm.created_at DESC, sm.movement_id DESC;


/* =========================================================
   12) Query ดูผล AI prediction
   ========================================================= */
SELECT
    ap.ai_prediction_id,
    ap.image_path,
    pt.type_code AS predicted_type_code,
    ps.subtype_name AS predicted_subtype_name,
    ap.confidence,
    ap.model_name,
    ap.is_used_in_transaction,
    ap.created_at
FROM ai_predictions ap
LEFT JOIN plastic_types pt
    ON ap.predicted_type_id = pt.type_id
LEFT JOIN plastic_subtypes ps
    ON ap.predicted_subtype_id = ps.subtype_id
ORDER BY ap.created_at DESC;