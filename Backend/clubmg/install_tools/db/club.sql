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
-- Table structure for table `athlete_company`
--

DROP TABLE IF EXISTS `athlete_company`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `athlete_company` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `company_id` varchar(32) NOT NULL COMMENT '公司唯一ID',
  `company_name` varchar(64) NOT NULL COMMENT '单位名称',
  `author_rep` varchar(64) NOT NULL DEFAULT '' COMMENT '单位名称',
  `credit_code` varchar(128) NOT NULL DEFAULT '' COMMENT '统一社会信用代码',
  `company_addr` varchar(1024) NOT NULL DEFAULT '' COMMENT '单位地址',
  `contact` varchar(64) NOT NULL DEFAULT '' COMMENT '联系人',
  `contact_way` tinyint(2) NOT NULL DEFAULT '0' COMMENT '电话/手机',
  `context_info` varchar(64) NOT NULL DEFAULT '' COMMENT '联系方式',
  `state` tinyint(2) NOT NULL DEFAULT '0' COMMENT '删除标记',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '信息完善时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '信息更新时间',
  `deleted_at` datetime DEFAULT NULL COMMENT '删除时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `company_id_idx` (`company_id`),
  UNIQUE KEY `company_name_idx` (`company_name`),
  KEY `author_rep_idx` (`author_rep`),
  KEY `credit_code_idx` (`credit_code`)
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `athlete_group`
--

DROP TABLE IF EXISTS `athlete_group`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `athlete_group` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(64) NOT NULL COMMENT '运动员分组名称',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '信息完善时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '信息更新时间',
  `deleted_at` datetime DEFAULT NULL COMMENT '删除时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `name_idx` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=14 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `athlete_group_link`
--

DROP TABLE IF EXISTS `athlete_group_link`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `athlete_group_link` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `athlete_id` int(11) NOT NULL COMMENT '关联运动信息表主键 id',
  `group_id` int(11) NOT NULL COMMENT '关联运动分组表主键 id',
  PRIMARY KEY (`id`),
  UNIQUE KEY `athlete_id_group_id_idx` (`athlete_id`,`group_id`),
  KEY `athlete_id_idx` (`athlete_id`),
  KEY `group_id_idx` (`group_id`)
) ENGINE=InnoDB AUTO_INCREMENT=40 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `athlete_info`
--

DROP TABLE IF EXISTS `athlete_info`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `athlete_info` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `athlete_id` varchar(32) NOT NULL COMMENT '运动员唯一ID',
  `company_id` varchar(32) NOT NULL DEFAULT 'fb3cd64493f09deb788c20412c9263a1' COMMENT '关联运动员信息来源公司唯一 id(暂时无用)',
  `name` varchar(64) NOT NULL COMMENT '姓名',
  `english_name` varchar(64) NOT NULL COMMENT '英文名字',
  `gender` tinyint(4) NOT NULL DEFAULT '0' COMMENT '性别',
  `profile_photo` varchar(128) NOT NULL DEFAULT 'static/img/athlete/default-photo.jpg' COMMENT '运动员头像',
  `nationality` varchar(32) NOT NULL COMMENT '国籍',
  `native_place` varchar(255) NOT NULL DEFAULT '' COMMENT '籍贯',
  `folk` varchar(32) NOT NULL DEFAULT '汉族' COMMENT '民族',
  `birthday` datetime DEFAULT NULL COMMENT '出生日期',
  `sport_project` varchar(32) NOT NULL COMMENT '运动项目',
  `hand_held` tinyint(4) NOT NULL DEFAULT '0' COMMENT '持拍手',
  `sport_level` tinyint(4) NOT NULL COMMENT '运动等级',
  `initial_training_time` datetime DEFAULT NULL COMMENT '初始训练时间',
  `first_coach` varchar(64) NOT NULL DEFAULT '' COMMENT '启蒙教练',
  `pro_team_coach` varchar(64) NOT NULL DEFAULT '' COMMENT '省队教练',
  `nat_team_coach` varchar(64) NOT NULL DEFAULT '' COMMENT '国家队教练',
  `state` tinyint(2) NOT NULL DEFAULT '0' COMMENT '删除标记',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '信息完善时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '信息更新时间',
  `deleted_at` datetime DEFAULT NULL COMMENT '信息删除时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `athlete_id` (`athlete_id`),
  KEY `company_id_idx` (`company_id`),
  KEY `name_idx` (`name`),
  KEY `english_name_idx` (`english_name`)
) ENGINE=InnoDB AUTO_INCREMENT=38 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `auth_group`
--

