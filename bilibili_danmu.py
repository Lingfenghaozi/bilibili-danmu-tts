import requests
import time
import threading
import traceback

class BilibiliDanmu(threading.Thread):
    # 网络请求参数
    url = 'https://api.live.bilibili.com/xlive/web-room/v1/dM/gethistory'
    headers = {
        'Host': 'api.live.bilibili.com',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.66 Safari/537.36 SE 2.X MetaSr 1.0',
    }
    data = {
        'roomid': '13645871', # 房间号，获取不同主播的直播间弹幕修改这里
    }

    # 默认值
    DEFAULT_MAX_HISTORY = 20    # 历史弹幕最大上限
    DEFAULT_MAX_READ = 3        # 待TTS的缓冲池弹幕个数上限
    DEFAULT_SLEEP_TIME = 1      # 获取弹幕的间隔休眠时间（单位：秒）


    
    def __init__(self, max_history: int = DEFAULT_MAX_HISTORY, max_read: int = DEFAULT_MAX_READ, sleep_time: int = DEFAULT_SLEEP_TIME):
        
        threading.Thread.__init__(self)

        """
            从网络请求返回里裁剪出来的自定义数据存储结构
            数据结构参考：
            [
                {'nickname':'aaa', 'text':'2021再见！', 'timeline':'2022-01-01 00:00:00'},
                {'nickname':'bbb', 'text':'2022你好！', 'timeline':'2022-01-01 00:00:01'},
                {'nickname':'cde', 'text':'新年快乐！', 'timeline':'2022-01-01 00:00:02'}
            ]
        """
        # 记录弹幕历史，用于新旧弹幕的检测（可设置上限防止内存占用过多）
        self.danmu_list_history = []

        # 记录弹幕列表，用于弹幕的本地显示
        self.danmu_list_show = []

        # 要读的弹幕的池子（可设置上限只读最近的几条弹幕，过滤因弹幕过多、读弹幕速度慢等因素导致的时效性不高的弹幕）
        self.danmu_list_read = []

        # 用于记录的历史弹幕列表的最大上限
        self.max_history = max_history if max_history > 0 else BilibiliDanmu.DEFAULT_MAX_HISTORY

        # 等待TTS完成后播放音频的弹幕池子
        self.max_read = max_read if max_read > 0 else BilibiliDanmu.DEFAULT_MAX_READ

        # 获取弹幕的间隔时间（单位：秒）
        self.sleep_time = sleep_time if sleep_time > 0 else BilibiliDanmu.DEFAULT_SLEEP_TIME


    
    def get_new_danmu(self):
        """
        循环获取弹幕，实现更新
        """
        while True:
            try:
                # 带参请求
                message = requests.get(url=BilibiliDanmu.url, headers=BilibiliDanmu.headers, params=BilibiliDanmu.data).json()
                # 从网页请求返回的结果提取弹幕信息，包括发送人、发送时间、发送内容等键值对的列表list
                danmu_info = message['data']['room']

                # 判断当次网页请求返回结果是否获取到弹幕（可能包含已记录和未记录）
                if len(danmu_info) > 0:
                    # 如果没有历史弹幕，则此次获取到的弹幕直接全部添加进历史弹幕列表中记录起来
                    if len(self.danmu_list_history) == 0:
                        for i in range(len(danmu_info)):
                            danmu = {'nickname':danmu_info[i]['nickname'], 'text':danmu_info[i]['text'], 'timeline':danmu_info[i]['timeline']}
                            self.add_history_list(danmu)
                            self.add_show_list(danmu)
                            self.add_read_list(danmu)
                    else:
                        # 轮询读获取到的弹幕列表
                        for i in range(len(danmu_info)):
                            # 逐条弹幕根据获取到的发送时间比较本地已经记录的最后一条弹幕的时间判断是否是新消息，若是新的则将后边的全部添加（内层循环负责操作后续的添加），然后直接结束外层循环（外层循环负责检查判断）
                            if danmu_info[i]['timeline'] > self.danmu_list_history[-1]['timeline']:
                                for j in range(i, len(danmu_info)):
                                    danmu = {'nickname':danmu_info[j]['nickname'], 'text':danmu_info[j]['text'], 'timeline':danmu_info[j]['timeline']}
                                    self.add_history_list(danmu)
                                    self.add_show_list(danmu)
                                    self.add_read_list(danmu)
                                break
                    
                    # 更新显示弹幕
                    self.update_danmu_show()
                time.sleep(self.sleep_time)

            except Exception:
                print(traceback.format_exc())
                print("网络请求异常，将于5秒后自动忽略并重新发送弹幕请求。")
                print("网络请求异常，将于5秒后自动忽略并重新发送弹幕请求。")
                print("网络请求异常，将于5秒后自动忽略并重新发送弹幕请求。")
                time.sleep(5)
                pass
    

    def run(self):
        # 第一次启动，会先去发送一次请求来获得历史弹幕
        try:
            # 带参请求
            message = requests.get(url=BilibiliDanmu.url, headers=BilibiliDanmu.headers, params=BilibiliDanmu.data).json()
            # 从网页请求返回的结果提取弹幕信息，包括发送人、发送时间、发送内容等键值对的列表list
            danmu_info = message['data']['room']
            # 先判断获取的弹幕数量是否为0，即是否有历史弹幕
            if len(danmu_info) > 0:
                # 把获取到的弹幕拆分存储到我们的弹幕历史列表中
                for info in danmu_info:
                    danmu = {'nickname':info['nickname'], 'text':info['text'], 'timeline':info['timeline']}
                    self.add_history_list(danmu)
                    self.add_show_list(danmu)
        except Exception:
            print(traceback.format_exc())
            print("初始化时发生错误，第一次获取历史弹幕的网络请求异常，请关闭后重新运行程序。")
            pass
        

        # 更新显示弹幕
        self.update_danmu_show()
        time.sleep(self.sleep_time)
        self.get_new_danmu()





    
    def set_showlist_max(self, max_history: int):
        """
        用于提供UI控制的弹幕显示列表记录最大值的修改
        """
        self.max_history = max_history if max_history > 0 else BilibiliDanmu.DEFAULT_MAX_HISTORY


    
    def set_readlist_max(self, max_read: int):
        """
        用于提供UI控制的弹幕播放缓冲池最大值的修改
        """
        self.max_read = max_read if max_read > 0 else BilibiliDanmu.DEFAULT_MAX_READ

    
    def set_sleep_time(self, sleep_time: int):
        """
        用于提供UI控制的弹幕获取时间间隔（单位：秒）
        """
        self.sleep_time = sleep_time if sleep_time > 0 else BilibiliDanmu.DEFAULT_SLEEP_TIME


    
    def format_danmu_read(self, danmu: dict):
        """
        为弹幕TTS前做格式化
        danmu: 含弹幕信息的字典元素

        参考：
            xxx说：abcd，efg
        """
        if danmu is None:
            return None
        read_string = danmu['nickname'] + "说：" + danmu['text']
        return str(read_string)


    
    def pop_danmu_read(self):
        """
        为TTS模块提供调用服务：返回要读的弹幕信息
        1: 格式化待读弹幕缓冲池中的第一个弹幕字典成返回的文本信息
        2: 移除要读取的弹幕的消息池第一个元素
        3: 返回文本信息
        """
        if len(self.danmu_list_read) <= 0:
            return None
        danmu_string = self.format_danmu_read(self.danmu_list_read[0])
        del self.danmu_list_read[0]
        return danmu_string


    
    def add_history_list(self, danmu: dict):
        """
        根据弹幕历史列表上限添加新的弹幕到列表中
        danmu: 含弹幕信息的字典元素
        """
        if danmu is None:
            return False
        # 判断是否达到上限,若达到上限则移除第一个元素再添加
        if len(self.danmu_list_history) == self.max_history:
            del self.danmu_list_history[0]
        self.danmu_list_history.append(danmu)
        return True


    
    def add_show_list(self, danmu: dict):
        """
        添加新的弹幕到现实列表
        danmu: 含弹幕信息的字典元素
        """
        if danmu is None:
            return False
        self.danmu_list_show.append(danmu)
        return True
    

    
    def add_read_list(self, danmu: dict):
        """
        根据读弹幕缓冲池上限添加新的弹幕到缓冲池中
        danmu: 含弹幕信息的字典元素
        """
        if danmu is None:
            return False
        # 判断是否达到上限,若达到上限则移除第一个元素再添加
        if len(self.danmu_list_read) == self.max_read:
            del self.danmu_list_read[0]
        self.danmu_list_read.append(danmu)
        return True


    
    def update_danmu_show(self):
        """
        更新弹幕列表的显示
        """
        if len(self.danmu_list_show) > 0:
            for danmu in self.danmu_list_show:
                print("{0} {1} 说：{2}".format(danmu['timeline'], danmu['nickname'], danmu['text']))
            self.danmu_list_show.clear()
    
        

if __name__ == "__main__":
    thread_bilibili_danmu = BilibiliDanmu()
    thread_bilibili_danmu.start()
