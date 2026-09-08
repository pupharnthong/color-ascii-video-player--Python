import cv2
import curses
import numpy as np
import time
import os
import sys
import subprocess
import tempfile
import pygame

video_path = r"C:\Users\pupha\Downloads\heart_download.mp4"

ASCII_CHARS = ":.=+-_ #*!"
N_CHARS = len(ASCII_CHARS)

CHAR_LUT = np.array(list(ASCII_CHARS))[
    np.clip((np.arange(256) * N_CHARS) // 256, 0, N_CHARS - 1)
]


def quantize(channel, levels=6):
    return (channel.astype(np.int32) * (levels - 1) // 255)


def to_256_color_id(r_idx, g_idx, b_idx):
    return 16 + (36 * r_idx) + (6 * g_idx) + b_idx


def init_colors():
    curses.start_color()
    curses.use_default_colors()
    if curses.COLORS < 256:
        return False
    for i in range(216):
        try:
            curses.init_pair(i + 1, 16 + i, -1)
        except curses.error:
            return False
    return True


def extract_audio(video_path):
    """Extract audio to a temp wav via ffmpeg. Returns path or None if unavailable."""
    tmp_wav = os.path.join(tempfile.gettempdir(), "ascii_player_audio.mp4")
    try:
        result = subprocess.run(
            [
                "ffmpeg", "-y", "-i", video_path,
                "-vn", "-acodec", "pcm_s16le", "-ar", "44100", "-ac", "2",
                tmp_wav,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        if result.returncode != 0 or not os.path.exists(tmp_wav):
            return None
        return tmp_wav
    except FileNotFoundError:
        return None  # ffmpeg not installed / not on PATH


def start_audio(wav_path):
    """Load and play audio via pygame.mixer. Returns True if playback started."""
    try:
        
        pygame.mixer.init()
        pygame.mixer.music.load(wav_path)
        pygame.mixer.music.play()
        return pygame, True
    except Exception:
        return None, False


def main(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(True)

    try:
        has_color = init_colors()
    except curses.error:
        has_color = False

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return

    video_fps = cap.get(cv2.CAP_PROP_FPS)
    frame_interval = (1.0 / video_fps) if video_fps > 0 else (1.0 / 30)

    # --- Try to set up audio and sync to it ---
    pygame_mod = None
    audio_ok = False
    wav_path = extract_audio(video_path)
    if wav_path:
        pygame_mod, audio_ok = start_audio(wav_path)

    start_time = time.perf_counter()
    frame_index = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        height, width = stdscr.getmaxyx()
        target_width = max(1, width)
        target_height = max(1, height - 1)

        resized = cv2.resize(frame, (target_width, target_height),
                              interpolation=cv2.INTER_AREA)
        gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
        ascii_frame = CHAR_LUT[gray]

        if has_color:
            rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
            r_idx = quantize(rgb[:, :, 0])
            g_idx = quantize(rgb[:, :, 1])
            b_idx = quantize(rgb[:, :, 2])
            pair_ids = to_256_color_id(r_idx, g_idx, b_idx) - 15

        for y in range(target_height):
            try:
                stdscr.move(y, 0)
            except curses.error:
                continue

            if not has_color:
                row = "".join(ascii_frame[y])
                try:
                    stdscr.addstr(row)
                except curses.error:
                    pass
                continue

            row_chars = ascii_frame[y]
            row_pairs = pair_ids[y]

            x = 0
            while x < target_width:
                pid = int(row_pairs[x])
                run_start = x
                x += 1
                while x < target_width and int(row_pairs[x]) == pid:
                    x += 1
                run_str = "".join(row_chars[run_start:x])
                try:
                    stdscr.addstr(run_str, curses.color_pair(pid))
                except curses.error:
                    pass

        stdscr.refresh()

        if stdscr.getch() == ord('q'):
            break

        frame_index += 1
        target_time = frame_index * frame_interval  # this frame's ideal timestamp

        # --- Sync source of truth: audio clock if available, else wall clock ---
        if audio_ok:
            elapsed = pygame_mod.mixer.music.get_pos() / 1000.0  # ms -> s
            if elapsed < 0:
                # get_pos() returns -1 if playback hasn't started/has stopped
                elapsed = time.perf_counter() - start_time
        else:
            elapsed = time.perf_counter() - start_time

        drift = target_time - elapsed
        if drift > 0:
            time.sleep(drift)
        elif drift < -frame_interval:
            # We're behind by more than a frame: drop frames to catch back up.
            frames_behind = int(-drift / frame_interval)
            for _ in range(frames_behind):
                ret2 = cap.grab()
                if not ret2:
                    break
                frame_index += 1

    cap.release()
    if audio_ok:
        pygame_mod.mixer.music.stop()


curses.wrapper(main)