DROP TABLE IF EXISTS `auth_group`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_group` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(80) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `auth_group_permissions`
--

DROP TABLE IF EXISTS `auth_group_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_group_permissions` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `group_id` int(11) NOT NULL,
  `permission_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_group_permissions_group_id_permission_id_0cd325b0_uniq` (`group_id`,`permission_id`),
  KEY `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` (`permission_id`),
  CONSTRAINT `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_group_permissions_group_id_b120cbf9_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `auth_permission`
--

DROP TABLE IF EXISTS `auth_permission`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_permission` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `content_type_id` int(11) NOT NULL,
  `codename` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_permission_content_type_id_codename_01ab375a_uniq` (`content_type_id`,`codename`),
  CONSTRAINT `auth_permission_content_type_id_2f476e4b_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=28 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `django_admin_log`
--

DROP TABLE IF EXISTS `django_admin_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `django_admin_log` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `action_time` datetime(6) NOT NULL,
  `object_id` longtext,
  `object_repr` varchar(200) NOT NULL,
  `action_flag` smallint(5) unsigned NOT NULL,
  `change_message` longtext NOT NULL,
  `content_type_id` int(11) DEFAULT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `django_admin_log_content_type_id_c4bce8eb_fk_django_co` (`content_type_id`),
  KEY `django_admin_log_user_id_c564eba6_fk_user_exp_id` (`user_id`),
  CONSTRAINT `django_admin_log_content_type_id_c4bce8eb_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`),
  CONSTRAINT `django_admin_log_user_id_c564eba6_fk_user_exp_id` FOREIGN KEY (`user_id`) REFERENCES `user_exp` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `django_content_type`
--

DROP TABLE IF EXISTS `django_content_type`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `django_content_type` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `app_label` varchar(100) NOT NULL,
  `model` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `django_content_type_app_label_model_76bd3d3b_uniq` (`app_label`,`model`)
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `django_migrations`
--

DROP TABLE IF EXISTS `django_migrations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `django_migrations` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `app` varchar(255) NOT NULL,
  `name` varchar(255) NOT NULL,
  `applied` datetime(6) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=16 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `django_session`
--

DROP TABLE IF EXISTS `django_session`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `django_session` (
  `session_key` varchar(40) NOT NULL,
  `session_data` longtext NOT NULL,
  `expire_date` datetime(6) NOT NULL,
  PRIMARY KEY (`session_key`),
  KEY `django_session_expire_date_a5c62663` (`expire_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `group_permission`
--

DROP TABLE IF EXISTS `group_permission`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `group_permission` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `group_id` int(11) NOT NULL COMMENT '关联用户组id',
  `permission_id` int(11) NOT NULL COMMENT '关联权限id',
  PRIMARY KEY (`id`),
  UNIQUE KEY `group_id_permission_id_idx` (`group_id`,`permission_id`),
  KEY `permission_id_idx` (`permission_id`)
) ENGINE=InnoDB AUTO_INCREMENT=61 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `group_resource`
--

DROP TABLE IF EXISTS `group_resource`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `group_resource` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `group_id` int(11) NOT NULL COMMENT '关联用户组id',
  `resource_type` varchar(20) NOT NULL COMMENT '资源类型',
  `resource_id` int(11) NOT NULL COMMENT '对应资源的主键id',
  PRIMARY KEY (`id`),
  UNIQUE KEY `group_id_resource_type_resource_id_idx` (`group_id`,`resource_type`,`resource_id`),
  KEY `resource_type_idx` (`resource_type`)
) ENGINE=InnoDB AUTO_INCREMENT=209 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `groups`
--

