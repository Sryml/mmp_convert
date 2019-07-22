# BoD - mmp files convert(Python program)&emsp;&emsp;[README EN](https://github.com/Sryml/mmp_convert/tree/v1.0#readme)

<div align="center">
  <img alt="GitHub release" src="https://img.shields.io/github/release/sryml/mmp_convert.svg?style=plastic">
  
  <img alt="GitHub last commit" src="https://img.shields.io/github/last-commit/sryml/mmp_convert.svg?style=plastic">

<a href="http://www.arokhslair.net/forum/viewforum.php?f=24" target="_blank">
    <img src="https://img.shields.io/badge/Blade-mmp__convert-blue.svg?style=plastic&logo=appveyor" alt="mmp_convert">
  </a>
</div>

<br>

July 2019 by Sryml

## 为什么写这个程序？
当前网络上3个mmp文件处理程序的功能：
- RAS's BaB  
  它似乎无法打包32bpp图片，而且只能打包不能解包。
  
- mmp_dump  
  命令行启动，只能解包不能打包，无法解包32bpp图片。
  
- SGIMMPWorkstation  
  SGI做的程序，所有功能都很完美。打包/解包/删除/添加/创建dat，支持8/24/32bpp，是一个很方便的软件。  
  它唯一缺少的是自动化批量处理和多进程。
  
<br>
  
你可能已经猜到了`mmp_convert`的功能:sunglasses:
- mmp_convert.py  
  打包/解包/添加/创建dat/转换bpp，支持8/24/32bpp，批量自动化和多进程。  
  需要python环境。


## 使用方法
1. 你需要一个Python环境 (我使用python 3.7)
2. 检查你是否安装了pip  
  在cmd输入`pip --version`
3. 安装第三方库PIL  
  在cmd输入`pip install Pillow`
4. 拖动需要处理的文件或文件夹到`.bat`文件上  

p.s. 调整`mmp_convert.py`文件中的变量`CPU_COUNT`可降低cpu使用率


## 功能描述
#### 支持的格式
- bmp, jpeg, png, webp

#### unpacking  
- 解包MMP  
- 1个必须参数  
  `--path`: 文件或文件夹路径
- 1个可选参数  
  `--bpp`: 8/24/32，默认为原mmp位数  
![mmp-unpacking](https://raw.githubusercontent.com/Sryml/Image/master/GIF/mmp-unpacking.gif)
  
<br>
  
#### packing  
- 打包/添加图片到MMP  
- 1个必须参数  
  `--path`: 文件或文件夹路径
- 2个可选参数  
  `--bpp`: 8/24/32，默认为原图片位数  
  `-y`: 覆盖，没有-y则不覆盖  
![mmp-packing](https://raw.githubusercontent.com/Sryml/Image/master/GIF/mmp-packing.gif)

<br>

#### tobpp  
- 转换MMP到其它位数  
- 1个必须参数  
  `--path`: 文件或文件夹路径
- 2个可选参数  
  `--bpp`: 8/24/32，默认为8  
  `-y`: 覆盖，没有-y则不覆盖
32bpp-1024 To 8bpp-768:  
![mmp-tobpp](https://raw.githubusercontent.com/Sryml/Image/master/GIF/mmp-tobpp.gif)

<br>

#### todat  
- 生成dat名称列表  
- 1个必须参数  
  `--path`: 文件或文件夹路径
MMP To Dat:  
![mmp-todat](https://raw.githubusercontent.com/Sryml/Image/master/GIF/mmp-todat.gif)

<br>

#### remove  
- 删除MMP文件中的图像  
- 1个必须参数  
  `--path`: 文件路径
- 输入多个序号以空格分隔可以删除图像。
MMP Remove:  
![mmp-remove](https://raw.githubusercontent.com/Sryml/Image/master/GIF/mmp-remove.gif)

#### toImg
- 图像格式转换  
- 2个必须参数  
  `--path`: 文件或文件夹路径  
  `--output`: 输出格式
- 3个可选参数  
  `--bpp`: 8/24/32/Alpha，默认为原图片位数。  
  `-max`: 分辨率（最大的边），像768  
  `-y`: 覆盖，没有-y则不覆盖
BMP To PNG:  
![mmp-toImg](https://raw.githubusercontent.com/Sryml/Image/master/GIF/mmp-toImg.gif)
  
  
## 更新日志
### v1.0
`[+]`新增功能`remove` - 删除MMP文件中的图像。  
`[+]`新增功能`toImg` - 图像格式转换。  
`[+]`新增字体颜色，绿色的进度条。  

`[^]`修复带Alpha的图像直接转换为8bpp导致失真（先转为24bpp再转为8bpp）。  
`[^]`改善预解析文件。  
`[^]`其它代码修改。

<br>
  
### v0.9
- mmp_convert程序提供了四个功能  
  unpacking, packing, tobpp, todat
- 支持多进程快速处理文件

  
## 已知问题
- 如果提示错误`命令行太长`，是因为选中的文件太多。请将文件放在一个文件夹里，再将这个文件夹拖动即可处理。这样的效果是只传递了一个文件夹路径。

