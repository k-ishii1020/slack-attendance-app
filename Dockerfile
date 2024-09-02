FROM python:3.12.4
LABEL maintainer="@k-ishii1020"

WORKDIR /usr/src/app

COPY .  .

RUN pip install --no-cache-dir -r requirements.txt
CMD ["python", "main.py"]
