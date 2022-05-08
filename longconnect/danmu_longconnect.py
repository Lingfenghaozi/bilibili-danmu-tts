import asyncio
import zlib
import brotli
from aiowebsocket.converses import AioWebSocket
import json


class BilibiliDanmu():
    
    # 未加密的WebSocket连接api
    api = 'ws://broadcastlv.chat.bilibili.com:2244/sub'

    # 心跳包
    heartbeat_package='00 00 00 10 00 10 00 01 00 00 00 02 00 00 00 01'

    # 待TTS的缓冲池弹幕个数上限
    DEFAULT_MAX_READ = 3


    def __init__(self, roomid: str = '1', max_read: int = DEFAULT_MAX_READ):
        # 房间号
        self.roomid = roomid

        # 要读的弹幕的池子（可设置上限只读最近的几条弹幕，过滤因弹幕过多、读弹幕速度慢等因素导致的时效性不高的弹幕）
        self.read_list = []

        # 等待TTS完成后播放音频的弹幕池子
        self.max_read = max_read if max_read > 0 else BilibiliDanmu.DEFAULT_MAX_READ


    # 发送心跳包，30秒发送一次，70秒不发送则会断开连接
    async def send_heartbeat(self, websocket):
        while True:
            await asyncio.sleep(30)
            await websocket.send(bytes.fromhex(self.heartbeat_package))


    # 接收数据包
    async def receive_packets(self, websocket):
        while True:
            packets = await websocket.receive()
            if packets:
                self.split_packets(packets)


    # 启动长连接获取弹幕和消息
    async def startup(self):
        # 预处理数据包
        packet_raw = '000000{header_length}0010000100000007000000017b22726f6f6d6964223a{roomid}7d'
        # 建立连接后的第一个数据包内容，对预处理再次格式化加工成为真实内容
        first_packet = packet_raw.format(header_length=hex(27 + len(self.roomid))[2:],
                                         roomid=''.join(map(lambda x: hex(ord(x))[2:], list(self.roomid))))
        async with AioWebSocket(self.api) as aws:
            # 发送第一个数据包，包含房间号的连接信息
            # 这个数据包必须为连接以后的第一个数据包，5秒内不发送进房数据包，服务器主动断开连接，任何数据格式错误将直接导致服务器主动断开连接。
            converse = aws.manipulator
            await converse.send(bytes.fromhex(first_packet))

            # 创建协程任务，分别处理后续长连接的心跳包和消息弹幕接收
            task1 = asyncio.create_task(self.send_heartbeat(converse))
            task2 = asyncio.create_task(self.receive_packets(converse))
            task_list = [task1, task2]
            # 并发运行
            await asyncio.wait(task_list)


    """
        参考https://github.com/lovelyyoshino/Bilibili-Live-API/blob/master/API.WebSocket.md来解析
    """

    # 拆解服务器发送回来的数据包
    def split_packets(self, packets):

        # 获取数据包的总长度
        packet_length = int(packets[:4].hex(), 16)
        # 获取协议版本
        protocol_version = int(packets[6:8].hex(), 16)
        # 获取操作类型
        operation_type = int(packets[8:12].hex(), 16)     

        # 网络拥挤等原因，有时候可能会两个数据包连在一起发过来，所以利用前面的数据包长度判断
        if len(packets) > packet_length:
            self.split_packets(packets[packet_length:])
            packets = packets[:packet_length]
        
        # 协议版本为2时表示这部分数据内容需要进行解压，需要使用zlib解压后以完整数据包的形式再重新操作，故使用嵌套递归操作
        if protocol_version == 2:
            packets = zlib.decompress(packets[16:])
            self.split_packets(packets)
            return

        # 协议版本为3时需要brotli解压，然后以完整数据包的形式再重新操作，用嵌套递归操作
        if protocol_version == 3:
            packets = brotli.decompress(packets[16:])
            self.split_packets(packets)
            return

        """
            协议版本为0和1分别是JSON纯文本和房间人气值
            如果不需要特殊处理则直接进行到下一步统一判断操作类型即可
            操作类型有2, 3, 5, 7, 8
            2和7分别是客户端向服务器发送的，所以我们作为客户端这里就不进行判断了
        """

        # 操作类型为3是服务器发送的心跳回应，包含房间人气值，4字节的整数
        if operation_type == 3:
            print('当前房间人气：{}'.format(int(packets[16:].hex(), 16)))

        # 操作类型为5表示弹幕礼物广播等信息，通过其字段来判断相应的弹幕特征类型
        elif operation_type == 5:
            try:
                msg = json.loads(packets[16:].decode('utf-8', errors='ignore'))
                # 弹幕消息分类并处理
                self.analyze_danmu(msg)
            except Exception:
                pass


        # 操作类型为8是服务器的进房回应，表示成功我们进入了房间
        elif operation_type == 8:
            print("成功连接至指定房间！")


    # 分析弹幕消息——根据数据包中包含的key进行分类处理
    def analyze_danmu(self, msg):
        try:
            # 弹幕消息
            if msg['cmd'] == 'DANMU_MSG':
                read_string = "{0}说：{1}".format(msg['info'][2][1], msg['info'][1])
                print(read_string)
                self.add_read_list(read_string)
            # 投喂礼物
            elif msg['cmd'] == 'SEND_GIFT':
                read_string = "感谢 {0} {1}了{2}个{3}".format(msg['data']['uname'], msg['data']['action'], msg['data']['num'], msg['data']['giftName'])
                print(read_string)
                self.add_read_list(read_string)
            # 连击礼物
            elif msg['cmd'] == 'COMBO_SEND':
                read_string ="感谢 {0}的{1}个{2}".format(msg['data']['uname'], msg['data']['combo_num'], msg['data']['gift_name'])
                print(read_string)
                self.add_read_list(read_string)
            # 观众进入房间
            elif msg['WELCOME']:
                read_string = "欢迎{0}".format(msg['data']['uname'])
                print(read_string)
                self.add_read_list(read_string)
        except Exception:
            pass

    
    def add_read_list(self, read_string):
        """
        根据读弹幕缓冲池上限添加新的弹幕到缓冲池中
        """
        if read_string is None:
            return False
        # 判断是否达到上限,若达到上限则移除第一个元素再添加
        if len(self.read_list) == self.max_read:
            del self.read_list[0]
        self.read_list.append(read_string)
        return True


    def pop_read_list(self):
        """
        为TTS模块提供调用服务：返回要读的弹幕信息
        1: 格式化待读弹幕缓冲池中的第一个弹幕字典成返回的文本信息
        2: 移除要读取的弹幕的消息池第一个元素
        3: 返回文本信息
        """
        if len(self.read_list) <= 0:
            return None
        read_string = self.read_list[0]
        del self.read_list[0]
        return read_string


def main():
    thread_bilibili_danmu = BilibiliDanmu('13645871')
    asyncio.run(thread_bilibili_danmu.startup())
    

if __name__ == "__main__":
    main()
