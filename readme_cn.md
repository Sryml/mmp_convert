# BoD - mmp files convert(Python program)&emsp;&emsp;[README EN](https://github.com/Sryml/mmp_convert/tree/v1.12#readme)

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
  SGI做的程序，所有功能都很完美。打包/解包/删除/添加/创建dat...支持8/24/32bpp，是一个很方便的软件。  
  它唯一不足的是批量处理。
  
<br>
  
我希望可以通过更方便的方式处理某些事情，所以`mmp_convert`诞生了:sunglasses:
- mmp_convert.py  
  打包/解包/删除/添加/创建dat/转换bpp/转换格式...支持8/24/32bpp，批量自动化和多进程。  
  最重要的一件事：python环境


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
- 3个可选参数  
  `--bpp`: 8/24/32，默认为8  
  `-max`: 分辨率（允许最大的边，忽略最大值以下的图像）  
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

<br>

#### toImg
- 图像格式转换  
- 2个必须参数  
  `--path`: 文件或文件夹路径  
  `--output`: 输出格式
- 5个可选参数  
  `--bpp`: 8/24/32/Alpha，默认为原图片位数。  
  `-max`: 分辨率（允许最大的边，忽略最大值以下的图像）  
  `--scale`: 缩放倍数，例如`4x`或`0.25x`。  
  `--quality`: JPG图像质量，默认为95。  
  `-y`: 覆盖，没有-y则不覆盖  
  
BMP To PNG:  
![mmp-toImg](https://raw.githubusercontent.com/Sryml/Image/master/GIF/mmp-toImg.gif)

<br>

#### StdUnify
- 文件统一化  
  统一名字/统一格式/文件重映射  
- 1个必须参数  
  `--path`: 文件或文件夹路径  
- 2个可选参数  
  `--format`: 文件格式  
  `-kl`: 提取指定格式的文件并保持目录层次; 否则给文件唯一ID并移动到同一个目录  

统一名字:  
![ReStdUnify](https://raw.githubusercontent.com/Sryml/Image/master/GIF/mmp-StdUnify.gif)

文件重映射:  
![ReStdUnify](https://raw.githubusercontent.com/Sryml/Image/master/GIF/mmp-ReStdUnify.gif)

统一格式:  
None

<br>

#### swapBGR
- 图像通道转换（RGB与BGR）  
- 1个必须参数  
  `--path`: 文件或文件夹路径  
- 1个可选参数  
  `--quality`: JPG图像质量，默认为95。  

  
## 更新日志
### v1.12
`[+]`新增功能`swapBGR` - 图像通道转换。  
`[^]``toImg`增加图像质量可选参数`quality`（适用于JPG格式）。  

<br>

### v1.1
`[+]`新增功能`StdUnify` - 文件统一化（统一名字或统一格式）。  
`[+]`增加`toImg`功能的参数`--scale` - 按比例缩放图像。  
`[^]`修复`tobpp`相同bpp的MMP文件无法转换分辨率。  

<br>

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

