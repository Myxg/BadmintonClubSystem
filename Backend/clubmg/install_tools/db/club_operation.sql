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
-- Table structure for table `operation`
--

DROP TABLE IF EXISTS `operation`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `operation` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(20) NOT NULL COMMENT '操作名称',
  `method` varchar(8) NOT NULL COMMENT '允许操作方法GET/PUT/POST/DELETE',
  `url` varchar(128) NOT NULL COMMENT '允许访问的 url',
  PRIMARY KEY (`id`),
  UNIQUE KEY `name_method_url_idx` (`name`,`method`,`url`)
) ENGINE=InnoDB AUTO_INCREMENT=21 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `operation`
--

LOCK TABLES `operation` WRITE;
/*!40000 ALTER TABLE `operation` DISABLE KEYS */;
INSERT INTO `operation` VALUES (2,'HEAD','HEAD','^.*$'),(1,'OPTIONS','OPTIONS','^.*$'),(20,'删除运动员赛事信息','DELETE','^athlete/sportevent/(?P<pk_id>[0-9]+)$'),(9,'录入运动员数据','PUT','^athlete/0$'),(14,'录入运动员来源公司数据','PUT','^athlete/company/0$'),(18,'录入运动员赛事信息','PUT','^athlete/sportevent/(?P<pk_id>[0-9]+)$'),(5,'更新用户数据','POST','^user/(?P<user_id>[0-9]+)$'),(11,'更新运动员数据','DELETE','^athlete/(?P<pk_id>[0-9]+)$'),(10,'更新运动员数据','POST','^athlete/(?P<pk_id>[0-9]+)$'),(16,'更新运动员来源公司数据','DELETE','^athlete/company/(?P<pk_id>[0-9]+)$'),(15,'更新运动员来源公司数据','POST','^athlete/company/(?P<pk_id>[0-9]+)$'),(19,'更新运动员赛事信息','POST','^athlete/sportevent/(?P<pk_id>[0-9]+)$'),(4,'获取单个用户数据','GET','^user/(?P<user_id>[0-9]+)$'),(7,'获取单个运动员数据','GET','^athlete/(?P<pk_id>[0-9]+)$'),(13,'获取单个运动员来源公司数据','GET','^athlete/company/(?P<pk_id>[0-9]+)$'),(3,'获取用户列表','GET','^users$'),(6,'获取运动员列表','GET','^athletes$'),(12,'获取运动员来源公司列表','GET','^athlete/companys$'),(8,'获取运动员来源公司列表(简单)','GET','^companylist$'),(17,'获取运动员赛事信息','GET','^athlete/sportevent/(?P<pk_id>[0-9]+)$');
/*!40000 ALTER TABLE `operation` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2019-05-13 14:09:48
