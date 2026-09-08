import cv2
import curses
import numpy as np
import time
import os
import sys

video_path = "path/to/your/video.mp4"

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
        target_time = frame_index * frame_interval

        # Sync using wall clock
        elapsed = time.perf_counter() - start_time

        drift = target_time - elapsed
        if drift > 0:
            time.sleep(drift)
        elif drift < -frame_interval:
            # Drop frames if rendering falls behind schedule
            frames_behind = int(-drift / frame_interval)
            for _ in range(frames_behind):
                ret2 = cap.grab()
                if not ret2:
                    break
                frame_index += 1

    cap.release()


curses.wrapper(main)
