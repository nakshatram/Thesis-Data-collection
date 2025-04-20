import pygame
import os
import time
import csv

pygame.init()
pygame.display.set_mode((1, 1))  # Enable event handling for key presses.
pygame.mixer.init()

def play_n_back_sequence(seq, folder, pid, trial, n_back, lighting, seq_order, letter_delay=1500):
    responses = []
    trial_start_time = time.time()
    for char in seq:
        sound_file = f"sounds/{char.upper()}.wav"
        if os.path.exists(sound_file):
            sound = pygame.mixer.Sound(sound_file)
            sound.play()
        else:
            print(f"Sound file {sound_file} not found.")
        key_pressed = None
        key_press_time = None
        key_release_time = None
        t0 = time.time()
        # Listen for space bar events during the letter delay.
        while time.time() - t0 < letter_delay / 1000.0:
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    if key_pressed is None:
                        key_pressed = "space"
                        key_press_time = time.time() - trial_start_time
                if event.type == pygame.KEYUP and event.key == pygame.K_SPACE:
                    if key_pressed is not None and key_release_time is None:
                        key_release_time = time.time() - trial_start_time
            pygame.time.wait(10)
        response_time = key_press_time if key_pressed is not None else ""
        key_duration = (key_release_time - key_press_time) if key_pressed is not None and key_release_time is not None else ""
        responses.append([
            pid,
            f"Run{trial}",
            time.time() - trial_start_time,
            char,
            n_back,
            lighting,
            seq_order,
            key_pressed if key_pressed is not None else "",
            response_time,
            key_duration
        ])
    csv_file = os.path.join(folder, "main.csv")
    with open(csv_file, 'a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerows(responses)
