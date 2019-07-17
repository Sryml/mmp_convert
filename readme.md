# BoD - mmp files convert(Python program)

- July 2019 by Sryml
- sryml@hotmail.com
- version 0.9

## 为什么写这个程序？
先说下三个mmp文件处理程序的功能：
- RAS's BaB
  它似乎无法打包32bpp图片，而且只能打包不能解包。
- mmp_dump
  命令行启动，只能解包不能打包，无法解包32bpp图片。
- SGIMMPWorkstation
  SGI做的程序，所有功能都很完美。打包/解包/删除/添加/创建dat，支持8/24/32bpp，是一个很方便的软件。它唯一缺少的是自动化批量处理和多进程。
  

- mmp_convert.py
  你可能已经猜到了它的功能
  打包/解包/添加/创建dat/转换bpp，支持8/24/32bpp，批量自动化和多进程。
  需要python环境


## 使用方法
- 1. 你需要一个Python环境(我使用python 3.7)
- 2. 检查你是否安装了pip
  在cmd输入pip --version
- 3. 安装第三方库PIL
  在cmd输入pip install Pillow
- 4. 拖动需要处理的文件或文件夹到.bat文件上

  
## 描述
- mmp_convert程序提供了四个功能
  - packing
    打包/添加图片,2个可选参数
    --bpp: 8/24/32，默认为原图片位数
    -y: 覆盖，没有-y则不覆盖
    
  - unpacking
    解包mmp，1个可选参数
    --bpp: 8/24/32，默认为原mmp位数
    
  - tobpp
    转换到其它位数，2个可选参数
    --bpp: 8/24/32，默认为8
    -y: 覆盖，没有-y则不覆盖
    
  - todat
    生成dat名称列表
    
- 支持多进程快速处理文件
- 暂时没有删除功能，请重新打包即可

  
## 已知问题
- 如果提示错误“命令行太长”，是因为选中的文件太多。请将文件放在一个文件夹里，再将这个文件夹拖动即可处理。这样的效果是只传递了一个文件夹路径。

