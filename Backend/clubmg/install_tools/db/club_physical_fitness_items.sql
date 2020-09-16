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
-- Table structure for table `physical_fitness_items`
--

DROP TABLE IF EXISTS `physical_fitness_items`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `physical_fitness_items` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `item_level1` varchar(32) NOT NULL COMMENT '身体素质一级分类名称',
  `item_name` varchar(32) NOT NULL COMMENT '身体素质类型名称',
  `item_id` varchar(32) NOT NULL COMMENT '身体素质类型名称编号',
  `unit` varchar(8) NOT NULL DEFAULT '' COMMENT '单位',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '信息完善时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '信息更新时间',
  `deleted_at` datetime DEFAULT NULL COMMENT '信息删除时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `item_id_idx` (`item_id`),
  KEY `item_name_idx` (`item_name`)
) ENGINE=InnoDB AUTO_INCREMENT=34 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `physical_fitness_items`
--

LOCK TABLES `physical_fitness_items` WRITE;
/*!40000 ALTER TABLE `physical_fitness_items` DISABLE KEYS */;
INSERT INTO `physical_fitness_items` VALUES (1,'基础体能','卧推','C001','公斤','2019-02-21 18:30:52','2019-02-21 18:30:52',NULL),(2,'基础体能','400米x5(平均成绩)','C009','秒','2019-02-21 18:30:52','2019-02-21 18:30:52',NULL),(3,'基础体能','立定跳远','C015','米','2019-02-21 18:30:52','2019-02-21 18:30:52',NULL),(4,'基础体能','4000米','C017','秒','2019-02-21 18:30:52','2019-02-21 18:30:52',NULL),(5,'FMS测试','深蹲','C101','','2019-02-21 18:30:52','2019-02-21 18:30:52',NULL),(6,'FMS测试','跨栏步(左)','C102','','2019-02-21 18:30:52','2019-02-21 18:30:52',NULL),(7,'FMS测试','跨栏步(右)','C103','','2019-02-21 18:30:52','2019-02-21 18:30:52',NULL),(8,'FMS测试','直线弓步(左)','C104','','2019-02-21 18:30:53','2019-02-21 18:30:53',NULL),(9,'FMS测试','直线弓步(右)','C105','','2019-02-21 18:30:53','2019-02-21 18:30:53',NULL),(10,'FMS测试','肩关节灵活性(左)','C106','','2019-02-21 18:30:53','2019-02-21 18:30:53',NULL),(11,'FMS测试','肩关节灵活性(右)','C107','','2019-02-21 18:30:53','2019-02-21 18:30:53',NULL),(12,'FMS测试','直腿上抬(左)','C108','','2019-02-21 18:30:53','2019-02-21 18:30:53',NULL),(13,'FMS测试','直腿上抬(右)','C109','','2019-02-21 18:30:53','2019-02-21 18:30:53',NULL),(14,'FMS测试','躯干撑起','C110','','2019-02-21 18:30:53','2019-02-21 18:30:53',NULL),(15,'FMS测试','旋转稳定性(左)','C111','','2019-02-21 18:30:53','2019-02-21 18:30:53',NULL),(16,'FMS测试','旋转稳定性(右)','C112','','2019-02-21 18:30:53','2019-02-21 18:30:53',NULL),(17,'生理生化','白细胞','C201','','2019-02-21 18:30:53','2019-02-21 18:30:53',NULL),(18,'生理生化','红细胞','C202','','2019-02-21 18:30:53','2019-02-21 18:30:53',NULL),(19,'生理生化','血红蛋白','C203','','2019-02-21 18:30:53','2019-02-21 18:30:53',NULL),(20,'生理生化','血球压积','C204','','2019-02-21 18:30:53','2019-02-21 18:30:53',NULL),(21,'生理生化','肌酸激酶','C205','','2019-02-21 18:30:53','2019-02-21 18:30:53',NULL),(22,'生理生化','血尿素','C206','','2019-02-21 18:30:53','2019-02-21 18:30:53',NULL),(23,'生理生化','睾酮','C207','','2019-02-21 18:30:53','2019-02-21 18:30:53',NULL),(24,'生理生化','皮质醇','C208','','2019-02-21 18:30:53','2019-02-21 18:30:53',NULL),(25,'基础体能','引体向上','C022','次','2019-02-21 18:30:54','2019-02-21 18:30:54',NULL),(26,'基础体能','原地二级跳左','C026','米','2019-02-21 18:30:54','2019-02-21 18:30:54',NULL),(27,'基础体能','原地二级跳右','C027','米','2019-02-21 18:30:54','2019-02-21 18:30:54',NULL),(28,'FMS测试','闭眼单腿平衡30秒(左)','C113','','2019-02-21 18:30:54','2019-02-21 18:30:54',NULL),(29,'FMS测试','闭眼单腿平衡30秒(右)','C114','','2019-02-21 18:30:54','2019-02-21 18:30:54',NULL),(30,'FMS测试','肩关节右上','C115','','2019-02-21 18:30:54','2019-02-21 18:30:54',NULL),(31,'FMS测试','肩关节右下','C116','','2019-02-21 18:30:54','2019-02-21 18:30:54',NULL),(32,'FMS测试','坐姿体前屈','C117','','2019-02-21 18:30:54','2019-02-21 18:30:54',NULL),(33,'基础体能','深蹲','C032','公斤','2019-02-21 18:30:55','2019-02-21 18:30:55',NULL);
/*!40000 ALTER TABLE `physical_fitness_items` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2019-05-13 14:11:48
