CREATE TABLE `news_picture` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `news_id` bigint(18) DEFAULT NULL,
  `url` varchar(300) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `order` smallint(6) DEFAULT 0,
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP,
  `create_by` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `update_time` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `update_by` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;