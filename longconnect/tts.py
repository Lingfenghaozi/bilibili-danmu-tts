import asyncio
import os
import tempfile
from playsound import playsound

class TTS:
    # SSML格式头--可以自己修改关键的参数 (制表符\t要不要都行，为了好看我这里加了\t)
    head_ssml = '<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis"\n' + \
        '\t   xmlns:mstts="https://www.w3.org/2001/mstts" xml:lang="zh-CN">\n' + \
        '\t<voice name="zh-CN-YunxiNeural">\n' + \
        '\t\t<mstts:express-as style="chat" styledegree="0.01">\n' + \
        '\t\t\t<prosody rate="+3%" pitch="-0.7st">\n'


    # SSML格式尾--可以自己修改关键的参数
    tail_ssml = '\n\t\t\t</prosody>\n' + \
        '\t\t</mstts:express-as>\n' + \
        '\t</voice>\n' + \
        '</speak>'

    """
        参考
        <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis"
            xmlns:mstts="https://www.w3.org/2001/mstts" xml:lang="zh-CN">
            <voice name="zh-CN-YunxiNeural">
                <mstts:express-as style="chat" styledegree="0.01">
                    <prosody rate="+3%" pitch="-0.7st">
                        观众1说：主播早上好！
                    </prosody>
                </mstts:express-as>
            </voice>
        </speak>
    """
    

    # SSML文件，计划创建于本机临时文件夹，所以获取并拼接临时文件夹地址得到文件地址（也就是包含绝对路径的文件名）
    ssml_file_name = tempfile.gettempdir() + "\\TTS-SSML.xml"
    # 生成的弹幕音频文件位置（包含绝对路径的文件名）
    danmu_file_name = tempfile.gettempdir() + "\\弹幕.mp3"
    # 拼接edge-tts命令，用于上传发送用户自定义SSML文件，请求Microsoft的TTS服务，转换为音频文件
    cmd_tts = "edge-tts --custom-ssml --file " + ssml_file_name + " --write-media " + danmu_file_name

    """
        参考
        ssml_file_name = "C:\\Users\\LINGFE~1\\AppData\\Local\\Temp\\TTS-SSML.xml"
        danmu_file_name = "C:\\Users\\LINGFE~1\\AppData\\Local\\Temp\\弹幕.mp3"
        cmd_tts = "edge-tts --custom-ssml --file TTS-SSML.xml --write-media 弹幕.mp3"
    """

    
    def play_tts_mp3(self, read_string: str):
        """
        文本转语音并播放合成好的mp3音频文件
        read_string: 要读的文字，包括弹幕发送人、弹幕内容等信息，在弹幕获取模块处理好作为参数直接传入
        """

        if read_string is None:
            return False
        # 结合传入的文字内容修改（覆写）SSML文件--SSML文件是根据Microsoft提供的格式来写的
        # 具体参考https://docs.microsoft.com/zh-cn/azure/cognitive-services/speech-service/speech-synthesis-markup?tabs=csharp
        try:
            with open(TTS.ssml_file_name, 'w', encoding='utf-8') as ssml_file:
                ssml_file.write(TTS.head_ssml + '\t\t\t\t' + read_string + TTS.tail_ssml)
        except Exception:
            pass

        # 执行拼接好的edge-tts命令，利用含有弹幕信息及朗读参数的SSML文件，获取转换后的弹幕音频文件
        os.system(TTS.cmd_tts)

        try:
            # 调用playsound模块读转换好的mp3弹幕文件
            playsound(TTS.danmu_file_name)
        except Exception:
            return



def main():
    tts = TTS()
    # 获取弹幕
    read_string = "先来模拟测试一下弹幕，测试1。"
    tts.play_tts_mp3(read_string)
    read_string2 = "先来模拟测试一下弹幕，测试2。"
    tts.play_tts_mp3(read_string2)
    read_string2 = "先来模拟测试一下弹幕，测试3。"
    tts.play_tts_mp3(read_string2)
    

if __name__ == "__main__":
    asyncio.run(main())
    