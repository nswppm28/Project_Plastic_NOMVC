USE plastic_buyback_db;

-- =====================================================
-- FIX 1: เพิ่ม customers.is_active ถ้ายังไม่มี
-- เหตุผล: customer_service.py ใช้ WHERE c.is_active = 1
-- และใช้ soft delete โดย UPDATE customers SET is_active = 0
-- =====================================================

DELIMITER $$

DROP PROCEDURE IF EXISTS add_customers_is_active_if_missing $$

CREATE PROCEDURE add_customers_is_active_if_missing()
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'customers'
          AND COLUMN_NAME = 'is_active'
    ) THEN
        ALTER TABLE customers
        ADD COLUMN is_active TINYINT(1) NOT NULL DEFAULT 1 AFTER note;
    END IF;
END $$

DELIMITER ;

CALL add_customers_is_active_if_missing();

DROP PROCEDURE IF EXISTS add_customers_is_active_if_missing;


-- =====================================================
-- FIX 2: เพิ่ม index สำหรับ customers.is_active ถ้ายังไม่มี
-- =====================================================

DELIMITER $$

DROP PROCEDURE IF EXISTS add_customers_is_active_index_if_missing $$

CREATE PROCEDURE add_customers_is_active_index_if_missing()
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM INFORMATION_SCHEMA.STATISTICS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'customers'
          AND INDEX_NAME = 'idx_customers_active'
    ) THEN
        ALTER TABLE customers
        ADD INDEX idx_customers_active (is_active);
    END IF;
END $$

DELIMITER ;

CALL add_customers_is_active_index_if_missing();

DROP PROCEDURE IF EXISTS add_customers_is_active_index_if_missing;


-- =====================================================
-- FIX 3: ตั้งค่าลูกค้าเดิมให้ active ทั้งหมด
-- =====================================================

UPDATE customers
SET is_active = 1
WHERE is_active IS NULL;