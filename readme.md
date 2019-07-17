# BoD - mmp files convert(Python program)&emsp;&emsp;[中文文档](https://github.com/Sryml/mmp_convert/blob/master/readme_cn.md#readme)

<div align="center">
  <img alt="GitHub tag (latest SemVer)" src="https://img.shields.io/github/tag/sryml/mmp_convert.svg?color=blue&label=version&style=plastic">
  
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
  packing/unpacking/deleting/adding/generating dat, supporting 8/24/32bpp, is a very convenient software.  
  The only thing missing is automated batch processing and multi-process.
  
<br>
  
You may have guessed the function of `mmp_convert`:sunglasses:
- mmp_convert.py  
  packing/unpacking/adding/generating dat/convert bpp, support 8/24/32bpp, batch automation and multi-process.  
  Need a python environment.


## Instructions
1. You need a Python environment (I use python 3.7)
2. Check if you have pip installed  
  Enter `pip --version` in cmd
3. Install third-party library PIL  
  Enter `pip install Pillow` in cmd
4. Drag the file or folder you want to process to the .bat file

  
## Description
- The mmp_convert program provides four functions
  - unpacking  
    Unpacking mmp, 1 optional parameter:  
    `--bpp`: 8/24/32, default bpp from the original mmp
    ![mmp-unpacking](https://raw.githubusercontent.com/Sryml/Image/master/GIF/mmp-unpacking.gif)
    
    <br>
    
  - packing  
    Pack/add images, 2 optional parameters:  
    `--bpp`: 8/24/32, default bpp from the original image.  
    `-y`: overwrite, no -y does not overwrite.
    ![mmp-packing](https://raw.githubusercontent.com/Sryml/Image/master/GIF/mmp-packing.gif)
    
    <br>
    
  - tobpp  
    Convert to other bpp, 2 optional parameters:  
    `--bpp`: 8/24/32, default 8.  
    `-y`: overwrite, no -y does not overwrite.
    ![mmp-tobpp](https://raw.githubusercontent.com/Sryml/Image/master/GIF/mmp-tobpp.gif)
    
    <br>
    
  - todat  
    Generate a list of names to dat.
    ![mmp-todat](https://raw.githubusercontent.com/Sryml/Image/master/GIF/mmp-todat.gif)
    
    <br>
    
- Support multi-process to quickly process files.
- There is no delete function at this time, please repack it.

  
## Known issues
- If the error "Command line is too long", it is because there are too many files selected. Put these files in a folder and drag the folder to handle it. The result of this is that only one parameter folder path is passed.

