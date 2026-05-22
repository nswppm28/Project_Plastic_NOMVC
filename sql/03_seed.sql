
SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;

USE plastic_buyback_db;

-- =====================================================
-- ล้างข้อมูลเดิม (ถ้ามี)
-- =====================================================

SET FOREIGN_KEY_CHECKS = 0;

TRUNCATE TABLE ai_predictions;
TRUNCATE TABLE receipts;
TRUNCATE TABLE purchase_items;
TRUNCATE TABLE purchases;
TRUNCATE TABLE purchase_prices;
TRUNCATE TABLE plastic_subtypes;
TRUNCATE TABLE plastic_types;
TRUNCATE TABLE customers;
TRUNCATE TABLE users;

SET FOREIGN_KEY_CHECKS = 1;

-- =====================================================
-- USERS
-- =====================================================

INSERT INTO users (
    user_id,
    username,
    password_hash,
    full_name,
    role,
    is_active
) VALUES

(
    1,
    'admin',
    'pbkdf2:sha256:1000000$plasticAdmin2026$10e6d152a32cea4b983622c36a270a1d0c8ce8ec8efd7a1fd6cdb4dbba14ddf6',
    'ผู้ดูแลระบบ',
    'admin',
    1
),

(
    2,
    'staff01',
    'pbkdf2:sha256:1000000$plasticStaff0126$b218147c36f9793b8323bab0fb077c16d206f6af2b3b3f537662c8dbf9921a88',
    'พนักงานรับซื้อ 1',
    'staff',
    1
),

(
    3,
    'owner',
    'pbkdf2:sha256:1000000$plasticOwner2026$5948fcf988881ef73a1f94c5a60ff51b1a55d25d000753574226744ab563ac5f',
    'เจ้าของร้าน',
    'admin',
    1
),

(
    4,
    'staff02',
    'pbkdf2:sha256:1000000$plasticStaff0226$d5ff836a5109f72f7fde9e26678f78162387b20e924b5339d6a3636e8011267c',
    'พนักงานรับซื้อ 2',
    'staff',
    1
);

-- =====================================================
-- CUSTOMERS
-- =====================================================

INSERT INTO customers (
    customer_id,
    customer_code,
    full_name,
    phone,
    address,
    note
) VALUES

(1, 'CUST-0001', 'สมชาย ใจดี', '081-234-5678', 'อ.เมือง จ.นครราชสีมา', 'ลูกค้าประจำ'),
(2, 'CUST-0002', 'พิมพ์ชนก ศรีทอง', '089-555-2244', 'อ.ชุมพวง จ.นครราชสีมา', NULL),
(3, 'CUST-0003', 'ประสิทธิ์ มั่นคง', '092-111-7788', 'อ.ปากช่อง จ.นครราชสีมา', NULL),
(4, 'CUST-0004', 'หทัยรัตน์ บุญมาก', '095-678-1099', 'อ.สีคิ้ว จ.นครราชสีมา', NULL);

-- =====================================================
-- PLASTIC TYPES
-- =====================================================

INSERT INTO plastic_types (
    type_id,
    type_code,
    type_name_th,
    type_name_en,
    description
) VALUES

(1, 'PET',  'โพลิเอทิลีนเทเรฟทาเลต', 'Polyethylene Terephthalate', 'พลาสติกประเภทขวดน้ำดื่มและบรรจุภัณฑ์ใส'),

(2, 'HDPE', 'โพลิเอทิลีนความหนาแน่นสูง', 'High-Density Polyethylene', 'พลาสติกขวดขาวขุ่นและขวดสี'),

(3, 'PVC',  'โพลิไวนิลคลอไรด์', 'Polyvinyl Chloride', 'พลาสติกท่อและเปลือกสายไฟ'),

(4, 'LDPE', 'โพลิเอทิลีนความหนาแน่นต่ำ', 'Low-Density Polyethylene', 'พลาสติกถุงและฟิล์ม'),

(5, 'PP',   'โพลิโพรพิลีน', 'Polypropylene', 'พลาสติกกล่องอาหารและฝาขวด'),

(6, 'PS',   'โพลิสไตรีน', 'Polystyrene', 'พลาสติกแก้ว โฟม และช้อนส้อม');