DROP TABLE IF EXISTS `groups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `groups` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(20) NOT NULL COMMENT '组名',
  PRIMARY KEY (`id`),
  UNIQUE KEY `name_idx` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=22 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `history_data`
--

DROP TABLE IF EXISTS `history_data`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `history_data` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `module_id` varchar(32) NOT NULL COMMENT '对应唯一模块 id',
  `module_name` varchar(32) NOT NULL COMMENT '对应唯一模块名称',
  `data_path` varchar(128) NOT NULL COMMENT '历史数据根目录',
  PRIMARY KEY (`id`),
  UNIQUE KEY `module_id_idx` (`module_id`),
  UNIQUE KEY `module_name_idx` (`module_name`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `match_info`
--

DROP TABLE IF EXISTS `match_info`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `match_info` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `match_id` varchar(32) NOT NULL COMMENT '赛事ID',
  `level1` varchar(32) NOT NULL DEFAULT '' COMMENT '赛事级别1',
  `level2` varchar(32) NOT NULL DEFAULT '' COMMENT '赛事级别2',
  `match_type` tinyint(2) NOT NULL DEFAULT '0' COMMENT '比赛类型男单/女单/男双/女双/混双',
  `match_name` varchar(128) NOT NULL COMMENT '赛事名称',
  `match_date` datetime DEFAULT NULL COMMENT '赛事时间',
  `player_a` varchar(32) NOT NULL COMMENT '比赛球员A, 双打的话用空格隔开两个运动员',
  `player_a_id` varchar(128) NOT NULL COMMENT '球员A球员id, 双打的话用空格隔开两个运动员id',
  `player_b` varchar(32) NOT NULL COMMENT '比赛球员B, 双打的话用空格隔开两个运动员',
  `player_b_id` varchar(128) NOT NULL COMMENT '球员B球员id, 双打的话用空格隔开两个运动员id',
  `winnum_a` tinyint(4) NOT NULL DEFAULT '0' COMMENT '赛事球员A总得分',
  `winnum_b` tinyint(4) NOT NULL DEFAULT '0' COMMENT '赛事球员B总得分',
  `match_result` tinyint(2) NOT NULL COMMENT '球员A对球员B胜负结果(1: 胜, 2: 负)',
  `match_round` varchar(32) NOT NULL DEFAULT '' COMMENT '比赛回合',
  `memo` varchar(2048) NOT NULL DEFAULT '' COMMENT '备注信息',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '信息完善时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '信息更新时间',
  `deleted_at` datetime DEFAULT NULL COMMENT '信息删除时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `match_id_idx` (`match_id`),
  KEY `match_name_idx` (`match_name`),
  KEY `player_a_idx` (`player_a`),
  KEY `player_b_idx` (`player_b`),
  KEY `player_a_id_idx` (`player_a_id`),
  KEY `player_b_id_idx` (`player_b_id`)
) ENGINE=InnoDB AUTO_INCREMENT=21 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `match_videos`
--

DROP TABLE IF EXISTS `match_videos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `match_videos` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `match_id` varchar(32) NOT NULL COMMENT '关联 match_info 表 match_id 赛事ID',
  `match_round` tinyint(4) NOT NULL COMMENT '比赛局数',
  `score` tinyint(4) NOT NULL COMMENT '总分',
  `score_a` tinyint(4) NOT NULL COMMENT '球员A得分',
  `score_b` tinyint(4) NOT NULL COMMENT '球员B得分',
  `video` varchar(128) NOT NULL COMMENT '赛事视频',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '信息完善时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '信息更新时间',
  `deleted_at` datetime DEFAULT NULL COMMENT '信息删除时间',
  PRIMARY KEY (`id`),
  KEY `match_id_idx` (`match_id`),
  KEY `video_idx` (`video`)
) ENGINE=InnoDB AUTO_INCREMENT=504 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

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
-- Table structure for table `permission`
--

DROP TABLE IF EXISTS `permission`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `permission` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(20) NOT NULL COMMENT '权限名称',
  PRIMARY KEY (`id`),
  UNIQUE KEY `name_idx` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `physical_fitness_data`
--

