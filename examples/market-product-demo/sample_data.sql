-- DataWraith Market Product Management Demo Seed Data
-- Safe to rerun because inserts use ON CONFLICT where appropriate.

INSERT INTO market_categories (id, name, slug, active) VALUES
    (1, 'Fresh Produce', 'fresh-produce', true),
    (2, 'Pantry', 'pantry', true),
    (3, 'Beverages', 'beverages', true),
    (4, 'Household', 'household', true),
    (5, 'Personal Care', 'personal-care', true)
ON CONFLICT (id) DO NOTHING;

INSERT INTO market_suppliers (id, name, email, lead_time_days, active) VALUES
    (1, 'Green Farm Co', 'ops@greenfarm.example', 2, true),
    (2, 'Urban Pantry Ltd', 'orders@urbanpantry.example', 4, true),
    (3, 'River Drinks', 'supply@riverdrinks.example', 3, true),
    (4, 'Clean Home Wholesale', 'hello@cleanhome.example', 5, true),
    (5, 'Care Goods Market', 'team@caregoods.example', 6, true)
ON CONFLICT (id) DO NOTHING;

INSERT INTO products (id, category_id, supplier_id, sku, name, stock, price, reorder_level, status) VALUES
    (1, 1, 1, 'FRUIT-APPLE-001', 'Apple Pack', 120, 3.20, 20, 'active'),
    (2, 1, 1, 'VEG-CARROT-001', 'Carrot Bag', 95, 2.10, 20, 'active'),
    (3, 1, 1, 'VEG-TOMATO-001', 'Tomato Box', 80, 4.50, 15, 'active'),
    (4, 2, 2, 'PANTRY-RICE-001', 'Jasmine Rice 5kg', 60, 12.90, 10, 'active'),
    (5, 2, 2, 'PANTRY-PASTA-001', 'Pasta Pack', 75, 2.80, 15, 'active'),
    (6, 2, 2, 'PANTRY-OIL-001', 'Cooking Oil 1L', 45, 5.70, 10, 'active'),
    (7, 3, 3, 'DRINK-WATER-001', 'Mineral Water 24 Pack', 140, 6.40, 25, 'active'),
    (8, 3, 3, 'DRINK-JUICE-001', 'Orange Juice 1L', 50, 3.60, 12, 'active'),
    (9, 3, 3, 'DRINK-TEA-001', 'Iced Tea Bottle', 85, 1.90, 20, 'active'),
    (10, 4, 4, 'HOME-DETERGENT-001', 'Laundry Detergent', 35, 9.90, 8, 'active'),
    (11, 4, 4, 'HOME-TISSUE-001', 'Tissue Box', 110, 1.50, 25, 'active'),
    (12, 4, 4, 'HOME-CLEANER-001', 'Surface Cleaner', 42, 4.20, 10, 'active'),
    (13, 5, 5, 'CARE-SHAMPOO-001', 'Daily Shampoo', 65, 6.30, 15, 'active'),
    (14, 5, 5, 'CARE-SOAP-001', 'Soap Bar Pack', 100, 3.10, 20, 'active'),
    (15, 5, 5, 'CARE-TOOTHPASTE-001', 'Toothpaste', 90, 2.70, 18, 'active')
ON CONFLICT (id) DO NOTHING;

INSERT INTO inventory_movements (id, product_id, movement_type, quantity, note)
SELECT id, id, 'purchase', stock, 'initial demo stock'
FROM products
WHERE id BETWEEN 1 AND 15
ON CONFLICT (id) DO NOTHING;

INSERT INTO market_orders (id, product_id, customer_email, quantity, status) VALUES
    (1, 1, 'customer01@example.test', 2, 'paid'),
    (2, 4, 'customer02@example.test', 1, 'packed'),
    (3, 7, 'customer03@example.test', 3, 'pending'),
    (4, 10, 'customer04@example.test', 1, 'shipped'),
    (5, 13, 'customer05@example.test', 2, 'paid')
ON CONFLICT (id) DO NOTHING;
