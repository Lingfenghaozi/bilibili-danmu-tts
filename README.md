### 声明

目前版本仅针对作者个人需求开发使用，暂不考虑升级为UI版本

但源码中为升级保留需要的部分数据结构和一些函数处理，如有需求想法可自行改写完成

**当前的代码中依然存在未知原因的少数崩溃情况，初步推测触发原因可能为轮询发送请求频率过高而被服务器拒绝**

### 环境

如需使用，请确认安装有 **`edge--tts`** 、以及 **`playsound`** 库
```
pip install edge-tts
```
```
pip install playsound
```
将以上代码输入cmd中运行即可

### 修改房间号
打开`bilibili_danmu.py`文件，在网络请求参数的 **`roomid`** 后面修改房间号即可

### 其他

如果无法自动播放声音，则自行搜索 **`python playsound`** 模块的相关配置或用法

本项目的TTS使用了微软的TTS引擎，如果无法使用也有可能是接口服务方式等已经发生改变

参考了[rany2/edge-tts](https://github.com/rany2/edge-tts)的项目用例，感兴趣的朋友可以参考该源码进行你喜欢的针对性优化
