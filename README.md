# 复现笔记
拉取镜像
```sh
docker build -t antiuav_image:test --network=host --progress=plain .

docker run --name antiuav-test -itd --privileged --gpus all --network=host \
    -v /tmp/.X11-unix:/tmp/.X11-unix:ro \
    -e DISPLAY=$DISPLAY \
    -e LOCAL_USER_ID="$(id -u)" \
    antiuav_image:test /bin/bash

docker exec -it antiuav-test /bin/bash
```
下载代码
```sh
cd /workspace
git clone https://github.com/superboySB/Global-Local-MAV-Detection
```
模型量化（需要在docker内根据物理机定制）
```sh
cp /workspace/Global-Local-MAV-Detection/weights/*.pt /workspace/tensorrtx/yolov5/gen_wts.py /workspace/yolov5/
cd /workspace/yolov5/
python gen_wts.py -w yolov5s_GLAD.pt -o yolov5s_GLAD.wts
python gen_wts.py -w yolov5s_GLAD-crop.pt -o yolov5s_GLAD-crop.wts
vim /workspace/tensorrtx/yolov5/yololayer.h # (And change CLASS_NUM = 1)
mkdir /workspace/tensorrtx/yolov5/build
cd /workspace/tensorrtx/yolov5/build
cmake ..
make -j8
cp /workspace/yolov5/*.wts /workspace/tensorrtx/yolov5/build/
./yolov5 -s yolov5s_GLAD.wts yolov5s_GLAD.engine s
./yolov5 -s yolov5s_GLAD-crop.wts yolov5s_GLAD-crop.engine s
cp *.engine libmyplugins.so /workspace/Global-Local-MAV-Detection/weights/
```
运行demo
```sh
cd /workspace/Global-Local-MAV-Detection
python GLAD.py
```