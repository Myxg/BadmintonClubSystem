#coding: utf-8

from __future__ import unicode_literals

import time
import os
import shutil
from functools import partial

from celery import shared_task
import logging

from django.conf import settings
from .models import RptHits, RptScores, VideoProcInfo
from common.aws_s3 import (get_object_key, download_object_from_s3 as download,
                     upload_object_to_s3 as upload, copy_boject, object_exist)
from .video_proc import VideoProcess, merge_video_from_multi_video, conv_video

LOG = logging.getLogger(__file__)

@shared_task(track_started=True)
def add(x, y):
    LOG.info("x: {}, y: {}".format(x, y))
    time.sleep(100)
    return x + y

def log_format(log_prefix, log):
    return "{} {}".format(log_prefix, log)

class VideoProcState(object):

    def __init__(self, match_id, tb_name):
        self.match_id = match_id
        self.tb_name = tb_name
        self.video_proc_info = None

    @property
    def state(self):
        if self.video_proc_info:
            return self.video_proc_info.state
        else:
            return -1

    @state.setter
    def state(self, state):
        if self.video_proc_info:
            self.video_proc_info.state = state
            self.video_proc_info.save()

    @property
    def isinit(self):
        try:
            video_proc_info = VideoProcInfo.objects.get(
                match_id=self.match_id,
                tb_name=self.tb_name
            )
            if video_proc_info.init == 1:
                self.video_proc_info = video_proc_info
                return True
            return False
        except VideoProcInfo.DoesNotExist:
            return False

class StepRunBase(object):

    def __init__(self, match_id, tb_name, vstate):

        self.match_id = match_id
        self.tb_name = tb_name
        self.vstate = vstate

        y, md, vid = self.match_id.split('_')
        self.regstr = r'{}/{}/{}/{}.*\.(mp4|MP4|mts|MTS)'.format(y, md, vid, self.match_id)
        self.base_object_key = "{}/{}/{}".format(y, md, vid)
        self.full_video_name = "{}_0_00_00_00.mp4".format(self.match_id)
        self.full_video_object_key = os.path.join(self.base_object_key, "scores", self.full_video_name)

        self.s3_video_list = []
        self.video_list = []
        self.__v_proc = None

        self.log_prefix = "[{} {} {}]".format(
            self.vstate.video_proc_info.task_id,
            match_id,
            tb_name
        )

        self.__ = partial(log_format, self.log_prefix)

        self.mp4_save_path = os.path.join(settings.VIDEO_CONV_SAVE_PATH, self.match_id, self.tb_name, 'mp4')
        self.img_save_path = os.path.join(settings.VIDEO_CONV_SAVE_PATH, self.match_id, self.tb_name, 'img')
        self.tmp_img_save_path = os.path.join(settings.VIDEO_CONV_SAVE_PATH, self.match_id, self.tb_name, 'tmp')
        self.download_path = os.path.join(settings.VIDEO_DOWNLOAD_PATH, self.match_id, self.tb_name)

        self.full_video_path = os.path.join(
            self.download_path,
            os.path.basename(self.full_video_name)
        )

    @property
    def v_proc(self):
        if not self.__v_proc:
            self.get_s3_video_list()
            self.__v_proc = VideoProcess(self.s3_video_list, self.log_prefix)
        return self.__v_proc

    def clean_path(self):
        if os.path.isdir(self.mp4_save_path):
            shutil.rmtree(self.mp4_save_path)

        if os.path.isdir(self.img_save_path):
            shutil.rmtree(self.img_save_path)

        if os.path.isdir(self.tmp_img_save_path):
            shutil.rmtree(self.tmp_img_save_path)

        if os.path.isdir(self.download_path):
            shutil.rmtree(self.download_path)

    def init_path(self):
        os.makedirs(self.mp4_save_path)
        os.makedirs(self.img_save_path)
        os.makedirs(self.tmp_img_save_path)
        os.makedirs(self.download_path)

    def get_s3_video_list(self):
        if not self.s3_video_list:
            for f in os.listdir(self.download_path):
                self.s3_video_list.append(os.path.join(self.download_path, f))

        if not self.s3_video_list:
            msg = "match_id: {} 比赛视频在本地已被删除, 请重新运行任务.".format(self.match_id)
            LOG.error(self.__(msg))
            raise Exception(msg)

        self.s3_video_list.sort()

    def step1(self):
        """
        判断比赛视频是否存在。
        如果存在下载所有比赛视频
        """

        # 如果是从第一步开始运行的话，需要清理历史目录并初始化目录结构
        self.clean_path()
        self.init_path()

        self.s3_video_list = []

        object_key_list = get_object_key(self.regstr)
        object_key_list.sort()

        if not object_key_list:
            msg = "match_id: {} 比赛视频在 aws s3 中不存在.".format(self.match_id)
            LOG.error(self.__(msg))
            raise Exception(msg)
        # 下载所有视频
        for i, video in enumerate(object_key_list):
            save_video_name = "{}_{}.{}".format(self.match_id, i, os.path.basename(video).rsplit('.', 1)[1])
            save_path = os.path.join(self.download_path, save_video_name)
            LOG.info(self.__("下载比赛视频文件: aws s3 {} -> {} 开始".format(video, save_path)))
            self.s3_video_list.append(save_path)
            # 如果已经下载了就无需再下载
            if os.path.isfile(save_path):
                continue
            download(video, save_path)
            LOG.info(self.__("下载比赛视频文件: aws s3 {} -> {} 完成".format(video, save_path)))

    def step2(self):
        """
        视频帧转换为图片
        """

        self.get_s3_video_list()

        LOG.info(self.__("视频 {} --> 帧图片开始".format(self.s3_video_list)))
        self.v_proc.capture_video_to_img(self.img_save_path)
        LOG.info(self.__("视频 {} --> 帧图片完成".format(self.s3_video_list)))

    def step4(self):
        """
        上传视频
        """

        if not self.video_list:
            self.video_list = [
                (os.path.join(self.mp4_save_path, f), os.path.join(self.base_object_key, self.tb_name, f))
                for f in os.listdir(self.mp4_save_path)
                if os.path.isfile(os.path.join(self.mp4_save_path, f))
            ]

        for video in self.video_list:
            upload(video[0], video[1])
            LOG.info(self.__("视频：{} 已上传到 aws s3：{}".format(video[0], video[1])))
        LOG.info(self.__("视频已全部上传到 aws s3"))
    
    def step5(self):
        """
        清理本地目录
        """
        self.clean_path()

    def run_step(self):
        if self.vstate.state == 0:
            self.step1()
            self.vstate.state = 1

        if self.vstate.state == 1:
            self.step2()
            self.vstate.state = 2

        if self.vstate.state == 2:
            self.step3()
            self.vstate.state = 3

        if self.vstate.state == 3:
            self.step4()
            self.vstate.state = 4

        if self.vstate.state == 4:
            self.step5()
            self.vstate.state = 5

        return True
        
