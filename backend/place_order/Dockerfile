FROM python:3-slim
WORKDIR /usr/src/app/place_order
COPY place_order/requirements.txt ./
RUN python -m pip install --no-cache-dir -r requirements.txt
COPY place_order/app.py shared/auth.py shared/rabbitmq.py ./
CMD [ "python", "./app.py"]