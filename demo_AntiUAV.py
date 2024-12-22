from __future__ import division

import os
import cv2
import sys
import time
import torch
import struct
import socket
import logging
import datetime
import argparse

import numpy as np
from PIL import Image

import pdb

# 添加自定义模块的路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'detect_wrapper'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'tracking_wrapper/dronetracker'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'tracking_wrapper/drtracker'))

from Detectoruav import DroneDetection
from trackinguav.evaluation.tracker import Tracker

import warnings
warnings.filterwarnings("ignore")

g_init = False
g_detector = None  # 检测器
g_tracker = None   # 跟踪器
g_logger = None
detect_box = None
track_box = None
g_data = None
detect_first = True
g_enable_log = True
repeat_detect = True

count = 0
g_frame_counter = 0
TRACK_MAX_COUNT = 150

Visualization = 1
sendLocation = 0

# 全局socket
udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# 目标主机的IP和端口, 用来发送坐标
IP = '192.168.0.171'
Port = '9921'

def safe_log(msg):
    if g_logger:
        g_logger.info(msg)

def send_bbs(bbs):
    global g_logger
    if g_logger:
        g_logger.info('send a box : {}'.format(bbs))

def mono_to_rgb(data):
    w, h = data.shape
    img = np.zeros((w, h, 3), dtype=np.uint8)
    img[:, :, 0] = data
    img[:, :, 1] = data
    img[:, :, 2] = data
    return img

def rgb_to_ir(data):
    w, h, c = data.shape
    img = np.zeros((w, h), dtype=np.uint8)
    img = data[:, :, 0]
    return img

def distance_check(bbx1, bbx2, thd):
    cx1 = bbx1[0] + bbx1[2] / 2
    cy1 = bbx1[1] + bbx1[3] / 2
    cx2 = bbx2[0] + bbx2[2] / 2
    cy2 = bbx2[1] + bbx2[3] / 2
    dist = np.sqrt((cx1 - cx2)**2 + (cy1 - cy2)**2)
    return dist < thd

def scale_coords(img1_shape, coords, img0_shape):
    # Rescale coords (xyxy) from img1_shape to img0_shape
    gainx = img1_shape[0] / img0_shape[0]
    gainy = img1_shape[1] / img0_shape[1]

    coords[0] = coords[0] / gainx
    coords[1] = coords[1] / gainy
    coords[2] = coords[2] / gainx
    coords[3] = coords[3] / gainy
    coords = [int(x) for x in coords]
    return coords

def send_coord(coord):
    address = (IP, int(Port))
    # 定义C结构体：目标追踪信息
    msgCode = 1
    nAimType = 1
    nTrackType = 1
    nState = 1
    if coord is not None:
        print(coord)
        nAimX = coord[0]
        nAimY = coord[1]
        nAimW = coord[2]
        nAimH = coord[3]
        data = struct.pack("iiiiiiii", msgCode, nAimType, nAimX, nAimY, nAimW, nAimH, nTrackType, nState)
        # pdb.set_trace()
        udp_socket.sendto(data, address)
        safe_log("send successfully")
    else:
        print('coord is none!!!')

def global_init():
    """ global variables initialize.
    """
    global g_init, g_detector, g_tracker, g_logger, g_enable_log
    if not g_init:
        if g_enable_log:
            g_logger = logging.getLogger()
            g_logger.setLevel(logging.INFO)
            fh = logging.FileHandler('log.txt', mode='a')
            g_logger.addHandler(fh)
        IRweights_path = os.path.join(os.path.dirname(__file__), 'detect_wrapper/weights/best.pt')
        g_detector = DroneDetection(IRweights_path=IRweights_path, RGBweights_path=IRweights_path)
        g_tracker = Tracker()
        # g_tracker.warmup()
        g_init = True
    safe_log("global init done")

def result_visualization(img, bbox):
    magnification = 2
    oframe = img.copy()
    visuframe = cv2.resize(oframe, (oframe.shape[1]*magnification, oframe.shape[0]*magnification), cv2.INTER_LINEAR)
    bbx = [i * magnification for i in bbox]
    cv2.rectangle(visuframe, (bbx[0], bbx[1]), (bbx[0] + bbx[2], bbx[1] + bbx[3]), (0, 255, 0), 2)
    cv2.imshow("tracking", visuframe)
    cv2.waitKey(1)

