import os
import subprocess

# 执行命令并捕获输出
output = subprocess.getoutput(rf'm3u8dl.exe "https://hls.media.yangcong345.com/high/high_ef78e40b-85a9-4006-9d21-5d1a00115f3f.m3u8" --workDir "{os.getcwd()}"  --useKeyBase64 "==" --enableDelAfterDone --headers "Referer:https://hls.media.yangcong345.com/high/" ')
output_string = output.encode('utf-8')
output_string_decode = output_string.decode('gbk')
print(output_string_decode)