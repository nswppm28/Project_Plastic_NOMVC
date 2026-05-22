USE plastic_buyback_db;

SET NAMES utf8mb4;

-- =====================================================
-- ระบบจำหน่ายออก / ส่งออกพลาสติกจากคลัง
-- =====================================================


-- =====================================================
-- 1) ตารางผู้รับซื้อปลายทาง เช่น โรงงานรีไซเคิล / ลานรับซื้อใหญ่
-- =====================================================

CREATE TABLE IF NOT EXISTS stock_buyers (
    buyer_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    buyer_code VARCHAR(30) NOT NULL UNIQUE,
    buyer_name VARCHAR(150) NOT NULL,
    buyer_type VARCHAR(50) NOT NULL DEFAULT 'recycle_factory',
    phone VARCHAR(30) NULL,
    address TEXT NULL,
    contact_person VARCHAR(150) NULL,
    note VARCHAR(255) NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_stock_buyers_name (buyer_name),
    INDEX idx_stock_buyers_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- =====================================================
-- 2) ตารางหัวรายการจำหน่ายออก
-- =====================================================

CREATE TABLE IF NOT EXISTS stock_exports (
    export_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    export_no VARCHAR(30) NOT NULL UNIQUE,
    buyer_id BIGINT UNSIGNED NOT NULL,
    export_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    total_weight_kg DECIMAL(12,3) NOT NULL DEFAULT 0.000,
    total_amount DECIMAL(12,2) NOT NULL DEFAULT 0.00,

    transport_method VARCHAR(100) NULL,
    vehicle_plate VARCHAR(50) NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'completed',
    note VARCHAR(255) NULL,

    created_by BIGINT UNSIGNED NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_stock_exports_buyer
        FOREIGN KEY (buyer_id) REFERENCES stock_buyers(buyer_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT fk_stock_exports_created_by
        FOREIGN KEY (created_by) REFERENCES users(user_id)
        ON UPDATE CASCADE
        ON DELETE SET NULL,

    INDEX idx_stock_exports_buyer (buyer_id),
    INDEX idx_stock_exports_date (export_date),
    INDEX idx_stock_exports_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- =====================================================
-- 3) ตารางรายการย่อยของการจำหน่ายออก
-- =====================================================

CREATE TABLE IF NOT EXISTS stock_export_items (
    export_item_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    export_id BIGINT UNSIGNED NOT NULL,
    subtype_id BIGINT UNSIGNED NOT NULL,

    weight_kg DECIMAL(12,3) NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    amount DECIMAL(12,2) NOT NULL,

    note VARCHAR(255) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_stock_export_items_export
        FOREIGN KEY (export_id) REFERENCES stock_exports(export_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,

    CONSTRAINT fk_stock_export_items_subtype
        FOREIGN KEY (subtype_id) REFERENCES plastic_subtypes(subtype_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    INDEX idx_stock_export_items_export (export_id),
    INDEX idx_stock_export_items_subtype (subtype_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- =====================================================
-- 4) เพิ่ม column ใน stock_movements เพื่อเชื่อมกับรายการจำหน่ายออก
-- =====================================================

DELIMITER $$

DROP PROCEDURE IF EXISTS add_stock_export_item_id_if_missing $$

CREATE PROCEDURE add_stock_export_item_id_if_missing()
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'stock_movements'
          AND COLUMN_NAME = 'stock_export_item_id'
    ) THEN
        ALTER TABLE stock_movements
        ADD COLUMN stock_export_item_id BIGINT UNSIGNED NULL AFTER purchase_item_id;

        ALTER TABLE stock_movements
        ADD INDEX idx_stock_movements_export_item (stock_export_item_id);
    END IF;
END $$

DELIMITER ;

CALL add_stock_export_item_id_if_missing();

DROP PROCEDURE IF EXISTS add_stock_export_item_id_if_missing;


-- =====================================================
-- 5) Trigger: เพิ่มรายการจำหน่ายออกแล้วตัดสต๊อก
-- =====================================================

DROP TRIGGER IF EXISTS trg_stock_export_items_after_insert;

DELIMITER $$

CREATE TRIGGER trg_stock_export_items_after_insert
AFTER INSERT ON stock_export_items
FOR EACH ROW
BEGIN
    DECLARE current_balance DECIMAL(12,3);
    DECLARE new_balance DECIMAL(12,3);

    SELECT COALESCE(MAX(total_weight_kg), 0)
    INTO current_balance
    FROM stock_summary
    WHERE subtype_id = NEW.subtype_id;

    IF current_balance < NEW.weight_kg THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'จำนวนสินค้าในคลังไม่เพียงพอสำหรับจำหน่ายออก';
    END IF;

    SET new_balance = current_balance - NEW.weight_kg;

    UPDATE stock_summary
    SET total_weight_kg = new_balance,
        updated_at = CURRENT_TIMESTAMP
    WHERE subtype_id = NEW.subtype_id;

    UPDATE stock_exports
    SET total_weight_kg = total_weight_kg + NEW.weight_kg,
        total_amount = total_amount + NEW.amount,
        updated_at = CURRENT_TIMESTAMP
    WHERE export_id = NEW.export_id;

    INSERT INTO stock_movements (
        subtype_id,
        purchase_item_id,
        stock_export_item_id,
        movement_type,
        quantity_kg,
        balance_after_kg,
        note,
        created_at
    )
    VALUES (
        NEW.subtype_id,
        NULL,
        NEW.export_item_id,
        'SALE_OUT',
        NEW.weight_kg * -1,
        new_balance,
        'จำหน่ายออกจากคลัง',
        CURRENT_TIMESTAMP
    );
END $$

DELIMITER ;


-- =====================================================
-- 6) Trigger: ลบรายการจำหน่ายออกแล้วคืนสต๊อก
-- ใช้กรณียกเลิกหรือบันทึกผิด
-- =====================================================

DROP TRIGGER IF EXISTS trg_stock_export_items_after_delete;

DELIMITER $$

CREATE TRIGGER trg_stock_export_items_after_delete
AFTER DELETE ON stock_export_items
FOR EACH ROW
BEGIN
    DECLARE current_balance DECIMAL(12,3);
    DECLARE new_balance DECIMAL(12,3);

    SELECT COALESCE(MAX(total_weight_kg), 0)
    INTO current_balance
    FROM stock_summary
    WHERE subtype_id = OLD.subtype_id;

    SET new_balance = current_balance + OLD.weight_kg;

    INSERT INTO stock_summary (
        subtype_id,
        total_weight_kg,
        updated_at
    )
    VALUES (
        OLD.subtype_id,
        new_balance,
        CURRENT_TIMESTAMP
    )
    ON DUPLICATE KEY UPDATE
        total_weight_kg = new_balance,
        updated_at = CURRENT_TIMESTAMP;

    UPDATE stock_exports
    SET total_weight_kg = GREATEST(total_weight_kg - OLD.weight_kg, 0),
        total_amount = GREATEST(total_amount - OLD.amount, 0),
        updated_at = CURRENT_TIMESTAMP
    WHERE export_id = OLD.export_id;

    INSERT INTO stock_movements (
        subtype_id,
        purchase_item_id,
        stock_export_item_id,
        movement_type,
        quantity_kg,
        balance_after_kg,
        note,
        created_at
    )
    VALUES (
        OLD.subtype_id,
        NULL,
        OLD.export_item_id,
        'SALE_OUT_CANCEL',
        OLD.weight_kg,
        new_balance,
        'ยกเลิกการจำหน่ายออก คืนสินค้าเข้าคลัง',
        CURRENT_TIMESTAMP
    );
END $$

DELIMITER ;


-- =====================================================
-- 7) เพิ่มข้อมูลตัวอย่างผู้รับซื้อปลายทาง
-- =====================================================

INSERT INTO stock_buyers (
    buyer_code,
    buyer_name,
    buyer_type,
    phone,
    address,
    contact_person,
    note
)
VALUES
(
    'BUY-001',
    'โรงงานรีไซเคิลพลาสติกตัวอย่าง',
    'recycle_factory',
    '080-000-0001',
    'กรุงเทพมหานคร',
    'ฝ่ายจัดซื้อ',
    'ผู้รับซื้อปลายทางสำหรับนำพลาสติกไปรีไซเคิล'
),
(
    'BUY-002',
    'ลานรับซื้อวัสดุรีไซเคิลตัวอย่าง',
    'recycle_yard',
    '080-000-0002',
    'ปทุมธานี',
    'เจ้าของร้าน',
    'รับซื้อพลาสติกคัดแยกจากร้านย่อย'
)
ON DUPLICATE KEY UPDATE
    buyer_name = VALUES(buyer_name),
    buyer_type = VALUES(buyer_type),
    phone = VALUES(phone),
    address = VALUES(address),
    contact_person = VALUES(contact_person),
    note = VALUES(note),
    is_active = 1;