-- MySQL dump 10.13  Distrib 5.6.29, for Linux (x86_64)
--
-- Host: 127.0.0.1    Database: club
-- ------------------------------------------------------
-- Server version	5.6.29-log

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `operation_permission`
--

DROP TABLE IF EXISTS `operation_permission`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `operation_permission` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `permission_id` int(11) NOT NULL COMMENT '关联权限表id',
  `operation_id` int(11) NOT NULL COMMENT '关联操作表id',
  PRIMARY KEY (`id`),
  UNIQUE KEY `operation_id_permission_id_idx` (`permission_id`,`operation_id`),
  KEY `permission_id_idx` (`operation_id`)
) ENGINE=InnoDB AUTO_INCREMENT=42 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `operation_permission`
--

LOCK TABLES `operation_permission` WRITE;
/*!40000 ALTER TABLE `operation_permission` DISABLE KEYS */;
INSERT INTO `operation_permission` VALUES (26,1,1),(27,1,2),(1,1,8),(2,1,9),(3,1,18),(28,2,1),(29,2,2),(4,2,6),(5,2,7),(6,2,8),(7,2,10),(8,2,17),(9,2,19),(30,3,1),(31,3,2),(10,3,6),(11,3,7),(12,3,17),(32,4,1),(33,4,2),(13,4,6),(14,4,7),(15,4,11),(16,4,17),(17,4,20);
/*!40000 ALTER TABLE `operation_permission` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2019-05-13 14:11:13
