# -*- coding: utf-8 -*-
# python 3.7.2
# 2019/07/16 by sryml.

import os
import io
import struct
import threading
import json
import shutil

from argparse import ArgumentParser
from binascii import crc32
from time import sleep
from math import ceil
from timeit import timeit
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from multiprocessing import Manager
from queue import Queue
from ctypes import windll
from sys import stdout

#
from PIL import Image

# -------------------
CPU_COUNT = max(os.cpu_count()-1, 1)
TIMER = None

# -------------------
class Unbuffered(object):
   def __init__(self, stream):
       self.stream = stream
   def write(self, data):
       self.stream.write(data)
       self.stream.flush()
   def __getattr__(self, attr):
       return getattr(self.stream, attr)
stdout = Unbuffered(stdout)


def GenerateName(root, type_='dir', n=0):
    name = os.path.join(root, '_tmp {}'.format(n))
    if type_ == 'dir':
        return not os.path.isdir(name) and name or \
            GenerateName(root, type_, n+1)
    elif type_ == 'file':
        return not os.path.isfile(name) and name or \
            GenerateName(root, type_, n+1)


def image_convert(img, mode):
    if img.mode!=mode:
        if mode=='P':
            if img.mode == 'RGBA':
                img = img.convert('RGB')
            return img.convert(mode, palette=Image.ADAPTIVE, colors=256)
        else:
            return img.convert(mode)
    return img
    
def IMG_resize(img, maxsize):
    im_size= img.size
    im_size_max =  max(im_size[0], im_size[1])
    if im_size_max > maxsize:
        if im_size[0] == im_size[1]:
            resize = [maxsize]*2
        else:
            scale = maxsize/im_size_max
            idx = im_size.index(im_size_max)
            resize = [maxsize, round(im_size[1-idx]*scale)]
            if idx==1:
                resize.reverse()
        return (1, img.resize(resize, Image.ANTIALIAS))
    return (0, img)


def progress_bar(maximum, q, fix_count=None, run=1):
    global TIMER
    if fix_count and not fix_count.empty():
        num = fix_count.get()
        maximum -= num
        if maximum <= 0:
            print ('\r',' '*60, end='')
            return
    period = 1/40
    block  = 0.05 # 100%/20%
    current = q.qsize()

    bar1   = '\r %3d%% ['
    bar2   = '%s'
    bar3   = '%s'
    bar4   = ']  %{}d/{}'.format(len(str(maximum)),maximum)
    ratio  = min(current/maximum, 1.0)
    num_up = int(ratio/block)
    up     = '█' * num_up
    down   = '▓' * (20-num_up) #▓□
    r      = ratio * 100
    #
    cmd_font.SetColor(cmd_font.LightGreen)
    stdout.write(bar1 % (r,))
    stdout.write(bar2 % (up,))
    
    cmd_font.SetColor()
    stdout.write(bar3 % (down,))
    
    cmd_font.SetColor(cmd_font.LightGreen)
    stdout.write(bar4 % (current,))
    #
    if not run:
        if r < 100:
            print ('\r',' '*60, end='')
        else:
            print ('\n')
        return

    if not TIMER.interval:
        progress_bar(maximum, q, fix_count, run=0)
        return
    TIMER = threading.Timer(period, progress_bar, (maximum, q, fix_count))
    TIMER.start()
    
def progress_bar2(str_, n=0):
    global TIMER
    if not TIMER.interval:
        print (str_,'done.', end='')
        return
    period = 1/10
    lst = ("\\", "|", "/", "-")
    print ('{}{}'.format(str_, lst[n]), end='')
    n = n-3 and n+1
    TIMER = threading.Timer(period, progress_bar2, (str_, n))
    TIMER.start()
        
        
def read_file(file, seek, size):
    return [file.seek(seek)] and file.read(size)


ERROR_NAME = 0
def str_codec(str_, method='decode'):
    global ERROR_NAME
    codecs = ['ISO-8859-1','utf-8']
    for codec in codecs:
        try: return eval('str_.{}(codec)'.format(method))
        except: pass
    ERROR_NAME += 1
    return 'ErrorName_{}'.format(ERROR_NAME)
    
   

    