-- =====================================================
-- PLASTIC SUBTYPES
-- =====================================================

INSERT INTO plastic_subtypes (
    subtype_id,
    type_id,
    subtype_code,
    subtype_name,
    description
) VALUES

(1, 1, 'PET-CLEAR',     'ขวดใส',               'ขวด PET ใส'),
(2, 1, 'PET-COLOR',     'ขวดสี',               'ขวด PET สี'),
(3, 1, 'PET-MIX',       'ขวดรวม',              'ขวด PET คละชนิด'),

(4, 2, 'HDPE-MILKY',    'ขวดขาวขุ่น',          'ขวด HDPE สีขาวขุ่น'),
(5, 2, 'HDPE-COLOR',    'ขวดสี',               'ขวด HDPE สีต่าง ๆ'),

(6, 3, 'PVC-WIRE',      'เปลือกสายไฟ',         'เปลือกสายไฟ PVC'),
(7, 3, 'PVC-BLUE-PIPE', 'ท่อ PVC ฟ้า',         'ท่อ PVC สีฟ้า'),
(8, 3, 'PVC-MIX-PIPE',  'ท่อ PVC เหลือง/เทา',  'ท่อ PVC สีเหลืองและสีเทา'),

(9, 4, 'LDPE-BAG',      'ถุงรวม',              'ถุง LDPE รวม'),
(10,4, 'LDPE-FILM',     'ฟิล์มพันพาเลท',       'ฟิล์ม LDPE พันพาเลท'),

(11,5, 'PP-OPAQUE-BOX', 'กล่องขุ่น',           'กล่อง PP ขุ่น'),
(12,5, 'PP-CLEAR-BOX',  'กล่องใส',             'กล่อง PP ใส'),
(13,5, 'PP-CAP',        'ฝาขวด',               'ฝาขวด PP'),

(14,6, 'PS-CUP',        'แก้ว',                'แก้ว PS'),
(15,6, 'PS-CUTLERY',    'ช้อนส้อมมีด',         'ช้อน ส้อม มีด PS'),
(16,6, 'PS-FOAM',       'โฟม',                 'โฟม PS');

-- =====================================================
-- PURCHASE PRICES
-- =====================================================

INSERT INTO purchase_prices (
    price_id,
    subtype_id,
    unit_price,
    unit_name,
    effective_start_date,
    effective_end_date,
    is_current,
    reference_source,
    updated_by
) VALUES

(1,  1,  8.50, 'บาท/กก.', '2026-01-01', NULL, 1, 'ราคากลางอ้างอิงจากร้าน', 1),
(2,  2,  6.50, 'บาท/กก.', '2026-01-01', NULL, 1, 'ราคากลางอ้างอิงจากร้าน', 1),
(3,  3,  5.50, 'บาท/กก.', '2026-01-01', NULL, 1, 'ราคากลางอ้างอิงจากร้าน', 1),

(4,  4, 12.00, 'บาท/กก.', '2026-01-01', NULL, 1, 'ราคากลางอ้างอิงจากร้าน', 1),
(5,  5,  9.00, 'บาท/กก.', '2026-01-01', NULL, 1, 'ราคากลางอ้างอิงจากร้าน', 1),

(6,  6, 11.00, 'บาท/กก.', '2026-01-01', NULL, 1, 'ราคากลางอ้างอิงจากร้าน', 1),
(7,  7,  7.50, 'บาท/กก.', '2026-01-01', NULL, 1, 'ราคากลางอ้างอิงจากร้าน', 1),
(8,  8,  6.80, 'บาท/กก.', '2026-01-01', NULL, 1, 'ราคากลางอ้างอิงจากร้าน', 1),

(9,  9,  6.00, 'บาท/กก.', '2026-01-01', NULL, 1, 'ราคากลางอ้างอิงจากร้าน', 1),
(10, 10, 7.20, 'บาท/กก.', '2026-01-01', NULL, 1, 'ราคากลางอ้างอิงจากร้าน', 1),

