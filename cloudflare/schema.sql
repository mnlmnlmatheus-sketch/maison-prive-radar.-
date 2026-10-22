-- Maison Privé / D1 storage and indexed search (prototype; not deployed)
CREATE TABLE IF NOT EXISTS products (
 id TEXT PRIMARY KEY,
 name TEXT NOT NULL,
 brand TEXT NOT NULL DEFAULT '',
 shop TEXT NOT NULL DEFAULT '',
 category TEXT NOT NULL DEFAULT '',
 audience TEXT,
 color TEXT,
 volume_ml REAL,
 concentration TEXT,
 price_cents INTEGER NOT NULL CHECK(price_cents > 0),
 original_price_cents INTEGER,
 price_basis TEXT NOT NULL DEFAULT 'listed',
 url TEXT NOT NULL,
 image TEXT,
 checked_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS products_brand ON products(brand,id);
CREATE INDEX IF NOT EXISTS products_cat_price ON products(category,price_cents,id);
CREATE INDEX IF NOT EXISTS products_shop ON products(shop,id);
CREATE INDEX IF NOT EXISTS products_checked ON products(checked_at DESC,id);
CREATE INDEX IF NOT EXISTS products_price ON products(price_cents,id);
CREATE INDEX IF NOT EXISTS products_perfume ON products(concentration,volume_ml,id);
CREATE VIRTUAL TABLE IF NOT EXISTS products_fts USING fts5(name,brand,category,content='products',content_rowid='rowid',tokenize='unicode61 remove_diacritics 2');
CREATE TRIGGER IF NOT EXISTS products_ai AFTER INSERT ON products BEGIN
 INSERT INTO products_fts(rowid,name,brand,category) VALUES(new.rowid,new.name,new.brand,new.category);
END;
CREATE TRIGGER IF NOT EXISTS products_ad AFTER DELETE ON products BEGIN
 INSERT INTO products_fts(products_fts,rowid,name,brand,category) VALUES('delete',old.rowid,old.name,old.brand,old.category);
END;
CREATE TRIGGER IF NOT EXISTS products_au AFTER UPDATE ON products BEGIN
 INSERT INTO products_fts(products_fts,rowid,name,brand,category) VALUES('delete',old.rowid,old.name,old.brand,old.category);
 INSERT INTO products_fts(rowid,name,brand,category) VALUES(new.rowid,new.name,new.brand,new.category);
END;
