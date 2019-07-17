# -*- coding: utf-8 -*-
# python 3.7.2
# 2019/07/16 by sryml.

import os
import io
import binascii
import struct
import argparse
import threading
import time

from timeit import timeit
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from multiprocessing import Manager
from queue import Queue

#
from PIL import Image

# -------------------
CPU_COUNT = os.cpu_count()-1

# -------------------
def image_convert(img,mode):
    if img.mode!=mode:
        if mode=='P':
            if img.mode == 'RGBA':
                img = img.convert('RGB')
            return img.convert(mode, palette=Image.ADAPTIVE, colors=256)
        else:
            return img.convert(mode)
    return img


def progress_bar(self, maximum, q, fix_count=None, run=1):
    if fix_count and not fix_count.empty():
        maximum -= fix_count.get()
        if maximum <= 0:
            return
    period = 1/40
    block  = 0.05 # 100%/20%
    current = q.qsize()

    bar    = '\r %3d%% [%s%s]  %{}d/{}'.format(len(str(maximum)),maximum)
    ratio  = min(current/maximum, 1.0)
    num_up = int(ratio/block)
    up     = '█' * num_up
    down   = '□' * (20-num_up)
    r      = ratio * 100
    print (bar % (r,up,down,current), end='')

    if not run:
        return

    if not self.isrun:
        progress_bar(self, maximum, q, fix_count, run=0)
        return
    timer = threading.Timer(period, progress_bar, (self, maximum, q, fix_count))
    timer.start()
        
        
def read_file(file, seek, size):
    return [file.seek(seek)] and file.read(size)


def str_codec(str_, method='decode'):
    codecs = ['ISO-8859-1','utf-8']
    for codec in codecs:
        try: return eval('str_.{}(codec)'.format(method))
        except: pass
    return 'ErrorName'


    
