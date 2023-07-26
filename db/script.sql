CREATE TABLE `Users` (
  `id` int PRIMARY KEY AUTO_INCREMENT,
  `name` varchar(255) UNIQUE NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `password_salt` varchar(255) NOT NULL,
  `email` varchar(255) UNIQUE NOT NULL
);

CREATE TABLE `Sensors` (
  `id` int PRIMARY KEY AUTO_INCREMENT,
  `name` varchar(255) UNIQUE NOT NULL
);

CREATE TABLE `Sensor_Data` (
  `id` int PRIMARY KEY AUTO_INCREMENT,
  `sensor_id` int,
  `value` float NOT NULL DEFAULT 0,
  `createdAt` DATETIME NOT NULL
);

CREATE TABLE `Scale` (
  `id` int PRIMARY KEY AUTO_INCREMENT,
  `weight` float NOT NULL DEFAULT 0,
  `imc` float NOT NULL DEFAULT 0,
  `fat` float NOT NULL DEFAULT 0,
  `sub_fat` float NOT NULL DEFAULT 0,
  `visc_fat` float NOT NULL DEFAULT 0,
  `water` float NOT NULL DEFAULT 0,
  `muscle_skeleton` float NOT NULL DEFAULT 0,
  `mass_skeleton` float NOT NULL DEFAULT 0,
  `protein` float NOT NULL DEFAULT 0,
  `tmb` int NOT NULL DEFAULT 0,
  `age` int NOT NULL DEFAULT 0,
  `createdAt` DATETIME NOT NULL,
  `id_user` int
);

ALTER TABLE `Sensor_Data` ADD FOREIGN KEY (`sensor_id`) REFERENCES `Sensors` (`id`);

ALTER TABLE `Scale` ADD FOREIGN KEY (`id_user`) REFERENCES `Users` (`id`);