#################################################
class mmp_convert(object):
    getmode    = {1:'P' , 2:'L' , 3:'P' , 4:'RGB' , 5:'RGBA'}
    bpp2mode   = {'8':'P' , '24':'RGB' , '32':'RGBA' , 'Alpha':'L'}
    gettype    = {'P':1 , 'L':2 , 'PaletteAlpha':3 , 'RGB':4 , 'RGBA':5}

    Palette         = 1
    Alpha           = 2
    PaletteAlpha    = 3
    TrueColour      = 4
    TrueColourAlpha = 5

    valid_format    = ('.bmp','.png','.jpg','.jpeg','.webp')
    # -------------------
    def __init__(self):
        self.bpp     = None
        self.output  = None
        self.maxsize = None
        self.scale   = None
        self.nTextures = 0
        self.overwrite = False
        self.mmp_paths = []
        self.img_paths = []
        self.dir_paths = []


    #######################
    # mmp unpacking.
    #######################
    def process_unpacking(self, params, FLAG='init'):
        cpu  = CPU_COUNT

        if FLAG == 'init':
            global TIMER
            paths,cmd = params
            str_ = '\rFiles pre-parsing...'
            print (str_, end='')
            if cmd:
                TIMER = threading.Timer(0.01, progress_bar2, (str_,))
                TIMER.start()

            self.mmp_paths = []
            self.nTextures = 0
            for p in paths:
                if os.path.isdir(p):
                    for root, dirs, files in os.walk(p):
                        files = [os.path.join(root,i) for i in files if os.path.splitext(i)[1].lower() == '.mmp']
                        self.mmp_paths.extend(files)
                elif os.path.splitext(p)[1].lower() == '.mmp':
                    self.mmp_paths.append(p)

            for file in self.mmp_paths:
                with open(file,'rb') as f:
                    self.nTextures += struct.unpack('<I', f.read(4))[0]
            if TIMER:
                TIMER.interval = 0
                sleep(0.2)
            print ('\n')
                    
            if not self.nTextures:
                print ('No mmp file!')
                return

            #--------------------------------
            print ('mmp unpacking...\n')
            # 多进程通信管理
            manager = Manager()
            q = manager.Queue()
            fix_count = manager.Queue()
            # 控制台模式下创建进度条
            if cmd:
                TIMER = threading.Timer(0.1, progress_bar, (self.nTextures, q, fix_count))
                TIMER.start()

            # 开启多进程任务分配
            pool = ProcessPoolExecutor(cpu)
            futures = []
            for task in self.mmp_paths:
                future = pool.submit(self.process_unpacking, (task,q,fix_count), FLAG='Process')
                futures.append(future)
            pool.shutdown()
            if TIMER:
                TIMER.interval = 0
                sleep(0.2)
                cmd_font.SetColor()
            qsize = q.qsize()

            length = len(self.mmp_paths)
            print ('\r%d mmp files unpacking done! Generate %d images.' % (length, qsize))
            for future in futures:
                results = future.result()
                if results:
                    for msg in results:
                        print (msg)
            print ('')
        elif FLAG == 'Process':
            file, q, fix_count = params
            error_msg = []

            mmp_file= open(file,'rb')
            nTextures= struct.unpack('<I', mmp_file.read(4))[0] #读取小端数据4字节无符号整型

            MMP_MAP = []
            EOF = os.path.getsize(file)
            for i in range(nTextures):
                two,checksum,size,name_len\
                     = struct.unpack('<HIII', mmp_file.read(14))
                if two != 2:
                    fix_count.put(nTextures)
                    mmp_file.close()
                    str_ = 'Error: "{}" Invalid file.'.format(os.path.split(file)[1])
                    return [str_]

                name = mmp_file.read(name_len)
                im_type,width,height\
                     = struct.unpack('<III', mmp_file.read(12))
                
                start_seek = mmp_file.tell()
                end_seek = mmp_file.seek(size-12, 1)
                name = str_codec(name)
                MMP_MAP.append(
                    (
                    ''.join([name,'.bmp']),
                    im_type, width, height,
                    (start_seek, end_seek - start_seek)
                    )
                )

                if mmp_file.tell() >= EOF:
                    nCurrents = i+1
                    if nCurrents != nTextures:
                        fix_count.put(nTextures-nCurrents)
                        str_ = 'Warning: {} file show {}, get {}.'.format(os.path.split(file)[1], nTextures, nCurrents)
                        error_msg.append(str_)
                    break
            
            unpack_dir= os.path.splitext(file)[0]
            if not os.path.exists(unpack_dir):
                os.makedirs(unpack_dir)
            # 将每块图像数据分配给多线程处理保存
            lock = Queue(maxsize=1)
            pool = ThreadPoolExecutor(4)
            futures = []
            for task in MMP_MAP:
                future = pool.submit(
                    self.process_unpacking,
                    (
                    task,
                    q,
                    unpack_dir,
                    mmp_file,
                    lock
                    ),
                    FLAG='Thread'
                )
                futures.append(future)
            pool.shutdown()
            mmp_file.close()
            return error_msg
        elif FLAG == 'Thread':
            bpp = self.bpp
            name,im_type,width,height,data_seek = params[0]
            q, unpack_dir, mmp_file, lock = params[1:]
            
            lock.put(1)
            data = read_file(mmp_file, data_seek[0], data_seek[1])
            lock.get()
            
            if im_type == self.Palette:
                img= Image.frombytes(self.getmode[im_type],(width,height),data[:-768])
                # 调色板像素乘以4恢复亮度
                palette= map(lambda i:min(i<<2 , 255),data[-768:])
                img.putpalette(palette)
            else:
                img= Image.frombytes(self.getmode[im_type],(width,height),data)
            if bpp in self.bpp2mode:
                img = image_convert(img, self.bpp2mode[bpp])

            im_path = os.path.join(unpack_dir, name)
            img.save(im_path)
            q.put(1)
            
    def unpacking(self, paths=[], bpp=None, cmd=False):
        if cmd:
            paths = parse_args.path
            self.bpp = parse_args.bpp
        else:
            self.bpp = bpp

        sec = timeit(lambda:self.process_unpacking((paths,cmd)), number=1)
        print ('Time used: {:.2f} sec\n'.format(sec))
        

    #######################
    # Image packing.
    #######################
    def process_packing(self, params, FLAG='init'):
        cpu  = CPU_COUNT

        if FLAG == 'init':
            global TIMER
            paths, cmd = params
            str_ = '\rFiles pre-parsing...'
            print (str_, end='')
            if cmd:
                TIMER = threading.Timer(0.01, progress_bar2, (str_,))
                TIMER.start()

            self.dir_paths = []
            self.nTextures = 0
            for p in paths:
                for root, dirs, files in os.walk(p):
                    files = [i for i in files if os.path.splitext(i)[1].lower() in self.valid_format]
                    if files:
                        self.dir_paths.append((root,files))
                        self.nTextures += len(files)
            if TIMER:
                TIMER.interval = 0
                sleep(0.2)
            print ('\n')

            if not self.nTextures:
                print ('No Image!')
                return

            #------------------------------
            print ('bmp packing...\n')
            # 多进程通信管理
            manager = Manager()
            q = manager.Queue()
            # 控制台模式下创建进度条
            if cmd:
                TIMER = threading.Timer(0.1, progress_bar, (self.nTextures, q))
                TIMER.start()

            # 开启多进程任务分配
            pool = ProcessPoolExecutor(cpu)
            futures = []
            for task in self.dir_paths:
                future = pool.submit(self.process_packing, (task,q), FLAG='Process')
                futures.append(future)
            pool.shutdown()
            if TIMER:
                TIMER.interval = 0
                sleep(0.2)
                cmd_font.SetColor()
            qsize = q.qsize()

            length = len(self.dir_paths)
            print ('\r%d images processed done! A total of %d mmp files:\n' % (qsize, length))
            hr = 0
            for i in futures:
                result = i.result()
                if result:
                    if not hr:
                        cmd_font.SetColor(cmd_font.Aqua)
                        stdout.write(''.join(['-'*79, '\n']))
                        hr = 1
                    stdout.write (''.join([result, '\n']))
            if hr:
                stdout.write(''.join(['-'*79, '\n']))
                cmd_font.SetColor()
                print ('')

        elif FLAG == 'Process':
            root, files = params[0] # abs path, files name
            q = params[1]
            
            old_nTextures = [0,0]
            nOverwrites   = 0
            nIgnores      = 0
            results       = ['new "', os.path.split(root)[1], '.mmp"', ": ", "add textures ", "{add}", "."]
            
            mmp_name      = ''.join([root,'.mmp'])
            # 如果mmp文件已存在则继续添加贴图
            if os.path.exists(mmp_name):
                mmp_file = open(mmp_name,'rb+')
                if os.path.getsize(mmp_name) >= 4:
                    old_nTextures = [struct.unpack('<I', mmp_file.read(4))[0]] * 2
                    # mmp文件图像数据区段映射
                    MMP_MAP = []
                    for i in range(old_nTextures[1]):
                        start_seek = mmp_file.tell()
                        two,checksum,size,name_len = struct.unpack('<HIII', mmp_file.read(14))
                        name = mmp_file.read(name_len)
                        end_seek = mmp_file.seek(size,1) # current_pos + size
                        MMP_MAP.append((str_codec(name), start_seek, end_seek - start_seek))
                    
                    FILES_LOWER = [os.path.splitext(i)[0].lower() for i in files]
                    MMP_MAP_LOWER = [i[0].lower() for i in MMP_MAP]

                    repeats = set()
                    if self.overwrite:
                        for idx,name in enumerate(MMP_MAP_LOWER):
                            if name in FILES_LOWER:
                                repeats.add(MMP_MAP[idx])
                                nOverwrites += 1
                        MMP_MAP = set(MMP_MAP) - repeats
                        old_nTextures[1] = old_nTextures[0] - nOverwrites
                        if nOverwrites:
                            mmp_tmp = mmp_name+'_tmp_'
                            with open(mmp_tmp,'wb+') as tmp:
                                os.popen('attrib +h "{}"'.format(mmp_tmp))
                                tmp.write(struct.pack('<I', old_nTextures[1]))
                                for i in MMP_MAP:
                                    mmp_file.seek(i[1])
                                    tmp.write(mmp_file.read(i[2]))
                            mmp_file.close()
                            os.remove(mmp_name)
                            os.rename(mmp_tmp,mmp_name)
                            os.popen('attrib -h "{}"'.format(mmp_name))
                            mmp_file = open(mmp_name,'rb+')
                        results[-1] = ', overwrite {}.'.format(nOverwrites)
                    else:
                        for idx,name in enumerate(FILES_LOWER):
                            if name in MMP_MAP_LOWER:
                                repeats.add(files[idx])
                                nIgnores += 1
                                q.put(1)
                        files = set(files) - repeats
                        results[-1] = ', ignore {}.'.format(nIgnores)
                    mmp_file.seek(0,2)
                results[0] = 'old "'
                results[3] = ' has {}, now {}: '.format(old_nTextures[0], '{now}')
            else:
                mmp_file= open(mmp_name,'wb+')
            if old_nTextures[0] == 0:
                mmp_file.seek(0)
                mmp_file.write(struct.pack('<I', 0)) #保留头4个字节
            # -------------------
            # 将每个图像文件分配给多线程编码为mmp字节
            nTextures = 0
            new_nTextures = old_nTextures[1]
            if files:
                data_q = Queue()
                pool = ThreadPoolExecutor(4)
                futures = []
                for file in files:
                    future = pool.submit(self.process_packing, ((root,file), data_q), FLAG='Thread')
                    futures.append(future)

                for i in range(len(files)):
                    data = data_q.get()
                    if data:
                        mmp_file.write(data.getvalue())
                        nTextures += 1
                    q.put(1)
                pool.shutdown()

                new_nTextures += nTextures
                mmp_file.seek(0)
                mmp_file.write(struct.pack('<I', new_nTextures))
                mmp_file.close()
            return ''.join(results).format(
                add = nTextures - nOverwrites,
                now = new_nTextures
                )

        elif FLAG == 'Thread':
            bpp    = self.bpp
            root, file_name = params[0]
            data_q = params[1]

            file = os.path.join(root, file_name)
            BytesIO = io.BytesIO()
            try:
                img= Image.open(file)

                isbmp = img.format == 'BMP'
                mode  = (bpp in self.bpp2mode) and self.bpp2mode[bpp] or img.mode
                img   = image_convert(img,mode)

                # 检查调色板
                palette = b''
                if mode=='P':
                    # 调色板像素除以4适应BoD
                    palette= map(lambda i: i>>2, img.getpalette())

                im_size  = img.size
                # 因为PIL不会读取BMP的alpha，手动给32位BMP添加alpha
                if isbmp and (not bpp or bpp=='32'):
                    with open(file, 'rb') as old:
                        old.seek(18)
                        biWidth, biHeight, biPlanes, biBitCount, biCompression, biSizeImage = struct.unpack('<IIHHII', old.read(20))

                        if biBitCount==32:
                            mode= 'RGBA'
                            img= img.convert(mode)
                            old.seek(54)
                            # 跳过BGR三个字节取Alpha，步长为4
                            alpha= Image.frombytes('L', im_size, old.read()[3::4])
                            # 检查行序是否翻转
                            if biWidth*biHeight <= biSizeImage:
                                alpha= alpha.transpose(Image.FLIP_TOP_BOTTOM)
                            img.putalpha(alpha)

                # 所有图片都得保存为BMP格式
                img.save(BytesIO, 'bmp')

                # 将图片数据及信息转换成字节
                bmp_data = BytesIO.getvalue
                im_data  = img.tobytes() + bytes(palette)
                
                CRC32= crc32(bmp_data()) # 校检和保留0似乎也没影响，这里我使用crc32

                name = str_codec(os.path.splitext(file_name)[0], 'encode')
                two,checksum,size,name_len = 2, CRC32, len(im_data)+12, len(name)
                im_type,width,height       = self.gettype[mode], im_size[0], im_size[1]

                BytesIO.seek(0)
                BytesIO.write(struct.pack('<HIII', two,checksum,size,name_len))
                BytesIO.write(name)
                BytesIO.write(struct.pack('<III', im_type,width,height))
                BytesIO.write(im_data)
                BytesIO.truncate()

                data_q.put(BytesIO)
            except:
                data_q.put(False)

    def packing(self, paths=[], bpp=None, overwrite=False, cmd=False):
        if cmd:
            paths = parse_args.path
            self.bpp = parse_args.bpp
            self.overwrite = parse_args.yes
        else:
            self.bpp = bpp
            self.overwrite = overwrite

        sec = timeit(lambda:self.process_packing((paths,cmd)), number=1)
        print ('Time used: {:.2f} sec\n'.format(sec))

        
    ############################
    # Convert MMP to other bpp.
    ############################
    def process_tobpp(self, params, FLAG='init'):
        cpu  = CPU_COUNT
       
        if FLAG == 'init':
            global TIMER
            paths, cmd = params
            str_ = '\rFiles pre-parsing...'
            print (str_, end='')
            if cmd:
                TIMER = threading.Timer(0.01, progress_bar2, (str_,))
                TIMER.start()
            
            self.mmp_paths = []
            self.nTextures = 0
            for p in paths:
                if os.path.isdir(p):
                    for root, dirs, files in os.walk(p):
                        files = [os.path.join(root,i) for i in files if os.path.splitext(i)[1].lower() == '.mmp']
                        self.mmp_paths.extend(files)
                else:
                    ext_name = os.path.splitext(p)[1].lower()
                    if ext_name == '.mmp':
                        self.mmp_paths.append(p)
            
            for file in self.mmp_paths:
                with open(file,'rb') as f:
                    self.nTextures += struct.unpack('<I', f.read(4))[0]
            if TIMER:
                TIMER.interval = 0
                sleep(0.2)
            print ('\n')

            if not self.nTextures:
                print ('No files need to be converted!')
                return

            #--------------------------------
            print ('mmp converting...\n')
            # 多进程通信管理
            manager = Manager()
            q = manager.Queue()
            fix_count = manager.Queue()
            # 控制台模式下创建进度条
            if cmd:
                TIMER = threading.Timer(0.1, progress_bar, (self.nTextures, q, fix_count))
                TIMER.start()

            # 开启多进程任务分配
            pool = ProcessPoolExecutor(cpu)
            Futures = []
            for task in self.mmp_paths:
                future = pool.submit(self.process_tobpp, (task,q,fix_count), FLAG='Process')
                Futures.append(future)
            pool.shutdown()
            if TIMER:
                TIMER.interval = 0
                sleep(0.2)
                cmd_font.SetColor()

            error_lst = []
            nRepeats = nErrors = 0
            repeat_msg = error_msg = ''
            for i in Futures:
                result = i.result()
                if result:
                    type_, file = result
                    self.mmp_paths.remove(file)
                    if type_ == 1:
                        error_lst.append(
                            'Error: "{}" Invalid file.'.format(os.path.split(file)[1])
                        )
                        nErrors += 1
                    elif type_ == 0:
                        nRepeats += 1
            if nRepeats:
                repeat_msg = ' Repeat Images {}.'.format(nRepeats)
            if nErrors:
                error_msg  = ' Error MMP {}.'.format(nErrors)
            mmp_length = len(self.mmp_paths)
            
            print ('\r{} mmp files convert to {} bpp done.{}{}'.format(mmp_length, self.bpp, repeat_msg, error_msg))
            for i in error_lst:
                print (i)
            print ('')

        elif FLAG == 'Process':
            file,q,fix_count = params

            mmp_file= open(file,'rb')
            header4b = mmp_file.read(4)
            nTextures= struct.unpack('<I', header4b)[0]

            repeats = 0
            invalid_file = 0
            mode = self.bpp2mode[self.bpp]
            MMP_MAP = []
            for i in range(nTextures):
                two,checksum,size,name_len\
                     = struct.unpack('<HIII', mmp_file.read(14))
                if two != 2:
                    invalid_file = 1
                    break
                name = mmp_file.read(name_len)
                im_type,width,height\
                     = struct.unpack('<III', mmp_file.read(12))
                
                start_seek = mmp_file.tell()
                end_seek = mmp_file.seek(size-12, 1)
                MMP_MAP.append(
                    (
                    two,checksum,size,name_len,
                    name,
                    im_type, width, height,
                    (start_seek, end_seek - start_seek)
                    )
                )
                if self.getmode[im_type]==mode and (not self.maxsize or max(width,height) < self.maxsize):
                    repeats += 1
            if (repeats == nTextures) or invalid_file:
                fix_count.put(nTextures)
                return (invalid_file, file)

            tmp_mmp_name = '{}_tmp'.format(file)
            new_mmp_file = open(tmp_mmp_name,'wb')
            new_mmp_file.write(header4b)

            data_q = Queue()
            lock = Queue(maxsize=1)
            pool = ThreadPoolExecutor(4)
            futures = []
            for task in MMP_MAP:
                future = pool.submit(
                    self.process_tobpp,
                    (
                    task,
                    data_q,
                    mmp_file,
                    lock
                    ),
                    FLAG = 'Thread'
                )
                futures.append(future)

            for i in range(nTextures):
                data = data_q.get()
                new_mmp_file.write(data.getvalue())
                q.put(1)
            pool.shutdown()

            mmp_file.close()
            new_mmp_file.close()
            if self.overwrite:
                os.remove(file)
                os.rename(tmp_mmp_name, file)
            else:
                new_mmp_name = '{}_to{}bpp.mmp'.format(os.path.splitext(file)[0], self.bpp)
                os.rename(tmp_mmp_name, new_mmp_name)
        elif FLAG == 'Thread':
            bpp = self.bpp
            two,checksum,size,name_len,name,\
                im_type,width,height,data_seek\
                = params[0]
            data_q, mmp_file, lock = params[1:]
            
            lock.put(1)
            data = read_file(mmp_file, data_seek[0], data_seek[1])
            lock.get()
            
            BytesIO = io.BytesIO()
            s_mode    = self.getmode[im_type]
            t_mode   = self.bpp2mode[bpp]
            if s_mode == t_mode and (not self.maxsize or max(width,height) < self.maxsize):
                BytesIO.write(struct.pack('<HIII', two,checksum,size,name_len))
                BytesIO.write(name)
                BytesIO.write(struct.pack('<III', im_type,width,height))
                BytesIO.write(data)
                data_q.put(BytesIO)
                return

            if im_type == self.Palette:
                img= Image.frombytes(s_mode, (width,height),data[:-768])
                palette= map(lambda i:min(i<<2 , 255),data[-768:])
                img.putpalette(palette)
            else:
                img= Image.frombytes(s_mode, (width,height),data)
                
            if self.maxsize:
                img = IMG_resize(img, self.maxsize)[1]
                width,height = img.size
            img = image_convert(img, t_mode)
                
            #-----------------------
            # 检查调色板
            palette = b''
            if t_mode=='P':
                # 调色板像素除以4适应BoD
                palette= map(lambda i: i>>2, img.getpalette())

            # 所有图片都得保存为BMP格式
            img.save(BytesIO, 'bmp')

            # 将图片数据及信息转换成字节
            bmp_data = BytesIO.getvalue
            im_data  = img.tobytes() + bytes(palette)
            
            CRC32 = crc32(bmp_data()) # 校检和保留0似乎也没影响，这里我使用crc32

            two,checksum,size,name_len = 2, CRC32, len(im_data)+12, len(name)
            im_type = self.gettype[t_mode]

            BytesIO.seek(0)
            BytesIO.write(struct.pack('<HIII', two,checksum,size,name_len))
            BytesIO.write(name)
            BytesIO.write(struct.pack('<III', im_type,width,height))
            BytesIO.write(im_data)
            BytesIO.truncate()

            data_q.put(BytesIO)

    def tobpp(self, paths=[], bpp='8', maxsize=None, overwrite=False, cmd=False):
        if cmd:
            paths = parse_args.path
            self.bpp = parse_args.bpp or bpp
            self.maxsize = parse_args.maxsize
            self.overwrite = parse_args.yes
        else:
            self.bpp = bpp
            self.maxsize = maxsize
            self.overwrite = overwrite

        sec = timeit(lambda:self.process_tobpp((paths, cmd)), number=1)
        print ('Time used: {:.2f} sec\n'.format(sec))


    #######################
    # create dat files.
    #######################
    def todat(self, paths=[], cmd=False):
        global TIMER
        if cmd:
            paths = parse_args.path

        str_ = '\rFiles pre-parsing...'
        print (str_, end='')
        if cmd:
            TIMER = threading.Timer(0.01, progress_bar2, (str_,))
            TIMER.start()

        mmp_paths = []
        for p in paths:
            if os.path.isdir(p):
                for root, dirs, files in os.walk(p):
                    files = [os.path.join(root,i) for i in files if os.path.splitext(i)[1].lower() == '.mmp']
                    mmp_paths.extend(files)
            elif os.path.splitext(p)[1].lower() == '.mmp':
                mmp_paths.append(p)
        if TIMER:
            TIMER.interval = 0
            sleep(0.2)
        print ('\n')
        
        print ('dat generation...\n')

        error_msg = []
        for file in mmp_paths[:]:
            dat_name = ''.join([file[:-4],'.dat'])
            dat_file = open(dat_name, 'w', encoding='utf-8')
            dat_file.write('1\n')
            with open(file,'rb') as mmp_file:
                nTextures = struct.unpack('<I', mmp_file.read(4))[0]
                for i in range(nTextures):
                    two,checksum,size,name_len = struct.unpack('<HIII', mmp_file.read(14))
                    if two != 2:
                        dat_file.close()
                        os.remove(dat_name)
                        mmp_paths.remove(file)
                        str_ = 'Error: "{}" Invalid file.'.format(os.path.split(file)[1])
                        error_msg.append(str_)
                        break
                    name = str_codec(mmp_file.read(name_len))
                    mmp_file.seek(size,1)
                    s = '{name}.bmp\n{name}\n'.format(name=name)
                    dat_file.write(s)
            dat_file.close()
        print ('{} dat files created done.\n'.format(len(mmp_paths)))
        for i in error_msg:
            print (i)
            
            
    #######################
    # mmp remove.
    #######################
    def remove(self, path=None, names=[], cmd=False):
        if cmd:
            file = parse_args.path[0]
        else:
            file = list(path)[0]
            
        mmp_name = os.path.split(file)[1]
        if os.path.splitext(mmp_name)[1].lower() != '.mmp':
            str_ = 'Error: "{}" Invalid file.\n'.format(mmp_name)
            print (str_)
            return 
            
        global TIMER
        str_ = '\rFiles pre-parsing...'
        print (str_, end='')
        if cmd:
            TIMER = threading.Timer(0.01, progress_bar2, (str_,))
            TIMER.start()
            
        width = 79
        MMP_MAP = {}
        Name2Index= {}
        NameCount = []
        with open(file,'rb') as mmp_file:
            nTextures = struct.unpack('<I', mmp_file.read(4))[0]
            for i in range(nTextures):
                start_seek = mmp_file.tell()
                two,checksum,size,name_len = struct.unpack('<HIII', mmp_file.read(14))
                if two!=2:
                    str_ = '\rError: "{}" Invalid file.\n'.format(mmp_name)
                    if TIMER:
                        TIMER.interval = 0
                        sleep(0.2)
                    print (str_)
                    return
                im_name = str_codec(mmp_file.read(name_len))
                end_seek = mmp_file.seek(size,1) # current_pos + size
                MMP_MAP[i] = (im_name, start_seek, end_seek-start_seek)
                Name2Index[im_name] = i
                NameCount.append(im_name)
        KEY_ORDERED = list(range(nTextures))
        KEY_ORDERED.sort(key=lambda i: MMP_MAP[i][0].lower())
        if TIMER:
            TIMER.interval = 0
            sleep(0.2)
        print ('\r%s' % (' '*width))
        if nTextures == 0:
            print ('Empty file.\n')
            return
        #---------------------------
        errors = []
        numbers = []
        if not names:
            title = '>>> {}\n'.format(mmp_name)
            
            cmd_font.print(title, cmd_font.LightGreen)
            print ('='*width)
            print ('')

            column = 3
            row  = ceil(nTextures / column)
            L_n1 = len(str(row)) + 2
            L_n2 = len(str(row*2)) + 3
            L_n3 = len(str(nTextures)) + 3
            size = (width - L_n1 - L_n2 - L_n3) // column
            num_size = (L_n1, L_n2, L_n3)
            for i in range(row):
                i += 1
                row_n = (i, i+row, i+row*2)
                row_str = []
                for i2,n in enumerate(row_n):
                    if n <= nTextures:
                        key = KEY_ORDERED[n-1]
                        im_name = MMP_MAP[key][0][:size]
                        str_ = '{:>%d}{:<%d}' % (num_size[i2], size)
                        n = '{}. '.format(n)
                        row_str.append([NameCount.count(im_name)>1, str_.format(n, im_name)])
                for l in row_str:
                    if l[0]:
                        cmd_font.print(l[1], cmd_font.LightRed)
                    else:
                        stdout.write(l[1])
                stdout.write('\n')
            print ('-'*width)
            print ('')
            print ('- Please enter numbers, separated by spaces.')
            while True:
                numbers = input('remove: ')
                if numbers.lower() in ('q','exit'):
                    return
                if numbers:
                    break
            numbers = numbers.split()
            for n,str_ in enumerate(numbers[:]):
                try:
                    i = int(str_)-1
                    if i >= nTextures or i < 0:
                        raise IndexError
                    numbers[n] = KEY_ORDERED[i]
                except:
                    numbers.remove(str_)
                    errors.append(str_)
        else:
            for str_ in names:
                if i not in Name2Index:
                    errors.append(str_)
                else:
                    numbers.append(Name2Index[str_])
        tmp = []
        for i in numbers:
            if i not in tmp:
                tmp.append(i)
        numbers = tmp
        if numbers:
            start = 0
            KEY_MMP_KEEP = []
            min_ = min(numbers)
            start = MMP_MAP[min_][1]
            KEY_MMP_KEEP = [i for i in range(min_, nTextures) if i not in numbers]
            with open(file, 'rb') as mmp_file:
                with open(file, 'rb+') as new_mmp_file:
                    if not KEY_MMP_KEEP:
                        new_mmp_file.truncate(start)
                    else:
                        new_mmp_file.seek(start)
                        for i in KEY_MMP_KEEP:
                            seek, size = MMP_MAP[i][1:]
                            mmp_file.seek(seek)
                            data = mmp_file.read(size)
                            new_mmp_file.write(data)
                        new_mmp_file.truncate()

                    new_mmp_file.seek(0)
                    nRemoves = len(numbers)
                    new_nTextures = nTextures - nRemoves
                    new_mmp_file.write(struct.pack('<I', new_nTextures))
            print ('')
            print ('-'*width)
            for i in numbers:
                print ('remove {} done.'.format(MMP_MAP[i][0]))
            print ('-'*width)
            print ('\n{} has {}, remove {}, now {}.\n'.format(
                        mmp_name,
                        nTextures,
                        nRemoves,
                        new_nTextures
                        )
                    )
        if errors:
            print ('Invalid input: {}\n'.format(', '.join(errors)))


    #######################
    # Image format convert.
    #######################
    def process_toImg(self, params, FLAG='init'):
        cpu  = CPU_COUNT

        if FLAG == 'init':
            global TIMER
            paths, cmd = params
            str_ = '\rFiles pre-parsing...'
            print (str_, end='')
            if cmd:
                TIMER = threading.Timer(0.01, progress_bar2, (str_,))
                TIMER.start()

            self.img_paths = []
            self.nTextures = 0
            for p in paths:
                if os.path.isdir(p):
                    split = os.path.split(p)
                    new_dir = '{}_toImg'.format(split[1])
                    new_dir = os.path.join(split[0], new_dir)

                    for root, dirs, files in os.walk(p):
                        files = [(root,i) for i in files if os.path.splitext(i)[1].lower() in self.valid_format]
                        if files and not self.overwrite:
                            new_root = root.replace(p, new_dir)
                            if not os.path.exists(new_root):
                                os.makedirs(new_root)
                            files = [(i[0],i[1], new_root) for i in files]
                        self.img_paths.extend(files)
                        self.nTextures += len(files)
                else:
                    root, name = os.path.split(p)
                    ext_name = os.path.splitext(name)[1].lower()
                    if ext_name in self.valid_format:
                        self.img_paths.append((root, name))
                        self.nTextures += 1
            if TIMER:
                TIMER.interval = 0
                sleep(0.2)
            print ('\n')

            if not self.nTextures:
                print ('No files need to be converted!')
                return

            #--------------------------------
            print ('Image converting...\n')
            # 多进程通信管理
            manager = Manager()
            q = manager.Queue()
            fix_count = manager.Queue()
            # 控制台模式下创建进度条
            if cmd:
                TIMER = threading.Timer(0.1, progress_bar, (self.nTextures, q, fix_count))
                TIMER.start()

            # 开启多进程任务分配
            pool = ProcessPoolExecutor(cpu)
            # pool = ThreadPoolExecutor(cpu)
            Futures = []
            for task in self.img_paths:
                future = pool.submit(self.process_toImg, (task,q,fix_count), FLAG='Process')
                Futures.append(future)
            pool.shutdown()
            if TIMER:
                TIMER.interval = 0
                sleep(0.2)
                cmd_font.SetColor()

            nRepeats = 0
            repeat_msg = ''
            for i in Futures:
                result = i.result()
                if result:
                    type_, item = result
                    self.img_paths.remove(item)
                    nRepeats += 1
            if nRepeats:
                repeat_msg = ' Ignore {} files.'.format(nRepeats)
            img_length = len(self.img_paths)
            
            print ('\r{} Image files convert completed.{}'.format(img_length,repeat_msg))
            print ('')

        elif FLAG == 'Process':
            bpp     = self.bpp
            maxsize = self.maxsize
            scale   = self.scale
            task,q,fix_count = params
            root, im_name    = task[0], task[1]
            name, ext        = os.path.splitext(im_name)
            
            file = os.path.join(root, im_name)
            img = Image.open(file)

            im_size  = img.size
            S_FORMAT = '.{}'.format(img.format.lower())
            T_FORMAT = self.output.replace('jpg','jpeg')
            A_FORMAT = ('.bmp', '.png', '.webp')

            S_MODE   = img.mode
            T_MODE   = bpp and self.bpp2mode[bpp]

            isbmp      = (S_FORMAT == '.bmp')
            T_isAlpha  = T_FORMAT in A_FORMAT

            if isbmp:
                with open(file, 'rb') as f:
                    f.seek(18)
                    biWidth, biHeight, biPlanes, biBitCount, biCompression, biSizeImage = struct.unpack('<IIHHII', f.read(20))

                    S_MODE = self.bpp2mode[str(biBitCount)]
                    img = img.convert(S_MODE)
                    if T_isAlpha and biBitCount == 32:
                        if not bpp or bpp=='32':
                            f.seek(54)
                            # 跳过BGR三个字节取Alpha，步长为4
                            alpha= Image.frombytes('L', im_size, f.read()[3::4])
                            # 检查行序是否翻转
                            if biWidth*biHeight <= biSizeImage:
                                alpha= alpha.transpose(Image.FLIP_TOP_BOTTOM)
                            img.putalpha(alpha)

            is_size   = not scale
            is_bpp    = True #not T_isAlpha or (not bpp)
            #
            is_format = (S_FORMAT == T_FORMAT)
            #
            if maxsize and not scale:
                resize_success, img = IMG_resize(img, maxsize)
                is_size = not resize_success
            elif scale:
                scale  = float(scale[:-1])
                resize = [int(i*scale) for i in im_size]
                img = img.resize(resize, Image.ANTIALIAS)
            #
            if bpp:
                is_bppCheck = 1
                if T_FORMAT == '.jpeg':
                    is_bppCheck = T_MODE not in ('P','RGBA')

                if is_bppCheck:
                    is_bpp = (S_MODE == T_MODE)
                    if not is_bpp:
                        img = image_convert(img, T_MODE)
            else:
                if T_FORMAT == '.jpeg':
                    if S_MODE in ('P','RGBA'):
                        img = image_convert(img, 'RGB')

            if is_format and is_size and is_bpp:
                fix_count.put(1)
                return (0, task)
            #-----------------------------------------
            
            if self.overwrite:
                BytesIO = io.BytesIO()
                img.save(BytesIO, T_FORMAT[1:], quality=95)
                img.close()
                os.remove(file)
                im_path = os.path.join(root, '{}{}'.format(name, self.output))
                with open(im_path, 'wb') as im_file:
                    im_file.write(BytesIO.getvalue())
            else:
                if len(task) > 2:
                    im_path = os.path.join(task[2], '{}{}'.format(name, self.output))
                else:
                    im_path = os.path.join(root, '{}_toImg{}'.format(name, self.output))
                img.save(im_path, quality=95)
            q.put(1)

    def toImg(self, path=[], output=None, bpp=None, maxsize=None, scale=None, overwrite=False, cmd=False):
        if cmd:
            paths = parse_args.path
            self.output  = parse_args.output
            self.bpp     = parse_args.bpp
            self.maxsize = parse_args.maxsize
            self.scale   = parse_args.scale
            self.overwrite = parse_args.yes
        else:
            self.output  = output
            self.bpp     = bpp
            self.maxsize = maxsize
            self.scale   = scale
            self.overwrite = overwrite

        self.output = '.{}'.format(self.output.lower())
        if self.output not in self.valid_format:
            print ('Error: Invalid format "{}"'.format(self.output))
            return
        if self.scale and self.scale[-1].lower() != 'x':
            print ('Error parameter: {}.'.format(self.scale))
            return

        sec = timeit(lambda:self.process_toImg((paths, cmd)), number=1)
        print ('Time used: {:.2f} sec\n'.format(sec))


    #######################
    # Files Unification
    #######################
    def StdUnify(self, path=[], format_=[], keeplevel=False, cmd=False):
        global TIMER
        if cmd:
            path = parse_args.path[0]
            format_ = parse_args.format
            keeplevel = parse_args.keeplevel
        if keeplevel and not format_:
            print ("Please specify the format!\n")
            return

        os.chdir(path)

        FileMapping = './!FileMapping.json'
        if os.path.exists(FileMapping):
            print ('Processing...\n')
            with open(FileMapping, 'r', encoding='utf-8') as f:
                Unifydirs = json.load(f)
            count = Unifydirs.pop('count')

            q = Queue()
            if cmd:
                TIMER = threading.Timer(0.1, progress_bar, (count, q))
                TIMER.start()

            files = []
            for key in Unifydirs:
                sub = Unifydirs[key]
                root = sub.pop('root')
                if root == './':
                    files = sub
                    continue
                if not os.path.exists(root):
                    os.makedirs(root)
                for id_name in sub:
                    shutil.move(
                    os.path.join('.', id_name),
                    os.path.join(root, sub[id_name])
                    )
                    q.put(1)
            if files:
                tmp = GenerateName('.')
                os.makedirs(tmp)
                for id_name in files:
                    shutil.move(
                    os.path.join('.', id_name),
                    os.path.join(tmp, files[id_name])
                    )
                for file in os.listdir(tmp):
                    shutil.move(
                    os.path.join(tmp, file),
                    os.path.join('.', file)
                    )
                    q.put(1)
                os.rmdir(tmp)
            os.remove(FileMapping)

            if TIMER:
                TIMER.interval = 0
                sleep(0.2)
                cmd_font.SetColor()
            print ('{} files <remapping> done.\n'.format(count))
            return

        #------------------------------------------
        print ('Processing...\n')
        format_ = ['.{}'.format(i.lower()) for i in format_]
        count = 0
        nDirs = nFiles = 1
        Unifydirs = {}
        
        basename = os.path.basename(path)
        out_dir = '../{}_StdUnify/'.format(basename)
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)
        if format_:
            for root, dirs, files in os.walk('./'):
                files = [i for i in files if os.path.splitext(i)[1].lower() in format_]
                if files:
                    Unifydirs[nDirs] = {'root':root, 'files':files}
                    if keeplevel:
                        new_root = root.replace('./', out_dir, 1)
                        if not os.path.exists(new_root):
                            os.makedirs(new_root)
                        Unifydirs[nDirs]['t_root'] = new_root
                    count += len(files)
                    nDirs += 1
        else:
            for root, dirs, files in os.walk('./'):
                if files:
                    Unifydirs[nDirs] = {'root':root, 'files':files}
                    count += len(files)
                    nDirs += 1
        q = Queue()
        if cmd:
            TIMER = threading.Timer(0.1, progress_bar, (count, q))
            TIMER.start()

        # root_files = []
        if keeplevel:
            for n in list(Unifydirs.keys()):
                sub = Unifydirs[n]
                root, files = sub['root'], sub.pop('files')
                new_root = sub.pop('t_root')
                for file in files:
                    shutil.move(
                        os.path.join(root, file),
                        os.path.join(new_root, file)
                        )
                    q.put(1)
            os.chdir('../')
            for root, dirs, files in os.walk(basename, topdown=False):
                if not os.listdir(root):
                    os.rmdir(root)

            if TIMER:
                TIMER.interval = 0
                sleep(0.2)
                cmd_font.SetColor()
            print ('{} files <Format Unification> done.\n'.format(count))
        else:
            for n in list(Unifydirs.keys()):
                sub = Unifydirs[n]
                root, files = sub['root'], sub.pop('files')
                for file in files:
                    ext = os.path.splitext(file)[1]
                    id_name = '{}{}'.format(nFiles,ext)
                    sub[id_name] = file
                    shutil.move(
                        os.path.join(root, file),
                        os.path.join(out_dir, id_name)
                        )
                    nFiles += 1
                    q.put(1)
                # if root != './' and not os.listdir(root):
                #     os.
            Unifydirs['count'] = count
            FileMapping = os.path.join(out_dir, '!FileMapping.json')
            with open(FileMapping, 'w', encoding='utf-8') as f:
                json.dump(Unifydirs, f, indent=4, separators=(',',': '), ensure_ascii=False)
            os.chdir('../')
            for root, dirs, files in os.walk(basename, topdown=False):
                if not os.listdir(root):
                    os.rmdir(root)

            if TIMER:
                TIMER.interval = 0
                sleep(0.2)
                cmd_font.SetColor()
            print ('{} files <Name Unification> done.\n'.format(count))