def imgproc(data, out_video_writer=None, save_frame=True):
    global g_init, g_detector, g_tracker, g_frame_counter, count
    global detect_box, track_box, repeat_detect, detect_first, IMG_TYPE
    count += 1
    safe_log('recv a frame')
    bbx = None

    frame = np.array(data)
    print('frame.shape=', frame.shape)
    # cv2.imshow("visual", frame)
    # cv2.waitKey(1)
    # pdb.set_trace()
    IMG_TYPE = 0
    # frame = rgb_to_ir(frame)
    if len(frame.shape) == 2:
        IMG_TYPE = 1
        frame = mono_to_rgb(frame)
    # test
    IMG_TYPE = 1

    processed_frame = frame.copy()  # 复制一份用于保存

    if g_detector and g_tracker:
        # g_frame_counter = 0
        if g_frame_counter <= 0:
            if IMG_TYPE == 0:
                safe_log('{}'.format(IMG_TYPE))
                init_box = g_detector.forward_RGB(frame)
                center_box = [320, 192, 0, 0]
            else:
                safe_log('{}'.format(IMG_TYPE))
                init_box = g_detector.forward_IR(frame)
                center_box = [320, 256, 0, 0]

            #print("2")
            print(count)
            if detect_first:
                ## NO UAV Test 
                # if init_box is None:
                #     print('init_box is none, initialize!!!')
                #     init_box = [327, 247, 16, 15]                
                if init_box is not None:
                    if distance_check(init_box, center_box, 60) and count % 4 == 1:
                        g_tracker.init_track(init_box, frame)
                        g_frame_counter = TRACK_MAX_COUNT
                        safe_log('init done')
                        detect_first = False

                    init_box = [int(x) for x in init_box]
                    if IMG_TYPE == 1 and count % 8 == 1:
                        if sendLocation:
                            send_coord(init_box)
                        count = 1
                    elif IMG_TYPE == 0 and count % 8 == 1:
                        init_box = scale_coords([640, 384], init_box, [1920, 1080])
                        if sendLocation:
                            send_coord(init_box)
                        count = 1
                    print("detection")
                    if Visualization:
                        result_visualization(frame, init_box)
                        # 在保存的视频中绘制矩形框
                        bbx_to_draw = init_box
                        cv2.rectangle(processed_frame, (bbx_to_draw[0], bbx_to_draw[1]),
                                      (bbx_to_draw[0] + bbx_to_draw[2], bbx_to_draw[1] + bbx_to_draw[3]),
                                      (0, 255, 0), 2)
                elif count <= 1 or count >= 9:
                    print('init_box is none')
                    count = 0

            else:
                if init_box is not None and distance_check(init_box, center_box, 60):
                    g_tracker.change_state(init_box)
                    g_frame_counter = TRACK_MAX_COUNT

                    init_box = [int(x) for x in init_box]
                    if IMG_TYPE == 1 and count % 2 == 1:
                        if sendLocation:
                            send_coord(init_box)
                    elif IMG_TYPE == 0 and count % 2 == 1:
                        init_box = scale_coords([640, 384], init_box, [1920, 1080])
                        if sendLocation:
                            send_coord(init_box)
                    print("detection")
                    if Visualization:
                        result_visualization(frame, init_box)
                        # 在保存的视频中绘制矩形框
                        bbx_to_draw = init_box
                        cv2.rectangle(processed_frame, (bbx_to_draw[0], bbx_to_draw[1]),
                                      (bbx_to_draw[0] + bbx_to_draw[2], bbx_to_draw[1] + bbx_to_draw[3]),
                                      (0, 255, 0), 2)
                else:
                    print("keep")
                    g_frame_counter = TRACK_MAX_COUNT
                    bbx = g_tracker.on_track(frame)
                    g_frame_counter -= 1
                    send_bbs('get!--{}'.format(bbx))
                    if IMG_TYPE == 1 and count % 2 == 1:
                        if sendLocation:
                            send_coord(bbx)
                    elif IMG_TYPE == 0 and count % 2 == 1:
                        bbx = scale_coords([640, 384], bbx, [1920, 1080])
                        if sendLocation:
                            send_coord(bbx)
                    if Visualization:
                        result_visualization(frame, bbx)
                        # 在保存的视频中绘制矩形框
                        bbx_to_draw = bbx
                        cv2.rectangle(processed_frame, (bbx_to_draw[0], bbx_to_draw[1]),
                                      (bbx_to_draw[0] + bbx_to_draw[2], bbx_to_draw[1] + bbx_to_draw[3]),
                                      (0, 255, 0), 2)

        else:
            bbx = g_tracker.on_track(frame)
            g_frame_counter -= 1
            send_bbs('get!--{}'.format(bbx))
            if IMG_TYPE == 1 and count % 2 == 1:
                if sendLocation:
                    send_coord(bbx)
            elif IMG_TYPE == 0 and count % 2 == 1:
                bbx = scale_coords([640, 384], bbx, [1920, 1080])
                if sendLocation:
                    send_coord(bbx)
            if Visualization:
                result_visualization(frame, bbx)
                # 在保存的视频中绘制矩形框
                bbx_to_draw = bbx
                cv2.rectangle(processed_frame, (bbx_to_draw[0], bbx_to_draw[1]),
                              (bbx_to_draw[0] + bbx_to_draw[2], bbx_to_draw[1] + bbx_to_draw[3]),
                              (0, 255, 0), 2)

    # 保存处理后的帧
                if save_frame and out_video_writer is not None:
                    out_video_writer.write(processed_frame)

