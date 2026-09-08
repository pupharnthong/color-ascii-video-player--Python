# color-ascii-video-player--Python
 #  Terminal ASCII Video Player (with Audio & Color)

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![OpenCV](https://img.shields.io/badge/OpenCV-Supported-green)
![FFmpeg](https://img.shields.io/badge/FFmpeg-Required-red)
![License](https://img.shields.io/badge/License-MIT-brightgreen)

---

##  Features

*  **256-Color Support**: Quantizes RGB video colors to ANSI 256-color terminal space.
*  **Dynamic Frame Dropping**: Automatically drops frames if rendering falls behind to maintain real-time audio sync.

---

##  Prerequisites

Before running this project, ensure you have the following installed on your system:

### 1. Python 3.9 or higher
Check your Python version with:
```bash
python --version
```
### 2. FFmpeg 
#Windows
```Powershell
winget install ffmpeg
```
#MacOS
```bash
brew install ffmpeg
```
#Linux
```Bash
sudo apt update && sudo apt install ffmpeg
```
## Install required Python packages
```Bash
pip install opencv-python numpy
```
```Bash
pip install windows-curses
```

## Usage
#Configure Video Path
>video_path = "path/to/your/video.mp4"

#Run the Player
```Bash
python ascll_code.py
```
#Controls
Press q to quit playback at any time







