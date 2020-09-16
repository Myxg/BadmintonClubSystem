-- MySQL dump 10.13  Distrib 5.7.24, for Linux (x86_64)
--
-- Host: 127.0.0.1    Database: club
-- ------------------------------------------------------
-- Server version	5.7.24

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
) ENGINE=InnoDB AUTO_INCREMENT=43 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `history_data`
--

LOCK TABLES `history_data` WRITE;
/*!40000 ALTER TABLE `history_data` DISABLE KEYS */;
INSERT INTO `history_data` VALUES (1,'TrainingPlan','训练计划','TrainingPlan'),(2,'TrainingMonitor','训练监控','TrainingMonitor'),(9,'Videoinfo','原始视频','Videoinfo'),(10,'InternalRanking','内部排名','InternalRanking'),(11,'SelectionMethod','选举办法','SelectionMethod'),(12,'SelectionStandard','选拔标准','SelectionStandard'),(13,'PointCalculate','积分计算','PointCalculate'),(14,'DeterminProc','入选确定程序','DeterminProc'),(15,'AgainstPlan','对阵表','AgainstPlan'),(16,'GameResult','比赛结果','GameResult'),(17,'InjuryInvest','伤病情况调查','InjuryInvest'),(18,'TreatmentPlan','治疗方案及效果','TreatmentPlan'),(19,'TrainingProgram','康复训练计划及效果','TrainingProgram'),(20,'DiningStatistics','就餐统计','DiningStatistics'),(21,'BodyMonitor','体脂监测','BodyMonitor'),(22,'ProjectEstablish','立项申报书','ProjectEstablish'),(23,'ProjectManage','项目管理','ProjectManage'),(24,'AssessmentReport','评估报告','AssessmentReport'),(25,'SportmanSummary','运动员','SportmanSummary'),(26,'CoachSummary','教练','CoachSummary'),(27,'ResearchSummary','科研','ResearchSummary'),(28,'MedicalSummary','医务','MedicalSummary'),(29,'PhysicalSummary','体能','PhysicalSummary'),(30,'OpponentInfo','对手备战信息','OpponentInfo'),(31,'RuleChange','规则变化','RuleChange'),(32,'TechnologyTrack','技术追踪','TechnologyTrack'),(33,'AnalysisReport','分析报告','AnalysisReport'),(34,'ImproveMeasures','改进措施','ImproveMeasures'),(35,'EvaluationFeedback','评估反馈','EvaluationFeedback'),(36,'WeekPlan','周计划','WeekPlan'),(37,'QuarterPlan','季度计划','QuarterPlan'),(38,'YearPlan','年度计划','YearPlan'),(39,'PhasePlan','阶段计划','PhasePlan'),(40,'PlanChange','计划变更','PlanChange'),(41,'SportmanAttendance','运动员出勤率','SportmanAttendance'),(42,'TrainqualityScore','训练质量评分','TrainqualityScore');
/*!40000 ALTER TABLE `history_data` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2019-05-13 14:43:50
