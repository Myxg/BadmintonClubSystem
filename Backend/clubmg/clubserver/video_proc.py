#coding: utf-8

import os
import logging
import shutil
from functools import partial

import cv2
import ffmpeg

LOG = logging.getLogger(__file__)

# cv2 默认只支持生成 avi 格式视频
fourcc = cv2.VideoWriter_fourcc(*'DIVX')

def conv_video(from_file, to_file, quiet=False):
    # ffmpeg-python 在目标文件存在是无法转换生成，需要先删除目标文件
    if os.path.isfile(to_file):
        os.remove(to_file)
    (
        ffmpeg
        .input(from_file)
        .output(to_file, vcodec='h264', strict=-2)
        .run(quiet=quiet)
    )

def merge_video_from_multi_video(from_file, to_file, quiet=False):
    """多个视频文件合并为一个视频文件
    """
    # ffmpeg-python 在目标文件存在是无法转换生成，需要先删除目标文件
    if os.path.isfile(to_file):
        os.remove(to_file)
    (
        ffmpeg
        .input(from_file, f='concat', safe=0)
        .output(to_file, vcodec='h264', strict=-2)
        .run(quiet=quiet)
    )

def merge_video_from_img(img_path, to_file, quiet=False):
    """通过图片生成视频
    """
    if os.path.isfile(to_file):
        os.remove(to_file)
    # 图片合成mp4视频
    (
        ffmpeg
        .input(img_path, f='image2')
        .output(to_file, vcodec='h264')
        .run(quiet=quiet)
    )

def log_format(log_prefix, log):
    return "{} {}".format(log_prefix, log)

