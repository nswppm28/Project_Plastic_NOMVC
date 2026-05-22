USE plastic_buyback_db;

DROP TRIGGER IF EXISTS trg_purchase_items_after_insert;
DROP TRIGGER IF EXISTS trg_purchase_items_after_delete;

DELIMITER $$

CREATE TRIGGER trg_purchase_items_after_insert
AFTER INSERT ON purchase_items
FOR EACH ROW
BEGIN
    /*
      1) อัปเดตยอดรวมของหัวรายการรับซื้อ
      2) อัปเดต stock_summary
      3) บันทึก stock_movements
    */

    UPDATE purchases
    SET total_amount = total_amount + NEW.amount,
        updated_at = CURRENT_TIMESTAMP
    WHERE purchase_id = NEW.purchase_id;

    INSERT INTO stock_summary (
        subtype_id,
        total_weight_kg,
        last_in_datetime,
        updated_at
    )
    VALUES (
        NEW.subtype_id,
        NEW.weight_kg,
        CURRENT_TIMESTAMP,
        CURRENT_TIMESTAMP
    )
    ON DUPLICATE KEY UPDATE
        total_weight_kg = total_weight_kg + VALUES(total_weight_kg),
        last_in_datetime = VALUES(last_in_datetime),
        updated_at = CURRENT_TIMESTAMP;

    INSERT INTO stock_movements (
        subtype_id,
        purchase_item_id,
        movement_type,
        quantity_kg,
        balance_after_kg,
        note
    )
    SELECT
        NEW.subtype_id,
        NEW.item_id,
        'PURCHASE_IN',
        NEW.weight_kg,
        ss.total_weight_kg,
        CONCAT('รับเข้าจากรายการซื้อเลขที่ purchase_id=', NEW.purchase_id)
    FROM stock_summary ss
    WHERE ss.subtype_id = NEW.subtype_id;
END$$

CREATE TRIGGER trg_purchase_items_after_delete
AFTER DELETE ON purchase_items
FOR EACH ROW
BEGIN
    /*
      1) ลดยอดรวมของหัวรายการรับซื้อ
      2) ลด stock_summary
      3) บันทึก stock_movements เป็นรายการยกเลิก
    */

    UPDATE purchases
    SET total_amount = GREATEST(0, total_amount - OLD.amount),
        updated_at = CURRENT_TIMESTAMP
    WHERE purchase_id = OLD.purchase_id;

    UPDATE stock_summary
    SET total_weight_kg = GREATEST(0, total_weight_kg - OLD.weight_kg),
        updated_at = CURRENT_TIMESTAMP
    WHERE subtype_id = OLD.subtype_id;

    INSERT INTO stock_movements (
        subtype_id,
        purchase_item_id,
        movement_type,
        quantity_kg,
        balance_after_kg,
        note
    )
    SELECT
        OLD.subtype_id,
        OLD.item_id,
        'PURCHASE_VOID',
        (0 - OLD.weight_kg),
        ss.total_weight_kg,
        CONCAT('ยกเลิกรายการซื้อ purchase_id=', OLD.purchase_id)
    FROM stock_summary ss
    WHERE ss.subtype_id = OLD.subtype_id;
END$$

DELIMITER ;