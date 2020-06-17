#json解析函数
DELIMITER $$
DROP FUNCTION IF EXISTS `json_extract_c`$$
CREATE FUNCTION `json_extract_c`(
details TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
required_field VARCHAR (255)
) RETURNS text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
BEGIN
SET details = SUBSTRING_INDEX(details, "{", -1);
SET details = SUBSTRING_INDEX(details, "}", 1);
RETURN TRIM(
    BOTH '"' FROM SUBSTRING_INDEX(
       -- SUBSTRING_INDEX(
            SUBSTRING_INDEX(
                CONCAT('"":"",',details),
                CONCAT(
                    '"',
                    SUBSTRING_INDEX(required_field,'$.', -1),
                    '":'
                ),
                -1
            ),
            ',"',
            1
      /*  ),
        ':',
        -1
			*/
    )
) ;
END$$
DELIMITER ;