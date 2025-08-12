FROM python:3-slim
WORKDIR /usr/src/app/display_orders
COPY display_orders/requirements.txt ./
RUN python -m pip install --no-cache-dir -r requirements.txt
COPY display_orders/ ./display_orders/
COPY shared/ ./shared/
ENV PYTHONPATH=/usr/src/app
CMD ["python", "-m", "display_orders.app"]