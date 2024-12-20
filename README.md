# 复现笔记
```sh
docker build -t antiuav_image:test --network=host --progress=plain .

docker run --name antiuav-test -itd --privileged --gpus all --network=host \
    -v /tmp/.X11-unix:/tmp/.X11-unix:ro \
    -e DISPLAY=$DISPLAY \
    -e LOCAL_USER_ID="$(id -u)" \
    antiuav_image:test /bin/bash

docker exec -it antiuav-test /bin/bash

cd /workspace
git clone https://github.com/superboySB/Global-Local-MAV-Detection
cd Global-Local-MAV-Detection
```
运行
```sh
python GLAD.py
```