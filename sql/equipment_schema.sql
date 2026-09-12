-- Экипировка для велосипедистов с velosklad.ru.
-- Структура совпадает с запчастями: на сайте это соседние разделы одного
-- каталога с общим пространством ID и одинаковым набором полей.
-- Применение: mysql -u root velostok < sql/equipment_schema.sql

CREATE TABLE IF NOT EXISTS equipment (
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

CREATE TABLE IF NOT EXISTS equipment_specs (
  equipment_id BIGINT NOT NULL,
  position     SMALLINT UNSIGNED NOT NULL,
  name         VARCHAR(128) NOT NULL,
  value        TEXT NULL,
  PRIMARY KEY (equipment_id, position),
  KEY idx_name (name),
  CONSTRAINT fk_especs_eq FOREIGN KEY (equipment_id) REFERENCES equipment(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS equipment_images (
  equipment_id BIGINT NOT NULL,
  position     SMALLINT UNSIGNED NOT NULL,
  url          VARCHAR(512) NOT NULL,
  is_main      BOOLEAN NOT NULL DEFAULT FALSE,
  PRIMARY KEY (equipment_id, position),
  CONSTRAINT fk_eimages_eq FOREIGN KEY (equipment_id) REFERENCES equipment(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS equipment_queue (
  equipment_id BIGINT       NOT NULL PRIMARY KEY,
  url          VARCHAR(512) NOT NULL,
  status       ENUM('pending','fetched','parsed','failed','not_found')
               NOT NULL DEFAULT 'pending',
  attempts     TINYINT UNSIGNED NOT NULL DEFAULT 0,
  http_status  SMALLINT UNSIGNED NULL,
  error        TEXT NULL,
  fetched_at   DATETIME NULL,
  updated_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
