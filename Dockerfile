FROM python:3.9.5-slim

COPY . /myapp

WORKDIR /myapp

COPY requirements.txt requirements.txt

RUN pip3 install -r requirements.txt

WORKDIR /myapp/src

ENV PATH=/myapp:$PATH
ENV PATH=/myapp/src:$PATH

ENV PYTHONPATH "${PYTHONPATH}:/myapp:/myapp/src"

CMD ["python3", "main.py"]