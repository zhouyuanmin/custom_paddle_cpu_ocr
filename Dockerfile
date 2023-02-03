FROM registry.baidubce.com/paddlepaddle/paddle:2.3.2

WORKDIR /paddle

COPY . /paddle

RUN python3 -m pip install paddlepaddle -i https://mirror.baidu.com/pypi/simple \
    && pip install "paddleocr>=2.0.1" -i https://mirror.baidu.com/pypi/simple \
    && pip install "fastapi==0.78.0" -i https://mirror.baidu.com/pypi/simple \
    && pip install "uvicorn==0.17.6" -i https://mirror.baidu.com/pypi/simple

CMD ["python", "main.py"]