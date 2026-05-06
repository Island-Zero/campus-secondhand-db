PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS user (
    user_id TEXT PRIMARY KEY,
    user_name TEXT NOT NULL,
    phone TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS item (
    item_id TEXT PRIMARY KEY,
    item_name TEXT NOT NULL,
    category TEXT NOT NULL,
    price REAL NOT NULL CHECK (price >= 0),
    status INTEGER NOT NULL CHECK (status IN (0, 1)),
    seller_id TEXT NOT NULL,
    FOREIGN KEY (seller_id) REFERENCES user(user_id)
        ON UPDATE CASCADE ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS orders (
    order_id TEXT PRIMARY KEY,
    item_id TEXT NOT NULL UNIQUE,
    buyer_id TEXT NOT NULL,
    order_date TEXT NOT NULL,
    FOREIGN KEY (item_id) REFERENCES item(item_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (buyer_id) REFERENCES user(user_id)
        ON UPDATE CASCADE ON DELETE RESTRICT
);

CREATE TRIGGER IF NOT EXISTS orders_item_must_be_sold_insert
BEFORE INSERT ON orders
FOR EACH ROW
WHEN (SELECT status FROM item WHERE item_id = NEW.item_id) != 1
BEGIN
    SELECT RAISE(ABORT, 'ordered item status must be 1');
END;

CREATE TRIGGER IF NOT EXISTS orders_item_must_be_sold_update
BEFORE UPDATE OF item_id ON orders
FOR EACH ROW
WHEN (SELECT status FROM item WHERE item_id = NEW.item_id) != 1
BEGIN
    SELECT RAISE(ABORT, 'ordered item status must be 1');
END;

CREATE TRIGGER IF NOT EXISTS item_with_order_cannot_be_unsold
BEFORE UPDATE OF status ON item
FOR EACH ROW
WHEN NEW.status = 0
     AND EXISTS (SELECT 1 FROM orders WHERE item_id = NEW.item_id)
BEGIN
    SELECT RAISE(ABORT, 'item with order cannot be unsold');
END;

CREATE VIEW IF NOT EXISTS sold_item_view AS
SELECT item.item_name, orders.buyer_id
FROM item
JOIN orders ON orders.item_id = item.item_id
WHERE item.status = 1;

CREATE VIEW IF NOT EXISTS unsold_item_view AS
SELECT item_id, item_name, category, price, seller_id
FROM item
WHERE status = 0;

INSERT INTO user (user_id, user_name, phone) VALUES
('u001', 'ZhangSan', '13800000001'),
('u002', 'LiSi', '13800000002'),
('u003', 'WangWu', '13800000003'),
('u004', 'ZhaoLiu', '13800000004');

INSERT INTO item (item_id, item_name, category, price, status, seller_id) VALUES
('i001', 'CalculusBook', 'Book', 20, 0, 'u001'),
('i002', 'DeskLamp', 'DailyGoods', 35, 1, 'u002'),
('i003', 'Microcontroller', 'Electronics', 80, 0, 'u001'),
('i004', 'Chair', 'Furniture', 50, 1, 'u003'),
('i005', 'WaterBottle', 'DailyGoods', 15, 0, 'u004');

INSERT INTO orders (order_id, item_id, buyer_id, order_date) VALUES
('o001', 'i002', 'u001', '2024-05-01'),
('o002', 'i004', 'u002', '2024-05-03');