class StepRunScores(StepRunBase):

    def step3(self):
        """
        合成比分视频
        """
        LOG.info(self.__("开始合成整场视频文件/局数视频文件/比分视频文件"))
        self.video_list = []
        # 合成整场比赛视频
        game_frame_start = 1
        game_frame_end = self.v_proc.total_frame_count
        LOG.info(self.__("合成整场比赛视频，帧[{}:{}] 开始".format(game_frame_start, game_frame_end)))
        video_name_prefix = "{}_0_00_00_00".format(self.match_id)
        video_path = self.v_proc.merge_scores_video(
            self.img_save_path,
            self.tmp_img_save_path,
            self.mp4_save_path,
            video_name_prefix,
            game_frame_start,
            game_frame_end,
            0
        )
        file_name = os.path.basename(video_path)
        object_key = os.path.join(self.base_object_key, self.tb_name, file_name)
        self.video_list.append((video_path, object_key))
        LOG.info(self.__("合成整场比赛视频，帧[{}:{}] 完成，视频：{}".format(game_frame_start, game_frame_end, video_path)))
        for game in range(1, 4):
            rpt_scores = RptScores.objects.filter(matchid=self.match_id, game=game).order_by('frame_start').all()
            if not rpt_scores:
                LOG.warning(self.__("表中数据为空。match_id: {}, tb_name: {}, game: {}".format(self.match_id, self.tb_name, game)))
                continue
            rpt_scores_list = list(rpt_scores)
            game_frame_start = rpt_scores_list[0].frame_start
            game_frame_end = rpt_scores_list[-1].frame_end
            video_name_prefix = "{}_{}_00_00_00".format(self.match_id, game)
            LOG.info(self.__("合成第 {} 局比赛视频，帧[{}:{}] 开始".format(game, game_frame_start, game_frame_end)))
            video_path = self.v_proc.merge_scores_video(
                self.img_save_path,
                self.tmp_img_save_path,
                self.mp4_save_path,
                video_name_prefix,
                game_frame_start,
                game_frame_end,
                2
            )
            file_name = os.path.basename(video_path)
            object_key = os.path.join(self.base_object_key, self.tb_name, file_name)
            self.video_list.append((video_path, object_key))
            LOG.info(self.__("合成第 {} 局比赛视频，帧[{}:{}]完成，视频：{}".format(game, game_frame_start, game_frame_end, video_path)))
            for score in rpt_scores:
                if score.is_mark_error:
                    LOG.error(self.__("比赛 {} 第 {} 局，比分 [{}:{}] 帧 [{}:{}] 标注错误".format(
                        score.matchid, game, score.score_a, score.score_b, score.frame_start, score.frame_end)))
                    continue
                # "YYYY_MMDD_XXXX_A_BB_CC_DD"
                video_name_prefix = "{}_{}_{}_{}_{}".format(
                    self.match_id, game, str(score.score).zfill(2),
                    str(score.score_a).zfill(2), str(score.score_b).zfill(2)
                )
                LOG.info(self.__("合成第 {} 局比分视频，比分帧[{}:{}] 开始".format(game, score.frame_start, score.frame_end)))
                video_path = self.v_proc.merge_scores_video(
                    self.img_save_path,
                    self.tmp_img_save_path,
                    self.mp4_save_path,
                    video_name_prefix,
                    score.frame_start,
                    score.frame_end,
                    1
                )
                # 将视频存储在 aws s3 中的 object kye 记录到相应的表记录
                file_name = os.path.basename(video_path)
                object_key = os.path.join(self.base_object_key, self.tb_name, file_name)
                score.video = object_key
                score.save()
                self.video_list.append((video_path, object_key))
                LOG.info(self.__("合成第 {} 局比分视频，比分帧[{}:{}]完成，视频：{}".format(game, score.frame_start, score.frame_end, video_path)))
        LOG.info(self.__("合成整场视频文件/局数视频文件/比分视频文件完成，共计：{} 个，mp4 保存目录：{}".format(
            len(self.video_list), self.mp4_save_path)))

