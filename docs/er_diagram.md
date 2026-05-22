# ER Diagram - ระบบร้านรับซื้อพลาสติก

## 1) ภาพรวมความสัมพันธ์ของตาราง

```mermaid
erDiagram
    USERS ||--o{ PURCHASES : creates
    USERS ||--o{ PURCHASE_PRICES : updates
    USERS ||--o{ RECEIPTS : prints

    CUSTOMERS ||--o{ PURCHASES : sells_to_shop

    PLASTIC_TYPES ||--o{ PLASTIC_SUBTYPES : contains
    PLASTIC_SUBTYPES ||--o{ PURCHASE_PRICES : has_price_history

    PURCHASES ||--o{ PURCHASE_ITEMS : contains
    PLASTIC_SUBTYPES ||--o{ PURCHASE_ITEMS : selected_as

    PURCHASES ||--|| RECEIPTS : generates

    PLASTIC_SUBTYPES ||--|| STOCK_SUMMARY : summarized_in
    PLASTIC_SUBTYPES ||--o{ STOCK_MOVEMENTS : moves
    PURCHASE_ITEMS ||--o{ STOCK_MOVEMENTS : creates_stock_movement

    PURCHASE_ITEMS ||--o| AI_PREDICTIONS : may_have_prediction
    PLASTIC_TYPES ||--o{ AI_PREDICTIONS : predicted_type
    PLASTIC_SUBTYPES ||--o{ AI_PREDICTIONS : predicted_subtype

    
---

