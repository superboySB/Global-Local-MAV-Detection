FROM nvcr.io/nvidia/tensorrt:21.03-py3

# Please contact with me if you have problems
LABEL maintainer="Zipeng Dai <daizipeng@bit.edu.cn>"
ENV DEBIAN_FRONTEND=noninteractive

# TODO：网络不好的话可以走代理
ENV http_proxy=http://127.0.0.1:8889
ENV https_proxy=http://127.0.0.1:8889

RUN apt-get update && \
    apt-get install -y --no-install-recommends locales git tmux gedit vim unzip python3-pip
RUN locale-gen en_US en_US.UTF-8 && update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
ENV LANG=en_US.UTF-8

RUN apt-get install -y --no-install-recommends \
    libxkbcommon-x11-0 libqt5gui5 libqt5core5a libqt5widgets5 libxcb-xinerama0 libopencv-dev ffmpeg
RUN /usr/bin/python -m pip install --upgrade pip
RUN pip install torch==1.8.1+cu111 torchvision==0.9.1+cu111 torchaudio==0.8.1 -f https://download.pytorch.org/whl/torch_stable.html
RUN pip install numpy numba pandas scipy requests pyyaml tqdm matplotlib seaborn opencv-python==4.4.0.46

WORKDIR /workspace
RUN git clone -b v6.0 https://github.com/ultralytics/yolov5.git && \
    git clone -b yolov5-v6.0 https://github.com/wang-xinyu/tensorrtx.git

# TODO：如果走了代理、但是想镜像本地化到其它机器，记得清空代理（或者容器内unset）
# ENV http_proxy=
# ENV https_proxy=
# ENV no_proxy=
CMD ["/bin/bash"]
WORKDIR /workspace