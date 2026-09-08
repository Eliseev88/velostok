-- Схема хранения карточек велосипедов, спарсенных с velosklad.ru
-- Применение: mysql -u root < sql/schema.sql

CREATE DATABASE IF NOT EXISTS velostok
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE velostok;

-- Очередь обхода. Она же механизм перезапуска: прогон всегда берёт
-- из неё только незавершённые строки, поэтому прерывание не теряет прогресс.
CREATE TABLE IF NOT EXISTS crawl_queue (
  bike_id     BIGINT       NOT NULL PRIMARY KEY,
  url         VARCHAR(512) NOT NULL,
  slug        VARCHAR(255) NULL,
  status      ENUM('pending','fetched','parsed','failed','not_found')
              NOT NULL DEFAULT 'pending',
  attempts    TINYINT UNSIGNED NOT NULL DEFAULT 0,
  http_status SMALLINT UNSIGNED NULL,
  error       TEXT NULL,
  fetched_at  DATETIME NULL,
  updated_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Основная карточка. PK — собственный ID товара на velosklad.ru:
-- он стабилен и присутствует в URL, поэтому суррогатный ключ не нужен.
CREATE TABLE IF NOT EXISTS bikes (
  id            BIGINT       NOT NULL PRIMARY KEY,
  url           VARCHAR(512) NOT NULL,
  slug          VARCHAR(255) NULL,
  name          VARCHAR(512) NULL,
  brand         VARCHAR(128) NULL,
  model         VARCHAR(255) NULL,
  year          SMALLINT UNSIGNED NULL,
  sku           VARCHAR(64)  NULL,
  price         DECIMAL(10,2) NULL,
  old_price     DECIMAL(10,2) NULL,
  discount_pct  TINYINT UNSIGNED NULL,
  currency      CHAR(3)      NULL,
  availability  ENUM('in_stock','out_of_stock','preorder','unknown')
                NOT NULL DEFAULT 'unknown',
  description   TEXT         NULL,
  class_name    VARCHAR(128) NULL,
  class_rank    TINYINT UNSIGNED NULL,
  class_max     TINYINT UNSIGNED NULL,
  -- Не короткий признак пола, а описательная фраза целиком:
  -- «детский для мальчиков и девочек от 5 до 9 лет».
  gender        VARCHAR(128) NULL,
  main_image    VARCHAR(512) NULL,
  parsed_at     DATETIME     NULL,
  created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY idx_brand (brand),
  KEY idx_price (price),
  KEY idx_availability (availability),
  KEY idx_year (year)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Характеристики хранятся как EAV: набор атрибутов заметно плавает
-- от товара к товару, под фиксированные колонки его не подвести.
CREATE TABLE IF NOT EXISTS bike_specs (
  bike_id    BIGINT NOT NULL,
  position   SMALLINT UNSIGNED NOT NULL,
  name       VARCHAR(128) NOT NULL,
  value      TEXT NULL,
  rank_label VARCHAR(128) NULL,
  PRIMARY KEY (bike_id, position),
  KEY idx_name (name),
  CONSTRAINT fk_specs_bike FOREIGN KEY (bike_id) REFERENCES bikes(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS bike_images (
  bike_id  BIGINT NOT NULL,
  position SMALLINT UNSIGNED NOT NULL,
  url      VARCHAR(512) NOT NULL,
  is_main  BOOLEAN NOT NULL DEFAULT FALSE,
  PRIMARY KEY (bike_id, position),
  CONSTRAINT fk_images_bike FOREIGN KEY (bike_id) REFERENCES bikes(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS bike_sizes (
  bike_id  BIGINT NOT NULL,
  position SMALLINT UNSIGNED NOT NULL,
  size     VARCHAR(64) NOT NULL,
  PRIMARY KEY (bike_id, position),
  CONSTRAINT fk_sizes_bike FOREIGN KEY (bike_id) REFERENCES bikes(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS bike_features (
  bike_id  BIGINT NOT NULL,
  position SMALLINT UNSIGNED NOT NULL,
  feature  VARCHAR(255) NOT NULL,
  PRIMARY KEY (bike_id, position),
  CONSTRAINT fk_features_bike FOREIGN KEY (bike_id) REFERENCES bikes(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