(11, 11, 8.00, 'บาท/กก.', '2026-01-01', NULL, 1, 'ราคากลางอ้างอิงจากร้าน', 1),
(12, 12, 9.00, 'บาท/กก.', '2026-01-01', NULL, 1, 'ราคากลางอ้างอิงจากร้าน', 1),
(13, 13,10.00, 'บาท/กก.', '2026-01-01', NULL, 1, 'ราคากลางอ้างอิงจากร้าน', 1),

(14, 14, 5.50, 'บาท/กก.', '2026-01-01', NULL, 1, 'ราคากลางอ้างอิงจากร้าน', 1),
(15, 15, 4.80, 'บาท/กก.', '2026-01-01', NULL, 1, 'ราคากลางอ้างอิงจากร้าน', 1),
(16, 16, 3.50, 'บาท/กก.', '2026-01-01', NULL, 1, 'ราคากลางอ้างอิงจากร้าน', 1);

-- =====================================================
-- PURCHASES
-- =====================================================

INSERT INTO purchases (
    purchase_id,
    purchase_no,
    customer_id,
    purchase_date,
    total_amount,
    payment_method,
    note,
    created_by
) VALUES

(1, 'PU-2026-0001', 1, '2026-04-22 09:30:00', 178.25, 'cash', 'รับซื้อช่วงเช้า', 2),

(2, 'PU-2026-0002', 2, '2026-04-22 10:15:00', 205.00, 'cash', 'ลูกค้านำมาขายหลายประเภท', 2),

(3, 'PU-2026-0003', 3, '2026-04-21 14:20:00', 144.00, 'cash', 'รายการย้อนหลัง', 4);

-- =====================================================
-- PURCHASE ITEMS
-- =====================================================

INSERT INTO purchase_items (
    item_id,
    purchase_id,
    subtype_id,
    weight_kg,
    unit_price,
    amount,
    image_path,
    confirmed_by_user
) VALUES

(1, 1, 1, 12.500,  8.50, 106.25, 'uploads/pet_clear_001.jpg', 1),

(2, 1, 4,  6.000, 12.00,  72.00, 'uploads/hdpe_milky_001.jpg', 1),

(3, 2, 6, 15.000, 11.00, 165.00, 'uploads/pvc_wire_001.jpg', 1),

(4, 2,13,  4.000, 10.00,  40.00, 'uploads/pp_cap_001.jpg', 1),

(5, 3,10, 20.000,  7.20, 144.00, 'uploads/ldpe_film_001.jpg', 1);

-- =====================================================
-- RECEIPTS
-- =====================================================

INSERT INTO receipts (
    receipt_id,
    purchase_id,
    receipt_no,
    printed_at,
    printed_by,
    status
) VALUES

(1, 1, 'RC-2026-0001', '2026-04-22 09:35:00', 2, 'printed'),

(2, 2, 'RC-2026-0002', '2026-04-22 10:20:00', 2, 'printed'),

(3, 3, 'RC-2026-0003', '2026-04-21 14:25:00', 4, 'printed');

-- =====================================================
-- AI PREDICTIONS
-- =====================================================

INSERT INTO ai_predictions (
    ai_prediction_id,
    purchase_item_id,
    image_path,
    predicted_type_id,
    predicted_subtype_id,
    confidence,
    model_name,
    raw_result_json,
    is_used_in_transaction
) VALUES

(
    1,
    1,
    'uploads/pet_clear_001.jpg',
    1,
    1,
    96.45,
    'mock-efficientnetb0-v1',
    JSON_OBJECT('PET', 96.45, 'HDPE', 1.20, 'PVC', 0.55),
    1
),

(
    2,
    3,
    'uploads/pvc_wire_001.jpg',
    3,
    6,
    94.10,
    'mock-efficientnetb0-v1',
    JSON_OBJECT('PVC', 94.10, 'PS', 2.30, 'PP', 1.10),
    1
),

(
    3,
    NULL,
    'uploads/unconfirmed_sample_001.jpg',
    2,
    NULL,
    88.70,
    'mock-efficientnetb0-v1',
    JSON_OBJECT('HDPE', 88.70, 'LDPE', 5.50, 'PP', 2.20),
    0
);

-- =====================================================
-- ตรวจสอบข้อมูล
-- =====================================================

SELECT * FROM users;
SELECT * FROM customers;
SELECT * FROM purchases;
SELECT * FROM purchase_items;

