#!/usr/bin/env python
#coding: utf-8


"""
由于无法动态监控多级目录文件的新增变化
此文件暂时没用到
"""

import os
import datetime
import pyinotify
import logging

logging.basicConfig(level=logging.INFO,filename='/tmp/monitor.log')

class ChangeEventHandler(pyinotify.ProcessEvent):
    def process_IN_CREATE(self, event):
        """
        新建事件
        """
        logging.info("CREATE event : %s  %s" % (os.path.join(event.path,event.name),datetime.datetime.now()))
      
    def process_IN_DELETE(self, event):
        """
        删除事件
        """
        logging.info("DELETE event : %s  %s" % (os.path.join(event.path,event.name),datetime.datetime.now()))
      
    def process_IN_MOVED(self, event):
        """
        移动事件(IN_MOVED_FROM&IN_MOVED_TO)
        """
        logging.info("MOVED event : %s  %s" % (os.path.join(event.path,event.name),datetime.datetime.now()))
     
     
def main():
    logging.info("Starting monitor...")
    # watch manager
    wm = pyinotify.WatchManager()
    wm.add_watch('/home/ubuntu/docs', pyinotify.ALL_EVENTS, rec=True)
    # event handler
    eh = MyEventHandler()
 
    # notifier
    notifier = pyinotify.Notifier(wm, eh)
    notifier.loop()
 
if __name__ == '__main__':
    main()
