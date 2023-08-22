FROM python:3.10
EXPOSE 5000
WORKDIR "C:\Users\userpc\Desktop\pyCharm\rest_API:/app"
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python3", "-m" , "flask", "run", "--host=0.0.0.0"]