DROP TABLE IF EXISTS `physical_fitness_data`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `physical_fitness_data` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `fitness_item_id` varchar(32) NOT NULL COMMENT '身体素质类型名称编号关联, physical_fitness_items 表 item_id 列',
  `fitness_test_date` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '测试时间',
  `fitness_test_value` float(12,4) NOT NULL COMMENT '测试数据',
  `athlete_id` varchar(32) NOT NULL COMMENT '运动员编号, 关联 athlete_info 表 athlete_id 列',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '信息完善时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '信息更新时间',
  `deleted_at` datetime DEFAULT NULL COMMENT '信息删除时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `athlete_id_test_date_item_id_idx` (`athlete_id`,`fitness_item_id`,`fitness_test_date`),
  KEY `fitness_item_id_idx` (`fitness_item_id`)
) ENGINE=InnoDB AUTO_INCREMENT=18 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

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
-- Table structure for table `rpt_hits`
--

DROP TABLE IF EXISTS `rpt_hits`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `rpt_hits` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `matchid` varchar(255) DEFAULT NULL,
  `frame_hit` int(11) NOT NULL,
  `frame_prev` int(11) NOT NULL,
  `frame_next` int(11) NOT NULL,
  `action` varchar(255) NOT NULL,
  `player` varchar(255) DEFAULT NULL,
  `zone_start` int(11) NOT NULL,
  `height` int(11) NOT NULL,
  `zone_end` int(11) NOT NULL,
  `video` varchar(255) DEFAULT NULL,
  `route` varchar(255) DEFAULT NULL,
  `operator` varchar(50) DEFAULT NULL,
  `oper_time` datetime(6) DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=18451 DEFAULT CHARSET=utf8mb4 ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `rpt_scores`
--

DROP TABLE IF EXISTS `rpt_scores`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `rpt_scores` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `matchid` varchar(255) DEFAULT NULL,
  `game` varchar(255) DEFAULT NULL,
  `score` int(11) NOT NULL,
  `score_a` int(11) NOT NULL,
  `score_b` int(11) NOT NULL,
  `a1num` varchar(255) DEFAULT NULL,
  `a2num` varchar(255) DEFAULT NULL,
  `serve` varchar(255) DEFAULT NULL,
  `goal` varchar(255) DEFAULT NULL,
  `frame_start` int(11) NOT NULL,
  `frame_end` int(11) NOT NULL,
  `duration` int(11) NOT NULL,
  `updown` varchar(255) DEFAULT NULL,
  `video` varchar(255) DEFAULT NULL,
  `route` varchar(255) DEFAULT NULL,
  `operator` varchar(50) DEFAULT NULL,
  `oper_time` datetime(6) DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=1901 DEFAULT CHARSET=utf8mb4 ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `sport_event_exp`
--

DROP TABLE IF EXISTS `sport_event_exp`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `sport_event_exp` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `sport_event_id` varchar(32) NOT NULL COMMENT '赛事唯一ID',
  `athlete_id` varchar(32) NOT NULL COMMENT '关联运动员唯一id',
  `event_name` varchar(64) NOT NULL COMMENT '赛事名称',
  `event_type` tinyint(2) NOT NULL DEFAULT '0' COMMENT '国内/国外',
  `event_time` datetime DEFAULT NULL COMMENT '赛事时间',
  `rank` varchar(64) NOT NULL DEFAULT '' COMMENT '赛事名次(成绩)',
  `rank_info` varchar(2048) DEFAULT '' COMMENT '赛事数据',
  `event_honor` varchar(2048) DEFAULT '' COMMENT '荣誉/奖励',
  `event_honor_img01` varchar(128) NOT NULL DEFAULT 'static/img/honor/default-honor.jpg' COMMENT '荣誉图片01',
  `event_honor_img02` varchar(128) NOT NULL DEFAULT 'static/img/honor/default-honor.jpg' COMMENT '荣誉图片02',
  `event_honor_img03` varchar(128) NOT NULL DEFAULT 'static/img/honor/default-honor.jpg' COMMENT '荣誉图片03',
  `state` tinyint(2) NOT NULL DEFAULT '0' COMMENT '删除标记',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '信息完善时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '信息更新时间',
  `deleted_at` datetime DEFAULT NULL COMMENT '信息删除时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `sport_event_id` (`sport_event_id`),
  KEY `athlete_id_idx` (`athlete_id`),
  KEY `event_name_idx` (`event_name`)
) ENGINE=InnoDB AUTO_INCREMENT=29 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `user_exp`
--

