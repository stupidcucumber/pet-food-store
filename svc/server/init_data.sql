CREATE TABLE IF NOT EXISTS products (
    product_id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_name VARCHAR(255) NOT NULL UNIQUE,
    product_description TEXT,
    quantity INTEGER DEFAULT 0,
    price DECIMAL(10, 2) NOT NULL,
    active BOOLEAN DEFAULT TRUE
);


INSERT OR IGNORE INTO products (product_name, product_description, quantity, price, active) VALUES
    ("Cat Indoor Basic", "For adult indoor cats with medium activity", 20, 150, true),
    ("Exotic Pet Blend", "For cats with sensitive digestion", 10, 230, false),
    ("Dog Puppy Start", "For puppies up to 1 year", 15, 200, true),
    ("Dog Senior Light", "For senior dogs, low calorie", 8, 220, true),
    ("Premium Dog Active", "For large active dogs", 12, 300, true),
    ("Small Breed Mix", "For small breed dogs", 18, 180, true),
    ("Cat Sensitive Care", "For small exotic pets", 5, 400, true);
