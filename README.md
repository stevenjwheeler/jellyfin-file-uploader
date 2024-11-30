# OasisLab File Uploader
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

### Docker (Recommended)
Requirements:
- [Docker](https://docs.docker.com/engine/install/) 
- [Docker Compose](https://docs.docker.com/compose/install/)

#### Instructions
- To run the jellyfin uploader on top of docker just clone the repo and deploy it with docker-compose as follows:
    ```bash
        git clone <ADD URL>
        cd <ADD DIRECTORY>
        docker-compose up -d --build
    ```
OasisLab File Uploader is now running on http://localhost:5005

### Direct
Requirements:
- Python

#### Instructions
-To run using your host python:
    ```bash
        git clone <ADD URL>
        cd <ADD DIRECTORY>
        RUN pip3 install --no-cache-dir -r requirements.txt
        python3 app.py 
    ```
OasisLab File Uploader is now running on http://localhost:5005

## 🧑 Attribution
Based on the work of Osama Yusuf (https://github.com/Osama-Yusuf, https://github.com/Osama-Yusuf/jellyfin-uploader)