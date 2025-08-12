FROM python:3-slim
WORKDIR /usr/src/app
COPY requirements.txt ./
RUN python -m pip install --no-cache-dir -r requirements.txt
COPY . /usr/src/app/orders
RUN [ -f /usr/src/app/orders/__init__.py ] || touch /usr/src/app/orders/__init__.py
CMD [ "python", "-m", "orders.app"]