class VideoProcess(object):
    
    def __init__(self, video_list, log_prefix=None):
        self.video_list = video_list
        self.log_prefix = log_prefix

        self.video_captures = []
        self.total_frame_count = 0
        # 前后增加多少视频时fps一律按照24来计算
        self.fps = 24

        for video in self.video_list:
            _video_capture = cv2.VideoCapture(video)
            frame_count = int(_video_capture.get(cv2.CAP_PROP_FRAME_COUNT))
            self.total_frame_count += frame_count
            self.video_captures.append(
                {
                    "video_capture": _video_capture,
                    "video": video,
                    "fps": self.get_fps(_video_capture),
                    "frame_count": frame_count
                }
            )

        if self.log_prefix:
            self.__ = partial(log_format, self.log_prefix)
        else:
            self.__ = lambda s: s

    def get_fps(self, video_capture):
        # OpenCV 版本
        (major_ver, minor_ver, subminor_ver) = (cv2.__version__).split('.')
        if int(major_ver)  < 3 :
            fps = video_capture.video.get(cv2.cv.CV_CAP_PROP_FPS)
        else :
            fps = video_capture.get(cv2.CAP_PROP_FPS)
    
        return fps

    def capture_video_to_img(self, img_save_path):
        """将视频切割为图片
        :param img_save_path: string 分解为图片后保存路径
        :return: None
        """
        
        frame_count = self.total_frame_count
        count = 1

        for video_capture in self.video_captures:
            while True:
                success, frame = video_capture["video_capture"].read()
                if not success:
                    break
                res = cv2.resize(
                    frame,
                    None,
                    fx=1,
                    fy=1,
                    interpolation=cv2.INTER_CUBIC
                ) 
                img_name = "{}.jpg".format(count)
                cv2.imwrite(
                    os.path.join(img_save_path, img_name),
                    res
                )
                if count % 2000 == 0:
                    LOG.info(self.__("{} 视频帧 -> 图片完成比 {}/{}".format(video_capture["video"], count, frame_count)))
                count += 1

        LOG.info(self.__("{} 视频帧 -> 图片完成比 {}/{}".format(video_capture["video"], count, frame_count)))
            
    def merge_video(self, img_save_path, tmp_img_save_path,
        mp4_save_path, name_prefix, start_frame, end_frame, 
        mark_frame=[]):

        """图片生成视频
        :param img_save_path: string 视频分解后的图片目录
        :param tmp_img_save_path: string 涉及到的视频帧图片保存目录
        :param mp4_save_path: string mp4 格式视频保存目录
        :param name_prefix: string 保存视频的名字前缀，扩展名由视频生成程序决定，最后将视频全路径返回
        :param start_frame: int 视频开始帧
        :param end_frame: int 视频结束帧
        :param mark_frame: list 需要标注的帧列表
        :return: 生成最后视频的路径
        """
        # 初始化目录
        if os.path.isdir(tmp_img_save_path):
            shutil.rmtree(tmp_img_save_path)

        os.makedirs(tmp_img_save_path)
        # 将涉及到的图片复制到 tmp_img_save_path，并重新排序帧号
        count = 1
        for i in range(start_frame, end_frame + 1):
            src_img_name = "{}.jpg".format(i)
            src_img = os.path.join(img_save_path, src_img_name)
            if not os.path.isfile(src_img):
                LOG.warning(self.__("视频帧图片：{} 不存在".format(src_img)))
                continue
            des_img_name = "{}.jpg".format(str(count).zfill(7))
            des_img = os.path.join(tmp_img_save_path, des_img_name)
            if i in mark_frame:
                img = cv2.imread(src_img)
                size = img.shape
                rect_size = (
                    (size[1] - 10),
                    (size[0] - 10),
                )
                # 标注当前帧
                cv2.rectangle(img, (10, 10), rect_size, (0, 0, 255,), 20)
                cv2.imwrite(des_img, img)
            else:
                shutil.copyfile(src_img, des_img)
            count += 1
        
        # 最终 mp4 h264 格式视频存储目录
        mp4_video_name = "{}.mp4".format(name_prefix)
        mp4_video_path = os.path.join(mp4_save_path, mp4_video_name)
        # 需要合成视频的所有图片
        imgs = os.path.join(tmp_img_save_path, "%07d.jpg")
        # 图片准备好后合成视频
        merge_video_from_img(imgs, mp4_video_path)
        
        return mp4_video_path
            

    def merge_scores_video(self, img_save_path, tmp_img_save_path, mp4_save_path,
            name_prefix, start_frame, end_frame, start_add_sec, end_add_sec=None):

        """比分视频合成
        :param img_save_path: string 视频分解后的图片目录
        :param tmp_img_save_path: string 涉及到的视频帧图片保存目录
        :param mp4_save_path: string mp4 格式视频保存目录
        :param name_prefix: string 保存视频的名字前缀，扩展名由视频生成程序决定，最后将视频全路径返回
        :param start_frame: int 视频开始帧
        :param end_frame: int 视频结束帧
        :param start_add_sec: int 起始帧之前补充多少秒视频(即向前推进 fps * sec 帧视频)
        :param end_add_sec: int 结束帧之后补充多少秒视频(即向后推进 fps * sec 帧视频，如果不设置则与 start_add_sec 相同)
        :return: 生成最后视频的路径
        """

        if not end_add_sec:
            end_add_sec = start_add_sec

        start_frame = start_frame - (start_add_sec * self.fps)
        end_frame = end_frame + (end_add_sec * self.fps)

        if start_frame < 0:
            start_frame = 1
        if end_frame > self.total_frame_count:
            end_frame = self.total_frame_count

        start_frame, end_frame = int(start_frame), int(end_frame)

        return self.merge_video(img_save_path, tmp_img_save_path, mp4_save_path, name_prefix, start_frame, end_frame)

    def merge_hits_video(self, img_save_path, tmp_img_save_path, mp4_save_path,
            name_prefix, hit_frame, mark_frame, start_add_sec, end_add_sec=None):

        """击球视频合成
        :param img_save_path: string 视频分解后的图片目录
        :param tmp_img_save_path: string 涉及到的视频帧图片保存目录
        :param mp4_save_path: string mp4 格式视频保存目录
        :param name_prefix: string 保存视频的名字前缀，扩展名由视频生成程序决定，最后将视频全路径返回
        :param hit_frame: int 击球帧
        :param mark_frame: int 标记击球前后几帧
        :param start_add_sec: int 起始帧之前补充多少秒视频(即向前推进 fps * sec 帧视频)
        :param end_add_sec: int 结束帧之后补充多少秒视频(即向后推进 fps * sec 帧视频，如果不设置则与 start_add_sec 相同)
        :return: 生成最后视频的路径
        """

        if not end_add_sec:
            end_add_sec = start_add_sec

        start_frame = hit_frame - (start_add_sec * self.fps)
        end_frame = hit_frame + (end_add_sec * self.fps)

        if start_frame < 0:
            start_frame = 0
        if end_frame > self.total_frame_count:
            end_frame = self.total_frame_count
        
        start_frame, end_frame = int(start_frame), int(end_frame)
        mark_frame = range(hit_frame - mark_frame, hit_frame + mark_frame + 1)

        return self.merge_video(img_save_path, tmp_img_save_path, mp4_save_path, name_prefix, start_frame, end_frame, mark_frame)


    def __del__(self):
        for video_capture in self.video_captures:
            try:
                video_capture.release()
            except Exception as e:
                continue

if __name__ == '__main__':
    pass
