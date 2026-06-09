CREATE TABLE `user` (
    `id` int unsigned NOT NULL AUTO_INCREMENT COMMENT 'User ID',
    `passport` varchar(45) NOT NULL COMMENT 'User Passport',
    `password` varchar(45) NOT NULL COMMENT 'User Password',
    `nickname` varchar(45) NOT NULL COMMENT 'User Nickname',
    `create_at` datetime DEFAULT NULL COMMENT 'Created Time',
    `update_at` datetime DEFAULT NULL COMMENT 'Updated Time',
    `delete_at` datetime DEFAULT NULL COMMENT 'Deleted Time',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uniq_passport` (`passport`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