############################################################
############################################################
class CmdFont(object):
    STD_INPUT_HANDLE  = -10
    STD_OUTPUT_HANDLE = -11
    STD_ERROR_HANDLE  = -12
     
    #colors
    # 0 = 黑色       8 = 灰色
    # 1 = 蓝色       9 = 淡蓝色
    # 2 = 绿色       A = 淡绿色
    # 3 = 青色       B = 淡青色
    # 4 = 红色       C = 淡红色
    # 5 = 紫色       D = 淡紫色
    # 6 = 黄色       E = 淡黄色
    # 7 = 白色       F = 亮白色
    Black,    Blue,        Green,       Aqua,\
    Red,      Purple,      Yellow,      White,\
    Gray,     LightBlue,   LightGreen,  LightAqua,\
    LightRed, LightPurple, LightYellow, BrightWhite\
        = [i for i in range(16)]
    
    def __init__(self):
        # get handle
        self.std_out_handle = windll.kernel32.GetStdHandle(self.STD_OUTPUT_HANDLE)
        
    def SetColor(self, color=0x7, bg_color=0, handle=None):
        handle = handle or self.std_out_handle
        if bg_color:
            bg_color = bg_color << 4
        return windll.kernel32.SetConsoleTextAttribute(handle, color | bg_color)

    def print(self, str_, color=0x7, bg_color=0):
        self.SetColor(color, bg_color)
        stdout.write(str_)
        self.SetColor()
            

            
            
