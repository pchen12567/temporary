FROM python:3.7.6
COPY . /app
COPY ./nltk_data/ /root/nltk_data/
WORKDIR /app
RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
ENTRYPOINT ["python"]
CMD ["app.py"]