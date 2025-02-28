# Jellyfin File Uploader
An advanced, self-hosted file uploader to your jellyfin volume.
Upload media using your browser locally or from other devices on your network, or expose it and upload media from anywhere in the world*!

(*Make sure that the login is enabled and connected to your jellyfin if you want to expose it publically! Not recommended unless you know what you're doing).

## ⭐ Features
- Login with your existing Jellyfin credentials
- Upload videos and pictures straight to jellyfin volume
- Select which folder inside the jellyfin volume do you want to save (movies, photos, etc)
- Descriptive progress bars and multiple file uploads
- Customizable file extension limits, file size limits and overall upload limit
- Automated skipping over files that can't be uploaded
- Automated cleanup of stale (incomplete uploads) files
- Automated logging
- XSS and CSRF protection
- Directory traversal protection

## 🔧 How to Install

### Docker Compose (Recommended)
Requirements:
- [Docker](https://docs.docker.com/engine/install/) 
- [Docker Compose](https://docs.docker.com/compose/install/)

#### Instructions
- Run the following commands in a terminal (change the variables in docker-compose.yml as necessary):
    ```bash
        git clone https://github.com/stevenjwheeler/jellyfin-file-uploader.git
        cd jellyfin-file-uploader
        nano docker-compose.yml
        docker-compose up -d --build
    ```
- Jellyfin File Uploader is now running on http://localhost:5005

### Pre-built Docker Container
Requirements:
- [Docker](https://docs.docker.com/engine/install/)

#### Instructions
- Run the following command in a terminal (change variables as necessary):
    ```bash
        docker run -d \
          -p 5005:5005 \
          -v /downloads:/app/downloads \
          -e FLASK_SECRET_KEY=your_secret_key \
          -e ALLOWED_EXTENSIONS=mp4,m4v,mov,mkv,avi,wmv,flv,webm,mp3,aac,flac,wav,ogg,m4a,mka,mks,jpg,jpeg,png,gif,bmp,tiff,webp \
          -e LOGIN_ENABLED=true \
          -e JELLYFIN_SERVER_ADDRESS=http://localhost:8096 \
          -e MAX_FILE_SIZE=5 \
          -e MAX_CONTENT_LENGTH=20 \
          -e STALE_FILE_THRESHOLD=86400 \
          ghcr.io/stevenjwheeler/jellyfin-file-uploader:latest
    ```
- Jellyfin File Uploader is now running on http://localhost:5005

### Direct
Requirements:
- Python3

#### Instructions
- Run the following commands in a terminal:
    ```bash
        git clone https://github.com/stevenjwheeler/jellyfin-file-uploader.git
        cd jellyfin-file-uploader
        RUN pip3 install --no-cache-dir -r requirements.txt
        python3 app.py 
    ```
- Jellyfin File Uploader is now running on http://localhost:5005

## 🧑 Attribution
Based on the work of Osama Yusuf (https://github.com/Osama-Yusuf, https://github.com/Osama-Yusuf/jellyfin-uploader)
