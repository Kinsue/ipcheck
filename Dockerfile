FROM python:alpine3.19
RUN pip install requests -i https://mirrors.ustc.edu.cn/pypi/simple

COPY ipcheck.py /run.py

ENTRYPOINT ["python3", "-u", "/run.py"]
