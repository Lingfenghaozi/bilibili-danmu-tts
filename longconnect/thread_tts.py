import asyncio
import threading
import time
import tts
from danmu_longconnect import BilibiliDanmu

class ThreadTTS(threading.Thread):
    def __init__(self, bilibili_danmu : BilibiliDanmu):
        threading.Thread.__init__(self)

        # 内部创建一个tts模块
        self.TTS = tts.TTS()

        # 传递一个弹幕类
        self.bilibili_danmu = bilibili_danmu


    def run(self):
        while True:
            try:
                # 获取要读的弹幕文本
                read_string = self.bilibili_danmu.pop_read_list()
                if read_string:
                    self.TTS.play_tts_mp3(read_string)
                else:
                    time.sleep(2)
            except Exception:
                pass


# test

def main():
    bilibili_danmu = BilibiliDanmu('5050', 1)
    thread_tts = ThreadTTS(bilibili_danmu)
    thread_tts.start()
    asyncio.run(bilibili_danmu.startup())


if __name__ == "__main__":
    main()