class StepRunHits(StepRunBase):
    
    def step3(self):
        """
        合成击球视频
        """
        LOG.info(self.__("开始合成击球视频"))
        self.video_list = []
        for game in range(1, 4):
            rpt_scores = RptScores.objects.filter(matchid=self.match_id, game=game).order_by('frame_start').all()
            if not rpt_scores:
                LOG.warning(self.__("表中数据为空。match_id: {}, tb_name: {}, game: {}".format(self.match_id, self.tb_name, game)))
                continue
            for score in rpt_scores:
                if score.is_mark_error:
                    LOG.error(self.__("比赛 {} 第 {} 局，比分 [{}:{}] 帧 [{}:{}] 标注错误".format(
                        score.matchid, game, score.score_a, score.score_b, score.frame_start, score.frame_end)))
                    continue
                rpt_hits = RptHits.objects.filter(
                    matchid=self.match_id,
                    frame_hit__gte=score.frame_start,
                    frame_hit__lte=score.frame_end
                ).order_by('frame_hit').all()
                # 每一个回合(最后一次击球是死球，需要去掉)
                rpt_hits = list(rpt_hits)[0:-1]
                hit_count = 1
                for hit in rpt_hits:
                    # "YYYY_MMDD_XXXX_A_BB_CC_DD_EEE_FFFFFFF"
                    video_name_prefix = "{}_{}_{}_{}_{}_{}_{}".format(
                        self.match_id, game, str(score.score).zfill(2),
                        str(score.score_a).zfill(2), str(score.score_b).zfill(2),
                        str(hit_count).zfill(3), str(hit.frame_hit).zfill(7)
                    )
                    LOG.info(self.__("生成第 {} 局击球视频，击球帧[{}] 开始".format(game, hit.frame_hit)))
                    video_path = self.v_proc.merge_hits_video(
                        self.img_save_path,
                        self.tmp_img_save_path,
                        self.mp4_save_path,
                        video_name_prefix,
                        hit.frame_hit,
                        8,
                        4
                    )
                    hit_count += 1
                    # 将视频存储在 aws s3 中的 object kye 记录到相应的表记录
                    file_name = os.path.basename(video_path)
                    object_key = os.path.join(self.base_object_key, self.tb_name, file_name)
                    hit.video = object_key
                    hit.save()
                    self.video_list.append((video_path, object_key))
                    LOG.info(self.__("生成第 {} 局击球视频，击球帧 [{}] 完成，视频：{}".format(game, hit.frame_hit, video_path)))
        LOG.info(self.__("击球视频文件合成完成，共计：{} 个，mp4 保存目录：{}".format(
            len(self.video_list), self.mp4_save_path)))
         
        
@shared_task(track_started=True)
def hits_video_proc(match_id, tb_name):

    vstate = VideoProcState(match_id, tb_name)
    for i in range(10):
        if vstate.isinit:
            break
        time.sleep(1)
    else:
        LOG.error(u"VideoProcState 初始化超时.")
        raise Exception(u"TimeOut: VideoProcState")

    steprun = StepRunHits(match_id, tb_name, vstate)
    steprun.run_step()

    return True

@shared_task(track_started=True)
def scores_video_proc(match_id, tb_name):

    vstate = VideoProcState(match_id, tb_name)
    for i in range(10):
        if vstate.isinit:
            break
        time.sleep(1)
    else:
        LOG.error(u"VideoProcState 初始化超时.")
        raise Exception(u"TimeOut: VideoProcState")

    steprun = StepRunScores(match_id, tb_name, vstate)
    steprun.run_step()

    return True
