FROM python:3.9-buster
RUN pip install requests
COPY porkbun-ddns.py /
ENTRYPOINT ["python3", "/porkbun-ddns.py"]
