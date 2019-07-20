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
4. Drag the file or folder you want to process to the `.bat` file

P.s. Adjust the variable `CPU_COUNT` in the `mmp_convert.py` file to reduce cpu usage.


## Functional description
#### unpacking  
- Unpacking mmp, 1 optional parameter:  
- `--bpp`: 8/24/32, default bpp from the original mmp
![mmp-unpacking](https://raw.githubusercontent.com/Sryml/Image/master/GIF/mmp-unpacking.gif)

<br>

#### packing  
- Pack/add images, 2 optional parameters:  
- `--bpp`: 8/24/32, default bpp from the original image.  
- `-y`: overwrite, no -y does not overwrite.
![mmp-packing](https://raw.githubusercontent.com/Sryml/Image/master/GIF/mmp-packing.gif)

<br>

#### tobpp  
- Convert to other bpp, 3 optional parameters:  
- `--bpp`: 8/24/32, default 8.  
- `-max`: resolution(maximum side), like 768
- `-y`: overwrite, no -y does not overwrite.
![mmp-tobpp](https://raw.githubusercontent.com/Sryml/Image/master/GIF/mmp-tobpp.gif)

<br>

#### todat  
- Generate a list of names to dat.
![mmp-todat](https://raw.githubusercontent.com/Sryml/Image/master/GIF/mmp-todat.gif)

<br>

#### remove  
- Drag the mmp file to `Remove.bat`, which will display all images and numbers.  
- Enter multiple numbers separated by spaces to delete images.
![mmp-remove](https://raw.githubusercontent.com/Sryml/Image/master/GIF/mmp-remove.gif)

  
## Update log
### v1.0
`[+]`Expand `tobpp` function, support direct conversion of image files, support for resolution modification.
`[+]`Add `remove` function - delete images in mmp file
`[+]`Increase font color, green progress bar  
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

