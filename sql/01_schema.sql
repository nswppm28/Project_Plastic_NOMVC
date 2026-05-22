CREATE DATABASE IF NOT EXISTS plastic_buyback_db
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE plastic_buyback_db;

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS ai_predictions;
DROP TABLE IF EXISTS stock_export_items;
DROP TABLE IF EXISTS stock_exports;
DROP TABLE IF EXISTS stock_buyers;
DROP TABLE IF EXISTS stock_movements;
DROP TABLE IF EXISTS stock_summary;
DROP TABLE IF EXISTS receipts;
DROP TABLE IF EXISTS purchase_items;
DROP TABLE IF EXISTS purchases;
DROP TABLE IF EXISTS purchase_prices;
DROP TABLE IF EXISTS plastic_subtypes;
DROP TABLE IF EXISTS plastic_types;
DROP TABLE IF EXISTS customers;
DROP TABLE IF EXISTS users;

SET FOREIGN_KEY_CHECKS = 1;

CREATE TABLE users (
    user_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(150) NOT NULL,
    role VARCHAR(30) NOT NULL DEFAULT 'staff',
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE customers (
    customer_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    customer_code VARCHAR(20) NOT NULL UNIQUE,
    full_name VARCHAR(150) NOT NULL,
    phone VARCHAR(30) NOT NULL,
    address TEXT NULL,
    note VARCHAR(255) NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_customers_full_name (full_name),
    INDEX idx_customers_phone (phone),
    INDEX idx_customers_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE plastic_types (
    type_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    type_code VARCHAR(10) NOT NULL UNIQUE,
    type_name_th VARCHAR(100) NOT NULL,
    type_name_en VARCHAR(150) NOT NULL,
    description VARCHAR(255) NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_plastic_types_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE plastic_subtypes (
    subtype_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    type_id BIGINT UNSIGNED NOT NULL,
    subtype_code VARCHAR(30) NOT NULL UNIQUE,
    subtype_name VARCHAR(150) NOT NULL,
    description VARCHAR(255) NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_plastic_subtypes_type
        FOREIGN KEY (type_id) REFERENCES plastic_types(type_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    CONSTRAINT uq_plastic_subtypes_name_per_type
        UNIQUE (type_id, subtype_name),
    INDEX idx_plastic_subtypes_type_id (type_id),
    INDEX idx_plastic_subtypes_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE purchase_prices (
    price_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    subtype_id BIGINT UNSIGNED NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    unit_name VARCHAR(20) NOT NULL DEFAULT 'บาท/กก.',
    effective_start_date DATE NOT NULL,
    effective_end_date DATE NULL,
    is_current TINYINT(1) NOT NULL DEFAULT 1,
    reference_source VARCHAR(255) NULL,
    updated_by BIGINT UNSIGNED NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_purchase_prices_subtype
        FOREIGN KEY (subtype_id) REFERENCES plastic_subtypes(subtype_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    CONSTRAINT fk_purchase_prices_updated_by
        FOREIGN KEY (updated_by) REFERENCES users(user_id)
        ON UPDATE CASCADE
        ON DELETE SET NULL,
    INDEX idx_purchase_prices_subtype (subtype_id),
    INDEX idx_purchase_prices_current (subtype_id, is_current, effective_start_date),
    INDEX idx_purchase_prices_date_range (effective_start_date, effective_end_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE purchases (
    purchase_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    purchase_no VARCHAR(30) NOT NULL UNIQUE,
    customer_id BIGINT UNSIGNED NOT NULL,
    purchase_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    total_amount DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    payment_method VARCHAR(30) NOT NULL DEFAULT 'cash',
    note VARCHAR(255) NULL,
    created_by BIGINT UNSIGNED NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_purchases_customer
        FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    CONSTRAINT fk_purchases_created_by
        FOREIGN KEY (created_by) REFERENCES users(user_id)
        ON UPDATE CASCADE
        ON DELETE SET NULL,
    INDEX idx_purchases_customer (customer_id),
    INDEX idx_purchases_purchase_date (purchase_date),
    INDEX idx_purchases_customer_date (customer_id, purchase_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE purchase_items (
    item_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    purchase_id BIGINT UNSIGNED NOT NULL,
    subtype_id BIGINT UNSIGNED NOT NULL,
    weight_kg DECIMAL(10,3) NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    amount DECIMAL(12,2) NOT NULL,
    image_path VARCHAR(255) NULL,
    confirmed_by_user TINYINT(1) NOT NULL DEFAULT 1,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_purchase_items_purchase
        FOREIGN KEY (purchase_id) REFERENCES purchases(purchase_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    CONSTRAINT fk_purchase_items_subtype
        FOREIGN KEY (subtype_id) REFERENCES plastic_subtypes(subtype_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    INDEX idx_purchase_items_purchase_id (purchase_id),
    INDEX idx_purchase_items_subtype_id (subtype_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE receipts (
    receipt_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    purchase_id BIGINT UNSIGNED NOT NULL,
    receipt_no VARCHAR(30) NOT NULL UNIQUE,
    printed_at DATETIME NULL,
    printed_by BIGINT UNSIGNED NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'printed',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_receipts_purchase
        FOREIGN KEY (purchase_id) REFERENCES purchases(purchase_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    CONSTRAINT fk_receipts_printed_by
        FOREIGN KEY (printed_by) REFERENCES users(user_id)
        ON UPDATE CASCADE
        ON DELETE SET NULL,
    CONSTRAINT uq_receipts_purchase UNIQUE (purchase_id),
    INDEX idx_receipts_printed_at (printed_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE stock_summary (
    stock_summary_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    subtype_id BIGINT UNSIGNED NOT NULL,
    total_weight_kg DECIMAL(12,3) NOT NULL DEFAULT 0.000,
    last_in_datetime DATETIME NULL,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_stock_summary_subtype
        FOREIGN KEY (subtype_id) REFERENCES plastic_subtypes(subtype_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    CONSTRAINT uq_stock_summary_subtype UNIQUE (subtype_id),
    INDEX idx_stock_summary_updated_at (updated_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE stock_movements (
    movement_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    subtype_id BIGINT UNSIGNED NOT NULL,
    purchase_item_id BIGINT UNSIGNED NULL,
    stock_export_item_id BIGINT UNSIGNED NULL,
    movement_type VARCHAR(30) NOT NULL,
    quantity_kg DECIMAL(12,3) NOT NULL,
    balance_after_kg DECIMAL(12,3) NULL,
    note VARCHAR(255) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_stock_movements_subtype
        FOREIGN KEY (subtype_id) REFERENCES plastic_subtypes(subtype_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    INDEX idx_stock_movements_subtype (subtype_id),
    INDEX idx_stock_movements_purchase_item (purchase_item_id),
    INDEX idx_stock_movements_export_item (stock_export_item_id),
    INDEX idx_stock_movements_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE stock_buyers (
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

CREATE TABLE stock_exports (
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

CREATE TABLE stock_export_items (
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

CREATE TABLE ai_predictions (
    ai_prediction_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    purchase_item_id BIGINT UNSIGNED NULL,
    image_path VARCHAR(255) NOT NULL,
    predicted_type_id BIGINT UNSIGNED NULL,
    predicted_subtype_id BIGINT UNSIGNED NULL,
    confidence DECIMAL(5,2) NOT NULL,
    model_name VARCHAR(100) NULL,
    raw_result_json JSON NULL,
    is_used_in_transaction TINYINT(1) NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_ai_predictions_purchase_item
        FOREIGN KEY (purchase_item_id) REFERENCES purchase_items(item_id)
        ON UPDATE CASCADE
        ON DELETE SET NULL,
    CONSTRAINT fk_ai_predictions_type
        FOREIGN KEY (predicted_type_id) REFERENCES plastic_types(type_id)
        ON UPDATE CASCADE
        ON DELETE SET NULL,
    CONSTRAINT fk_ai_predictions_subtype
        FOREIGN KEY (predicted_subtype_id) REFERENCES plastic_subtypes(subtype_id)
        ON UPDATE CASCADE
        ON DELETE SET NULL,
    INDEX idx_ai_predictions_purchase_item (purchase_item_id),
    INDEX idx_ai_predictions_type (predicted_type_id),
    INDEX idx_ai_predictions_subtype (predicted_subtype_id),
    INDEX idx_ai_predictions_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;