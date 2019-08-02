# BoD - mmp files convert(Python program)&emsp;&emsp;[中文文档](https://github.com/Sryml/mmp_convert/blob/v1.0/readme_cn.md#readme)

<div align="center">
  <img alt="GitHub release" src="https://img.shields.io/github/release/sryml/mmp_convert.svg?style=plastic">
  
  <img alt="GitHub last commit" src="https://img.shields.io/github/last-commit/sryml/mmp_convert.svg?style=plastic">

<a href="http://www.arokhslair.net/forum/viewforum.php?f=24" target="_blank">
    <img src="https://img.shields.io/badge/Blade-mmp__convert-blue.svg?style=plastic&logo=appveyor" alt="mmp_convert">
  </a>
</div>

<br>

July 2019 by Sryml

## Why write this program?
There are 3 mmp programs on the current network:  
- RAS's BaB  
  It seems that it can't package 32bpp images, and it can only be packaged and cannot be unpacked.
  
- mmp_dump  
  The command line starts, it can only unpack and can not be packaged, can not unpack 32bpp images.
  
- SGIMMPWorkstation  
  By SGI. All features are perfect.  
  packing/unpacking/deleting/adding/generating dat, support 8/24/32bpp, is a very convenient software.  
  The only downside is its automated batch processing and multithreading.
  
<br>
  
You may have guessed the function of `mmp_convert`:sunglasses:
- mmp_convert.py  
  packing/unpacking/deleting/adding/generating dat/convert bpp/convert format, support 8/24/32bpp, batch automation and multi-process.  
  The most important thing: the python environment


## Instructions
1. You need a Python environment (I use python 3.7)
2. Check if you have pip installed  
  Enter `pip --version` in cmd
3. Install third-party library PIL  
  Enter `pip install Pillow` in cmd
4. Drag the file or folder you want to process to the `.bat` file

P.s. Adjust the variable `CPU_COUNT` in the `mmp_convert.py` file to reduce cpu usage.


## Functional description
#### Supported formats
- bmp, jpeg, png, webp

#### unpacking  
- Unpacking MMP  
- 1 required parameter  
  `--path`: File or folder paths.
- 1 optional parameter  
  `--bpp`: 8/24/32, default bpp from the original mmp.  

![mmp-unpacking](https://raw.githubusercontent.com/Sryml/Image/master/GIF/mmp-unpacking.gif)

<br>

#### packing  
- Pack/add images to MMP  
- 1 required parameter  
  `--path`: File or folder paths.
- 2 optional parameter  
  `--bpp`: 8/24/32, default bpp from the original image.  
  `-y`: overwrite, no -y does not overwrite.  

![mmp-packing](https://raw.githubusercontent.com/Sryml/Image/master/GIF/mmp-packing.gif)

<br>

#### tobpp  
- Convert MMP to other bpp  
- 1 required parameter  
  `--path`: File or folder paths.
- 3 optional parameter  
  `--bpp`: 8/24/32, default 8.  
  `-max`: resolution(Allow the largest edge, ignoring the image below the maximum).  
  `-y`: overwrite, no -y does not overwrite.  

32bpp-1024 To 8bpp-768:  
![mmp-tobpp](https://raw.githubusercontent.com/Sryml/Image/master/GIF/mmp-tobpp.gif)

<br>

#### todat  
- Generate a list of names to dat  
- 1 required parameter  
  `--path`: File or folder paths.  

MMP To Dat:  
![mmp-todat](https://raw.githubusercontent.com/Sryml/Image/master/GIF/mmp-todat.gif)

<br>

#### remove  
- Delete images in mmp file  
- 1 required parameter  
  `--path`: File path.
- Enter multiple numbers separated by spaces to delete images.  

MMP Remove:  
![mmp-remove](https://raw.githubusercontent.com/Sryml/Image/master/GIF/mmp-remove.gif)

<br>

#### toImg
- Image format convert  
- 2 required parameter  
  `--path`: File or folder paths.  
  `--output`: Output format.
- 4 optional parameter  
  `--bpp`: 8/24/32/Alpha, default bpp from the original image.  
  `-max`: resolution(Allow the largest edge, ignoring the image below the maximum).  
  `--scale`: Zoom factor, such as `4x` or `0.25x`.  
  `-y`: overwrite, no -y does not overwrite.  
  
BMP To PNG:  
![mmp-toImg](https://raw.githubusercontent.com/Sryml/Image/master/GIF/mmp-toImg.gif)

<br>

#### StdUnify
- Files Unification  
  Uniform name/Uniform format/File remapping  
- 1 required parameter  
  `--path`: File or folder paths.  
- 2 optional parameter  
  `--format`: File format  
  `-kl`: Extract the file in the specified format and maintain the directory hierarchy; otherwise give the file a unique ID and move to the same directory  

Uniform name:  
![ReStdUnify](https://raw.githubusercontent.com/Sryml/Image/master/GIF/mmp-StdUnify.gif)

File remapping:  
![ReStdUnify](https://raw.githubusercontent.com/Sryml/Image/master/GIF/mmp-ReStdUnify.gif)

Uniform format:  
None

  
## Update log
### v1.1
`[+]`Added function `StdUnify` - Files Unification(Uniform name or uniform format).  
`[+]`Increase the `toImg` function's parameter `--scale`, scale the image proportionally.  
`[^]`Fix `tobpp` MMP files of the same bpp cannot convert resolution.  

<br>

### v1.0
`[+]`Added function `remove` - Delete images in mmp file.  
`[+]`Added function `toImg` - Image format convert.  
`[+]`Added font color, green progress bar.  

`[^]`Fixing images with Alpha directly converted to 8bpp causes distortion (first converted to 24bpp and then to 8bpp).  
`[^]`Improve pre-parsed files.  
`[^]`Other code modifications.

<br>
  
### v0.9
- The mmp_convert program provides four functions  
  unpacking, packing, tobpp, todat
- Support multi-process to quickly process files.

  
## Known issues
- If the error `Command line is too long`, it is because there are too many files selected. Put these files in a folder and drag the folder to handle it. The result of this is that only one parameter folder path is passed.