#################################################
class mmp_convert(object):
    RES_FOLDER = 'Textures/'
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
        self.isrun = 0
        self.nTextures = 0
        self.bpp = None
        self.overwrite = False
        self.mmp_paths = []
        self.dir_paths = []


    #######################
    # mmp unpacking.
    #######################
    def process_unpacking(self, params):
        cpu  = CPU_COUNT
        if params[0] == 'main':
            cmd = params[1]
            print ('mmp unpacking...\n')
            self.isrun = 1
            # 多进程通信管理
            manager = Manager()
            q = manager.Queue()
            fix_count = manager.Queue()
            # 控制台模式下创建进度条
            if cmd:
                timer = threading.Timer(0.1, progress_bar, (self, self.nTextures, q, fix_count))
                timer.start()

            # 开启多进程任务分配
            pool = ProcessPoolExecutor(cpu)
            futures = []
            for task in self.mmp_paths:
                future = pool.submit(self.process_unpacking,('Process',q,task,fix_count))
                futures.append(future)
            pool.shutdown()
                
            self.isrun = 0
            qsize = q.qsize()
            time.sleep(0.2)

            length = len(self.mmp_paths)
            print ('\n\n%d mmp files unpacking done! Generate %d images.\n' % (length, qsize))
            for future in futures:
                results = future.result()
                if results:
                    for msg in results:
                        print (msg)
        elif params[0] == 'Process':
            q = params[1]
            file = params[2]
            fix_count = params[3]
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
                    'Thread',
                    q,
                    unpack_dir,
                    task,
                    mmp_file,
                    lock
                    )
                )
                futures.append(future)
            pool.shutdown()
            mmp_file.close()
            return error_msg
        elif params[0] == 'Thread':
            bpp = self.bpp
            q = params[1]
            unpack_dir = params[2]
            name,im_type,width,height,data_seek = params[3]
            mmp_file = params[4]
            
            lock = params[5]
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

        self.mmp_paths = []
        self.nTextures = 0
        for p in paths:
            if os.path.isdir(p):
                for root, dirs, files in os.walk(p):
                    files = [os.path.join(root,i) for i in files if os.path.splitext(i)[1].lower() == '.mmp']
                    self.mmp_paths.extend(files)
            elif os.path.splitext(p)[1].lower() == '.mmp':
                self.mmp_paths.append(p)

        for i in self.mmp_paths:
            with open(i,'rb') as f:
                self.nTextures += struct.unpack('<I', f.read(4))[0]
                
        if not self.nTextures:
            print ('No mmp file!')
            return

        sec = timeit(lambda:self.process_unpacking(('main',cmd)), number=1)
        print ('Time used: {:.2f} sec\n'.format(sec))
        

    #######################
    # bmp packing.
    #######################
    def process_packing(self, params):
        cpu  = CPU_COUNT
        if params[0] == 'main':
            cmd = params[1]
            print ('bmp packing...\n')
            self.isrun = 1
            # 多进程通信管理
            manager = Manager()
            q = manager.Queue()
            # 控制台模式下创建进度条
            if cmd:
                timer = threading.Timer(0.1, progress_bar, (self, self.nTextures, q))
                timer.start()

            # 开启多进程任务分配
            pool = ProcessPoolExecutor(cpu)
            futures = []
            for task in self.dir_paths:
                future = pool.submit(self.process_packing,('Process',q,task))
                futures.append(future)
            pool.shutdown()
                
            self.isrun = 0
            qsize = q.qsize()
            time.sleep(0.2)

            length = len(self.dir_paths)
            print ('\n\n%d images processed done! A total of %d mmp files:' % (qsize, length))
            for i in futures:
                result = i.result()
                if result: print (result)
            print ('\n', end='')
        elif params[0] == 'Process':
            q = params[1]
            root = params[2][0] # abs path
            files = params[2][1] # files name
            
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
                    future = pool.submit(self.process_packing, ('Thread', data_q, (root,file)))
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

        elif params[0] == 'Thread':
            bpp    = self.bpp
            data_q = params[1]
            root   = params[2][0]
            file_name = params[2][1]

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
                
                crc32= binascii.crc32(bmp_data()) # 校检和保留0似乎也没影响，这里我使用crc32

                name = str_codec(os.path.splitext(file_name)[0], 'encode')
                two,checksum,size,name_len = 2, crc32, len(im_data)+12, len(name)
                im_type,width,height       = self.gettype[mode], im_size[0], im_size[1]

                BytesIO.seek(0)
                BytesIO.write(struct.pack('<HIII', two,checksum,size,name_len))
                BytesIO.write(name)
                BytesIO.write(struct.pack('<III', im_type,width,height))
                BytesIO.write(im_data)
                BytesIO.truncate(BytesIO.tell())

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

        self.dir_paths = []
        self.nTextures = 0
        for p in paths:
            for root, dirs, files in os.walk(p):
                files = [i for i in files if os.path.splitext(i)[1].lower() in self.valid_format]
                if files:
                    self.dir_paths.append((root,files))
                    self.nTextures += len(files)

        if not self.nTextures:
            print ('No Image!')
            return

        sec = timeit(lambda:self.process_packing(('main',cmd)), number=1)
        print ('Time used: {:.2f} sec\n'.format(sec))

        
    #######################
    # convert to Xbpp.
    #######################
    def process_tobpp(self, params):
        cpu  = CPU_COUNT
        if params[0] == 'main':
            cmd = params[1]
            print ('mmp converting...\n')
            self.isrun = 1
            # 多进程通信管理
            manager = Manager()
            q = manager.Queue()
            # 控制台模式下创建进度条
            if cmd:
                timer = threading.Timer(0.1, progress_bar, (self, self.nTextures, q))
                timer.start()

            # 开启多进程任务分配
            pool = ProcessPoolExecutor(cpu)
            futures = []
            for task in self.mmp_paths:
                future = pool.submit(self.process_tobpp,('Process',q,task))
                futures.append(future)
            pool.shutdown()
                
            self.isrun = 0
            # qsize = q.qsize()
            time.sleep(0.2)

            length = len(self.mmp_paths)
            print ('\n\n%d mmp file convert to %sbpp done.\n' % (length,self.bpp))
        elif params[0] == 'Process':
            q = params[1]
            file = params[2]

            mmp_file= open(file,'rb')
            header4b = mmp_file.read(4)
            nTextures= struct.unpack('<I', header4b)[0]

            MMP_MAP = []
            for i in range(nTextures):
                two,checksum,size,name_len\
                     = struct.unpack('<HIII', mmp_file.read(14))
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

            new_mmp_name = '{}_to{}bpp.mmp'.format(os.path.splitext(file)[0], self.bpp)
            new_mmp_file = open(new_mmp_name,'wb')
            new_mmp_file.write(header4b)

            data_q = Queue()
            lock = Queue(maxsize=1)
            pool = ThreadPoolExecutor(4)
            futures = []
            for task in MMP_MAP:
                future = pool.submit(
                    self.process_tobpp,
                    (
                    'Thread',
                    task,
                    data_q,
                    mmp_file,
                    lock
                    )
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
                os.rename(new_mmp_name, file)
        elif params[0] == 'Thread':
            bpp = self.bpp
            two,checksum,size,name_len,name,\
                im_type,width,height,data_seek\
                = params[1]
            data_q = params[2]
            mmp_file = params[3]
            
            lock = params[4]
            lock.put(1)
            data = read_file(mmp_file, data_seek[0], data_seek[1])
            lock.get()
            
            BytesIO = io.BytesIO()
            mode    = self.getmode[im_type]
            mode2   = self.bpp2mode[bpp]
            if mode == mode2:
                BytesIO.write(struct.pack('<HIII', two,checksum,size,name_len))
                BytesIO.write(name)
                BytesIO.write(struct.pack('<III', im_type,width,height))
                BytesIO.write(data)
                data_q.put(BytesIO)
                return

            if im_type == self.Palette:
                img= Image.frombytes(mode,(width,height),data[:-768])
                palette= map(lambda i:min(i<<2 , 255),data[-768:])
                img.putpalette(palette)
            else:
                img= Image.frombytes(mode,(width,height),data)
            img = image_convert(img, mode2)
                
            #-----------------------
            # 检查调色板
            palette = b''
            if mode2=='P':
                # 调色板像素除以4适应BoD
                palette= map(lambda i: i>>2, img.getpalette())

            # 所有图片都得保存为BMP格式
            img.save(BytesIO, 'bmp')

            # 将图片数据及信息转换成字节
            bmp_data = BytesIO.getvalue
            im_data  = img.tobytes() + bytes(palette)
            
            crc32= binascii.crc32(bmp_data()) # 校检和保留0似乎也没影响，这里我使用crc32

            two,checksum,size,name_len = 2, crc32, len(im_data)+12, len(name)
            im_type = self.gettype[mode2]

            BytesIO.seek(0)
            BytesIO.write(struct.pack('<HIII', two,checksum,size,name_len))
            BytesIO.write(name)
            BytesIO.write(struct.pack('<III', im_type,width,height))
            BytesIO.write(im_data)
            BytesIO.truncate(BytesIO.tell())

            data_q.put(BytesIO)

    def tobpp(self, paths=[], bpp='8', overwrite=False, cmd=False):
        if cmd:
            paths = parse_args.path
            self.bpp = parse_args.bpp or bpp
            self.overwrite = parse_args.yes
        else:
            self.bpp = bpp
            self.overwrite = overwrite

        self.mmp_paths = []
        self.nTextures = 0
        for p in paths:
            if os.path.isdir(p):
                for root, dirs, files in os.walk(p):
                    files = [os.path.join(root,i) for i in files if os.path.splitext(i)[1].lower() == '.mmp']
                    self.mmp_paths.extend(files)
            elif os.path.splitext(p)[1].lower() == '.mmp':
                self.mmp_paths.append(p)

        error_msg = []
        mode = self.bpp2mode[self.bpp]
        for file in self.mmp_paths[:]:
            with open(file,'rb') as f:
                nTextures = struct.unpack('<I', f.read(4))[0]
                repeats = 0
                invalid_file = 0
                for i in range(nTextures):
                    two,checksum,size,name_len\
                        = struct.unpack('<HIII', f.read(14))
                    if two != 2:
                        invalid_file = 1
                        str_ = 'Error: "{}" Invalid file.'.format(os.path.split(file)[1])
                        error_msg.append(str_)
                        break
                    name = f.read(name_len)
                    im_type,width,height\
                        = struct.unpack('<III', f.read(12))
                    f.seek(size-12, 1)
                    repeats += (self.getmode[im_type] == mode)
                if (repeats == nTextures) or invalid_file:
                    self.mmp_paths.remove(file)
                    continue
                self.nTextures += nTextures
                
        if not self.nTextures:
            print ('No files need to be converted!')
            return

        sec = timeit(lambda:self.process_tobpp(('main',cmd)), number=1)
        if error_msg:
            for i in error_msg:
                print (i)
            print ('\n', end='')
        print ('Time used: {:.2f} sec\n'.format(sec))


    #######################
    # create dat files.
    #######################
    def todat(self, paths=[], cmd=False):
        if cmd:
            paths = parse_args.path
        mmp_paths = []
        for p in paths:
            if os.path.isdir(p):
                for root, dirs, files in os.walk(p):
                    files = [os.path.join(root,i) for i in files if os.path.splitext(i)[1].lower() == '.mmp']
                    mmp_paths.extend(files)
            elif os.path.splitext(p)[1].lower() == '.mmp':
                mmp_paths.append(p)

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



########################## INSTANCE WRAPPERS
# mmp_convert
mmp = mmp_convert()


# -------------------------------------------
classes_defined = dir()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--type','-t', type=str, default=None, metavar='type')
    parser.add_argument('--func','-f', type=str, default=None, metavar='method')
    parser.add_argument('--bpp', '-b', type=str, default=None, metavar='bpp', choices=['8','24','32','Alpha'])
    parser.add_argument('--path','-p', type=str, default=[],   metavar='file paths', nargs='*')
    parser.add_argument('--yes', '-y', action='store_true')
    parse_args = parser.parse_args()

    if parse_args.type in classes_defined:
        exec(parse_args.type + '().' + parse_args.func + '(cmd=True)')

"""
mmp.unpacking(paths[, bpp=None])
    :param paths: [mmp files or folders]
    :param bpp:   8/24/32/Alpha

mmp.packing(paths[, bpp=None, overwrite=False])
    :param paths: [only image folders]
    :param bpp:   8/24/32/Alpha
    :param overwrite:   True/False

mmp.tobpp(paths[, bpp='8', overwrite=False])
    :param paths: [mmp files or folders]
    :param bpp:   8/24/32/Alpha
    :param overwrite:   True/False

mmp.todat(paths)
    :param paths: [only mmp files]

# mmp.remove(path, names) No function!

skip = 4 - ((m_iImageWidth * m_iBitsPerPixel)>>3) & 3

skip = 4 - (biWidth*biBitCount)>>3 & 3
skip = (skip!=4 and skip) or 0
out =im.convert("P", palette=Image.ADAPTIVE,colors=256)
struct.unpack('<2sIIIIIIHHIIIIII', f3.seek(0)+1 and f3.read(54))
alpha=Image.frombytes('L',(256,32),d[3::4]).transpose(Image.FLIP_TOP_BOTTOM)

"""