########################## INSTANCE WRAPPERS
# mmp_convert
mmp = mmp_convert()

# Cmd Font Color
cmd_font = CmdFont()


# -------------------------------------------
classes_defined = dir()

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument('--type','-t', type=str, default=None, metavar='type')
    parser.add_argument('--func','-f', type=str, default=None, metavar='method')
    parser.add_argument('--bpp', '-b', type=str, default=None, metavar='bpp', choices=['8','24','32','Alpha'])
    parser.add_argument('--path','-p', type=str, default=[],   metavar='file paths', nargs='*')
    parser.add_argument('--maxsize','-max', type=int, default=None,   metavar='maxsize')
    parser.add_argument('--output','-o',    type=str, default=None,   metavar='output')
    parser.add_argument('--format',      type=str, default=[],   metavar='format', nargs='*')
    parser.add_argument('--scale','-s',  type=str, default=None,   metavar='scale')
    parser.add_argument('--keeplevel', '-kl', action='store_true')
    parser.add_argument('--yes', '-y', action='store_true')
    parse_args = parser.parse_args()

    if parse_args.type in classes_defined:
        exec(parse_args.type + '().' + parse_args.func + '(cmd=True)')

"""
mmp.unpacking(paths[, bpp=None])
    :param paths:   [mmp files/folders]
    :param bpp:     8/24/32/Alpha

mmp.packing(paths[, bpp=None, overwrite=False])
    :param paths:   [image folders]
    :param bpp:     8/24/32/Alpha
    :param overwrite:   True/False

mmp.tobpp(paths[, bpp='8', maxsize=None, overwrite=False])
    :param paths:   [mmp files/folders]
    :param bpp:     8/24/32/Alpha
    :param maxsize:     Resolution(largest side)
    :param overwrite:   True/False

mmp.todat(paths)
    :param paths:   [mmp files/folders]

mmp.remove(path, names)
    :param path:    mmp file
    :names:         [texture names]


skip = 4 - (biWidth*biBitCount)>>3 & 3
skip = (skip!=4 and skip) or 0

"""
