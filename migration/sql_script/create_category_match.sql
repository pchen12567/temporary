CREATE TABLE `category_match` (
  `newsId` bigint(20) NOT NULL,
  `oldCategory` varchar(16) DEFAULT NULL,
  `title` varchar(2000) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `tags` varchar(500) DEFAULT NULL,
  `category` char(2) DEFAULT NULL COMMENT 'MI->"market index", BP -> "bunker price", IR -> "industry report"',
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP,
  `create_by` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `update_time` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `update_by` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`newsId`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='MOL新闻数据类别匹配表';