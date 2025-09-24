# Use the official Python base image
FROM python:3.9.13
ENV PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /app

# Install Python data_grabber dependencies
COPY data_grabber/requirements.txt .
RUN pip install -r requirements.txt

# Install Python website dependencies
COPY website/requirements.txt .
RUN pip install -r requirements.txt

# Copy the application files
COPY data_grabber /app/data_grabber
COPY website /app/website
COPY scheduler.py /app

# Set build arguments as environment variables
# ARG rdmo_token
# ENV RDMO_TOKEN=$RDMO_TOKEN
ENV RDMO_TOKEN="this_is_the_rdmo_token"

# Set the entrypoint command to run the main.py script with provided credentials
# CMD ["python", "data_grabber/main.py", "--username", "$USERNAME", "--password", "$PASSWORD", "--websusr", "$WEBSUSR", "--webspwrd", "$WEBSPWRD"]
# CMD ["python", "scheduler.py", "--username", "$USERNAME", "--password", "$PASSWORD"]
# CMD ["python", "scheduler.py", "--rdmo_token", "$RDMO_TOKEN"]
CMD ["python", "scheduler.py"]