DROP TABLE IF EXISTS `user_exp`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `user_exp` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `password` varchar(128) NOT NULL,
  `last_login` datetime(6) DEFAULT NULL,
  `is_superuser` tinyint(1) NOT NULL,
  `username` varchar(150) NOT NULL,
  `first_name` varchar(30) NOT NULL,
  `last_name` varchar(30) NOT NULL,
  `email` varchar(254) NOT NULL,
  `is_staff` tinyint(1) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `date_joined` datetime(6) NOT NULL,
  `user_type` int(11) NOT NULL,
  `profile_photo` varchar(128) NOT NULL DEFAULT 'static/img/profilephoto/default-user.png',
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB AUTO_INCREMENT=14 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `user_exp_groups`
--

DROP TABLE IF EXISTS `user_exp_groups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `user_exp_groups` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `group_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_exp_groups_user_id_group_id_99770061_uniq` (`user_id`,`group_id`),
  KEY `user_exp_groups_group_id_f85257a6_fk_auth_group_id` (`group_id`),
  CONSTRAINT `user_exp_groups_group_id_f85257a6_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`),
  CONSTRAINT `user_exp_groups_user_id_2b0d00c2_fk_user_exp_id` FOREIGN KEY (`user_id`) REFERENCES `user_exp` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `user_exp_user_permissions`
--

DROP TABLE IF EXISTS `user_exp_user_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `user_exp_user_permissions` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `permission_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_exp_user_permissions_user_id_permission_id_7388e627_uniq` (`user_id`,`permission_id`),
  KEY `user_exp_user_permis_permission_id_89058658_fk_auth_perm` (`permission_id`),
  CONSTRAINT `user_exp_user_permis_permission_id_89058658_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `user_exp_user_permissions_user_id_879e29c2_fk_user_exp_id` FOREIGN KEY (`user_id`) REFERENCES `user_exp` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `user_group`
--

DROP TABLE IF EXISTS `user_group`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `user_group` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL COMMENT '关联用户id',
  `group_id` int(11) NOT NULL COMMENT '关联组id',
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id_group_id_idx` (`user_id`,`group_id`),
  KEY `goup_id_idx` (`group_id`)
) ENGINE=InnoDB AUTO_INCREMENT=285 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `video_proc_info`
--

DROP TABLE IF EXISTS `video_proc_info`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `video_proc_info` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `match_id` varchar(32) NOT NULL COMMENT '赛事ID',
  `task_id` varchar(64) NOT NULL COMMENT '当前 celery task id',
  `tb_name` varchar(32) NOT NULL COMMENT '当前任务处理的表名(hits|scores)',
  `init` tinyint(1) NOT NULL DEFAULT '0' COMMENT '任务是否初始化完成(0:未完成|1:完成)',
  `state` tinyint(4) NOT NULL DEFAULT '0' COMMENT '当前状态',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '信息录入时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '信息更新时间',
  `deleted_at` datetime DEFAULT NULL COMMENT '信息删除时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `match_id_tb_name_idx` (`match_id`,`tb_name`),
  UNIQUE KEY `task_id_idx` (`task_id`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `world_ranking`
--

DROP TABLE IF EXISTS `world_ranking`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `world_ranking` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `match_type` tinyint(4) NOT NULL COMMENT '比赛类型(男单/女单/男双/女双/混双)',
  `athlete_id` varchar(128) NOT NULL COMMENT '运动员id(双打时是两个id,用空格分隔)',
  `ranking_last_week` tinyint(4) NOT NULL COMMENT '上周排名',
  `ranking_this_week` tinyint(4) NOT NULL COMMENT '本周排名',
  `ranking_change` tinyint(4) NOT NULL COMMENT '排名变化(升/降/-)',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '信息完善时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '信息更新时间',
  `deleted_at` datetime DEFAULT NULL COMMENT '信息删除时间',
  PRIMARY KEY (`id`),
  KEY `athlete_id_idx` (`athlete_id`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2019-05-13 14:01:57
