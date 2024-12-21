# 复现笔记
## 运行
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

## 素材
- 【大疆运载无人机“除冰”，凌空一击，酷！-哔哩哔哩】 https://b23.tv/OmDTmAX
- 【喜鹊战无人机-哔哩哔哩】 https://b23.tv/rJiGH7B
- 【大疆mini无人机装灯泡，犹如空间站的对接的操作-哔哩哔哩】 https://b23.tv/UEmFWZX
- 【周末的校园里两架穿越机追逐  也算是实现了曾经的一个小愿望了-哔哩哔哩】 https://b23.tv/SJounAP
- 【双机位  FPV追逐飞行-哔哩哔哩】 https://b23.tv/03avhJX
- 【Flylens75追逐speedybee25-哔哩哔哩】 https://b23.tv/3NOeJlY
- 【无人机追逐全速 FPV 无人机 ☠️🚀🚀☣️☢️-哔哩哔哩】 https://b23.tv/5EfEpEF
- 【无人机废旧工厂上演追逐大戏-哔哩哔哩】 https://b23.tv/HkkhqDo
- 【【穿越机灵感与启发 No.58】3寸涵道穿越机的追逐乐趣 GoPro拍摄-哔哩哔哩】 https://b23.tv/zgy8ppr
- 【追逐五寸-哔哩哔哩】 https://b23.tv/ICGgi1A
- 【超低空飞行和追逐穿越机-哔哩哔哩】 https://b23.tv/7a6YrTk