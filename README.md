### 最新说明，本程序暂时无法正常工作

此程序采用了edge-tts包，5.0.0版本指出当前Microsoft已阻止自定义SSML的工作，因此无法再使用自定义SSML文件上传获取TTS音频文件。

### V2.0更新说明

1.新增了长连接方式，有效解决了根源上频繁弹出报错异常等情况，一定程度上收到的弹幕请求回复能更加“实时”而不再是原来设定的1秒轮询一次。同时也可能较大程度的避免因短连接请求过于频繁而被标记黑名单阻止访问。强烈建议使用长连接方式。

2.保留了V1.0版本的短连接方式，去掉了except中的异常说明。

3.长连接和短连接方式读弹幕的处理格式有所不同，具体可以自行进入指定文件danmu_longconnect.py和danmu_shortconnect.py找到相应函数analyze_danmu()与format_danmu_read()内修改。

### 声明

目前版本仅针对作者个人需求开发使用，暂不考虑升级为UI版本

但源码中为升级保留需要的部分数据结构和一些函数处理，如有需求想法可自行改写完成

### 环境

如需使用，请确认安装有 **`edge--tts`** 、**`zlib`** 、**`brotli`** 、**`AioWebSocket·`** 以及 **`playsound`** 库
```
pip install edge-tts
```
```
pip install playsound
```
```
pip install zlib
```
```
pip install brotli
```
```
pip install AioWebSocket
```
将以上代码输入cmd中运行即可，如有失败，可自行搜索换源下载或其他解决方案

### 修改房间号
打开`bilibili_danmu.py`文件，在网络请求参数的 **`roomid`** 后面修改房间号即可

### 其他

如果无法自动播放声音，则自行搜索 **`python playsound`** 模块的相关配置或用法

本项目的TTS使用了微软的TTS引擎，如果无法使用也有可能是接口服务方式等已经发生改变

参考了[rany2/edge-tts](https://github.com/rany2/edge-tts)的项目用例，感兴趣的朋友可以参考该源码进行你喜欢的针对性优化
