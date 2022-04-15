import asyncio
import zlib
import brotli
from aiowebsocket.converses import AioWebSocket
import json



# 房间号
roomid = '5050'

# 未加密的WebSocket连接
remote = 'ws://broadcastlv.chat.bilibili.com:2244/sub'

data_raw = '000000{headerLen}0010000100000007000000017b22726f6f6d6964223a{roomid}7d'
data_raw = data_raw.format(headerLen=hex(27 + len(roomid))[2:],
                           roomid=''.join(map(lambda x: hex(ord(x))[2:], list(roomid))))

async def startup():
    async with AioWebSocket(remote) as aws:
        # 发送第一个数据包，包含房间号的连接信息
        # 这个数据包必须为连接以后的第一个数据包，5秒内不发送进房数据包，服务器主动断开连接，任何数据格式错误将直接导致服务器主动断开连接。
        converse = aws.manipulator
        await converse.send(bytes.fromhex(data_raw))
        # 创建协程任务
        task1 = asyncio.create_task(send_heartbeat(converse))
        task2 = asyncio.create_task(receive_packets(converse))
        task_list = [task1, task2]
        # 并发运行
        await asyncio.wait(task_list)


# 发送心跳包，30秒发送一次，70秒不发送则会断开连接
heartbeat_package='00 00 00 10 00 10 00 01 00 00 00 02 00 00 00 01'
async def send_heartbeat(websocket):
    while True:
        await asyncio.sleep(30)
        await websocket.send(bytes.fromhex(heartbeat_package))
        print('[通知] Sent HeartBeat.')


# 接收数据包
async def receive_packets(websocket):
    while True:
        packets = await websocket.receive()

        if packets:
            split_packets(packets)


"""
    参考https://github.com/lovelyyoshino/Bilibili-Live-API/blob/master/API.WebSocket.md来解析
"""

# 拆解服务器发送回来的数据包
def split_packets(packets):

    # 获取数据包的总长度
    packet_length = int(packets[:4].hex(), 16)
    # 获取协议版本
    protocol_version = int(packets[6:8].hex(), 16)
    # 获取操作类型
    operation_type = int(packets[8:12].hex(), 16)     

    # 网络拥挤等原因，有时候可能会两个数据包连在一起发过来，所以利用前面的数据包长度判断
    if len(packets) > packet_length:
        split_packets(packets[packet_length:])
        packets = packets[:packet_length]
    
    # 协议版本为2时表示这部分数据内容需要进行解压，需要使用zlib解压后以完整数据包的形式再重新操作，故使用嵌套递归操作
    if protocol_version == 2:
        packets = zlib.decompress(packets[16:])
        split_packets(packets)
        return

    # 协议版本为3时需要brotli解压，然后以完整数据包的形式再重新操作，用嵌套递归操作
    if protocol_version == 3:
        packets = brotli.decompress(packets[16:])
        split_packets(packets)
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
            analyze_danmu(msg)
        except Exception:
            pass


    # 操作类型为8是服务器的进房回应，表示成功我们进入了房间
    elif operation_type == 8:
        print("成功连接至指定房间！")


# 分析弹幕消息——根据数据包中包含的key进行分类处理
def analyze_danmu(msg):
    try:
        # 弹幕消息
        if msg['cmd'] == 'DANMU_MSG':
            print("{0}说：{1}".format(msg['info'][2][1], msg['info'][1]))
        # 投喂礼物
        elif msg['cmd'] == 'SEND_GIFT':
            print("感谢 {0} {1}了{2}个{3}".format(msg['data']['uname'], msg['data']['action'], msg['data']['num'], msg['data']['giftName']))
        # 连击礼物
        elif msg['cmd'] == 'COMBO_SEND':
            print('感谢 {0}的{1}个{2}'.format(msg['data']['uname'], msg['data']['combo_num'], msg['data']['gift_name']))
        # 观众进入房间
        elif msg['WELCOME']:
            print("欢迎{0}".format(msg['data']['uname']))
    except Exception:
        pass


# 入口
if __name__ == "__main__":
    asyncio.run(startup())
