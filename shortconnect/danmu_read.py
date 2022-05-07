import asyncio
import time
from danmu_shortconnect import BilibiliDanmu
from tts import TTS


async def danmu_tts_read():

    thread_bilibili_danmu = BilibiliDanmu()
    thread_bilibili_danmu.start()
    tts = TTS()
    
    while True:
        # 获取要读的弹幕文本（在弹幕类里面已经格式处理化好）
        read_string = thread_bilibili_danmu.pop_danmu_read()
        if read_string:
            await tts.play_tts_mp3(read_string)
        else:
            time.sleep(2)


def main():
    """
    为了方便在其他没有导asyncio库的py文件中测试，创建一个自带异步事件注册的程序入口
    """
    asyncio.run(danmu_tts_read())


if __name__ == "__main__":
    main()