def getUDPSocket(IpAddr, Port):
    server = socket.socket(type=socket.SOCK_DGRAM)
    server.bind((IpAddr, Port))
    safe_log("Server Socket is READY!")
    return server

def udpRecv(server, frameSize):
    global g_data
    img_recv_final = None
    # pdb.set_trace()
    g_data, addr = server.recvfrom(256)  # should be b'I BEGIN'

    # safe_log(str(data)+" from "+str(addr))
    if g_data == b'I BEGIN':
        print("I BEGIN!!")
        server.sendto(b'sucess', addr)
        data, addr = server.recvfrom(16)  # should be the img size that should be sent
        server.sendto(b'sucess', addr)
        img_size = int.from_bytes(data, byteorder='little')  # img size, (bytes)
        # safe_log(img_size)

        img_recv_all = b''
        recvd_size = 0
        # i = 1
        while recvd_size < img_size:
            data, addr = server.recvfrom(frameSize)  # 阻塞等待数据(value,(ip,port))
            server.sendto(b'sucess', addr)

            img_recv_all += data
            recvd_size += len(data)
        # i += 1
        # server.sendto(b'sucess', addr)
        img_recv_final = np.frombuffer(img_recv_all, np.uint8)
        if img_size < 500000:
            img_recv_final = img_recv_final.reshape((512, 640))
        else:
            img_recv_final = img_recv_final.reshape((384, 640, 3))
    return img_recv_final

if __name__ == "__main__":
    global_init()
    addr = '127.0.0.1'  # 本地地址
    port = 9999         # 监听端口
    frameSize = 8192
    detect_num = 5
    server = getUDPSocket(addr, port)  # bind server's address
    print("Start!!")

    # 创建保存结果的视频的文件夹
    result_dir = os.path.join(os.path.dirname(__file__), 'results_antiuav')
    if not os.path.exists(result_dir):
        os.makedirs(result_dir)

    # 获取输入视频路径
    video_path = os.path.join(os.path.dirname(__file__), 'videos/n9.mp4')
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        print("无法打开视频文件")
        sys.exit()

    # 获取视频的基本信息
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # 使用mp4编码

    # 构造输出视频的路径
    video_filename = os.path.basename(video_path)
    video_name, video_ext = os.path.splitext(video_filename)
    output_video_name = f"{video_name}_result{video_ext}"
    output_video_path = os.path.join(result_dir, output_video_name)

    # 初始化视频写入器
    out_video_writer = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))
    if not out_video_writer.isOpened():
        print("无法初始化视频写入器")
        sys.exit()

    print(f"结果视频将保存为: {output_video_path}")

    while True:
        # data = udpRecv(server, frameSize)
        ret, data = cap.read()

        if not ret:
            print("视频读取完毕或无法读取帧")
            break

        if g_data == b'STOP':
            g_frame_counter = 0
            count = 0
            detect_first = True
            repeat_detect = True
            # g_tracker.warmup()
            print("Start!!")

        if data is not None:
            imgproc(data, out_video_writer=out_video_writer, save_frame=True)

    # 释放资源
    cap.release()
    if out_video_writer is not None:
        out_video_writer.release()
    cv2.destroyAllWindows()
