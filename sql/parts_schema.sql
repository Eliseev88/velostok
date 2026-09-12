-- Запчасти для велосипедов с velosklad.ru.
-- Отдельные таблицы: структура похожа на bikes, но у запчастей нет года,
-- класса, пола и ростовок, зато есть категория из хлебных крошек.
-- Применение: mysql -u root velostok < sql/parts_schema.sql

CREATE TABLE IF NOT EXISTS parts (
  id            BIGINT       NOT NULL PRIMARY KEY,
  url           VARCHAR(512) NOT NULL,
  name          VARCHAR(512) NULL,
  brand         VARCHAR(128) NULL,
  model         VARCHAR(255) NULL,
  sku           VARCHAR(64)  NULL,
  category      VARCHAR(128) NULL,
  subcategory   VARCHAR(128) NULL,
  price         DECIMAL(10,2) NULL,
  old_price     DECIMAL(10,2) NULL,
  discount_pct  TINYINT UNSIGNED NULL,
  currency      CHAR(3)      NULL,
  availability  ENUM('in_stock','out_of_stock','preorder','unknown')
                NOT NULL DEFAULT 'unknown',
  description   TEXT         NULL,
  main_image    VARCHAR(512) NULL,
  parsed_at     DATETIME     NULL,
  created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY idx_brand (brand),
  KEY idx_price (price),
  KEY idx_availability (availability),
  KEY idx_category (category, subcategory)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS part_specs (
  part_id  BIGINT NOT NULL,
  position SMALLINT UNSIGNED NOT NULL,
  name     VARCHAR(128) NOT NULL,
  value    TEXT NULL,
  PRIMARY KEY (part_id, position),
  KEY idx_name (name),
  CONSTRAINT fk_pspecs_part FOREIGN KEY (part_id) REFERENCES parts(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS part_images (
  part_id  BIGINT NOT NULL,
  position SMALLINT UNSIGNED NOT NULL,
  url      VARCHAR(512) NOT NULL,
  is_main  BOOLEAN NOT NULL DEFAULT FALSE,
  PRIMARY KEY (part_id, position),
  CONSTRAINT fk_pimages_part FOREIGN KEY (part_id) REFERENCES parts(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Очередь обхода запчастей. Отдельная от crawl_queue: ID запчастей и
-- велосипедов живут в разных пространствах и в принципе могут совпасть.
CREATE TABLE IF NOT EXISTS parts_queue (
  part_id     BIGINT       NOT NULL PRIMARY KEY,
  url         VARCHAR(512) NOT NULL,
  status      ENUM('pending','fetched','parsed','failed','not_found')
              NOT NULL DEFAULT 'pending',
  attempts    TINYINT UNSIGNED NOT NULL DEFAULT 0,
  http_status SMALLINT UNSIGNED NULL,
  error       TEXT NULL,
  fetched_at  DATETIME NULL,
  updated_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
