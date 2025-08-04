FROM python:3-slim
WORKDIR /usr/src/app/display_orders
COPY display_orders/requirements.txt ./
RUN python -m pip install --no-cache-dir -r requirements.txt
COPY display_orders/app.py shared/auth.py ./
CMD [ "python", "./app.py"]