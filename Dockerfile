FROM registry.baidubce.com/paddlepaddle/paddle:2.3.2

WORKDIR /paddle

COPY . /paddle

RUN python3 -m pip install paddlepaddle -i https://mirror.baidu.com/pypi/simple \
    && pip install "paddleocr>=2.0.1" -i https://mirror.baidu.com/pypi/simple \
    && pip install "fastapi==0.78.0" -i https://mirror.baidu.com/pypi/simple \
    && pip install "imutils==0.5.4" -i https://mirror.baidu.com/pypi/simple \
    && pip install "uvicorn==0.17.6" -i https://mirror.baidu.com/pypi/simple

CMD ["python", "main.py"]

#docker build -t myardz/paddle_ocr:cpu_plate_crop .
#docker push myardz/paddle_ocr:cpu_plate_crop
#docker run --name paddle_cpu_plate --restart always -td -p 9020:8008 -v /root/zym/custom_paddle_cpu_ocr:/paddle myardz/paddle_ocr:cpu_plate_crop
