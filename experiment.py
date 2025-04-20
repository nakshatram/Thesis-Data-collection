# experiment.py

import os
import time
import csv
import pygame
import random
from datetime import datetime

from generate_letter_seq import generate_letter_seq
from eye_tracking      import calibrate_eye_tracker, start_eye_recording, stop_eye_recording

# ─────────────────────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────────────────────
TRIALS          = 5
NUM_TARGETS     = 10     # ← for testing, 10 sounds/block
LETTER_DELAY_MS = 2500   # 1.5 s per tone

LIGHT_DESC = {
    '1': "Complete Darkness (0–5 lux)",
    '2': "Rather Dark (10–50 lux)",
    '3': "Low Light (≈200 lux)",
    '4': "Rather Bright (300–500 lux)",
    '5': "Bright Light (>1000 lux)"
}

# ─────────────────────────────────────────────────────────────────────────────
# PYGAME SETUP
# ─────────────────────────────────────────────────────────────────────────────
pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.init()
pygame.mixer.init()
pygame.font.init()

info   = pygame.display.Info()
SCREEN = pygame.display.set_mode((info.current_w, info.current_h), pygame.FULLSCREEN)
pygame.display.set_caption("Auditory N‑Back Task")
pygame.mouse.set_visible(False)

BLACK, WHITE = (0, 0, 0), (255, 255, 255)
FONT         = pygame.font.SysFont(None, 48)
CROSS_L      = 40

# Base paths
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
SOUND_DIR  = os.path.join(BASE_DIR, "sounds")
print(f"[DEBUG] Base dir: {BASE_DIR}")
print(f"[DEBUG] Expecting sounds in: {SOUND_DIR}")

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def draw_cross():
    cx, cy = info.current_w//2, info.current_h//2
    pygame.draw.line(SCREEN, WHITE, (cx-CROSS_L, cy), (cx+CROSS_L, cy), 5)
    pygame.draw.line(SCREEN, WHITE, (cx, cy-CROSS_L), (cx, cy+CROSS_L), 5)

def wait_key(allowed=None):
    while True:
        for ev in pygame.event.get():
            if ev.type == pygame.KEYDOWN and (allowed is None or ev.key in allowed):
                return ev.key
            elif ev.type == pygame.QUIT:
                pygame.quit(); exit()
        pygame.time.wait(10)

def text_input(prompt):
    txt = ""
    while True:
        SCREEN.fill(BLACK)
        p = FONT.render(prompt, True, WHITE)
        SCREEN.blit(p, p.get_rect(center=(info.current_w//2, info.current_h//3)))
        e = FONT.render(txt+"|", True, WHITE)
        SCREEN.blit(e, e.get_rect(center=(info.current_w//2, info.current_h//2)))
        pygame.display.flip()
        for ev in pygame.event.get():
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_RETURN:
                    return txt.strip()
                elif ev.key == pygame.K_BACKSPACE:
                    txt = txt[:-1]
                else:
                    c = ev.unicode
                    if c.isprintable():
                        txt += c
            elif ev.type == pygame.QUIT:
                pygame.quit(); exit()
        pygame.time.wait(10)

def create_experiment_folder(pid):
    base = os.path.join(BASE_DIR, "participants_data")
    os.makedirs(base, exist_ok=True)
    ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
    root = os.path.join(base, f"{pid}_{ts}")
    print(f"[DEBUG] Creating data folder: {root}")
    for t in range(1, TRIALS+1):
        td = os.path.join(root, f"trial_{t}")
        os.makedirs(td, exist_ok=True)
        with open(os.path.join(td, "main.csv"), 'w', newline='', encoding='utf-8') as f:
            f.write(
                "Participant ID,Run ID,Timestamp,Stimulus,N-back Level,"
                "Lighting Condition,N-back Sequence,Key Press,Response Time,Key Duration\n"
            )
        with open(os.path.join(td, "eye_data.csv"), 'w', newline='', encoding='utf-8') as f:
            f.write(
                "Participant ID,Run ID,Timestamp,Left Pupil Dilation,"
                "Right Pupil Dilation,Blink\n"
            )
    return root

# ─────────────────────────────────────────────────────────────────────────────
# EXPERIMENT
# ─────────────────────────────────────────────────────────────────────────────
class AuditoryNBack:
    def __init__(self):
        # 1) ID & N‑back levels
        self.pid   = text_input("Enter Participant ID:")
        seq_str    = text_input("Enter N‑back seq (e.g. 1-2-3):")
        try:
            self.n_seq = [int(x) for x in seq_str.split('-')]
            assert len(self.n_seq) == 3
        except:
            pygame.quit()
            raise RuntimeError("Invalid N‑back format.")
        # 2) Folder & eye calibration
        self.root_folder = create_experiment_folder(self.pid)
        calibrate_eye_tracker()
        # 3) Lighting order
        self.light_order = random.sample(['1','2','3','4'], 4) + ['5']

    def run(self):
        for trial in range(1, TRIALS+1):
            self.run_trial(trial)
        SCREEN.fill(BLACK)
        bye = FONT.render("Done – Thank You!", True, WHITE)
        SCREEN.blit(bye, bye.get_rect(center=(info.current_w//2, info.current_h//2)))
        pygame.display.flip()
        time.sleep(2)
        pygame.quit()

    def run_trial(self, trial):
        # A) Lighting instruction
        Lkey = self.light_order[trial-1]
        desc = LIGHT_DESC[Lkey]
        SCREEN.fill(BLACK)
        a = FONT.render(f"Trial {trial}", True, WHITE)
        b = FONT.render(f"Set Lighting → {desc}", True, WHITE)
        c = FONT.render("Press SPACE when ready", True, WHITE)
        SCREEN.blit(a, a.get_rect(center=(info.current_w//2, info.current_h//3)))
        SCREEN.blit(b, b.get_rect(center=(info.current_w//2, info.current_h//2)))
        SCREEN.blit(c, c.get_rect(center=(info.current_w//2, info.current_h*2//3)))
        pygame.display.flip()
        wait_key([pygame.K_SPACE])

        # B) 1 s fixation cross
        SCREEN.fill(BLACK); draw_cross(); pygame.display.flip()
        pygame.time.wait(1000)

        # C) Start eye tracking
        trial_folder = os.path.join(self.root_folder, f"trial_{trial}")
        start_eye_recording(self.pid, f"Run{trial}", trial_folder)

        # D) Auditory blocks
        all_resps = []
        t0 = time.time()

        for blk_i, n in enumerate(self.n_seq):
            seq, _ = generate_letter_seq(n, NUM_TARGETS)
            for letter in seq:
                # show cross + label
                SCREEN.fill(BLACK); draw_cross()
                lbl = FONT.render(f"{n}-back", True, WHITE)
                SCREEN.blit(lbl, lbl.get_rect(topright=(info.current_w-50,50)))
                pygame.display.flip()

                # load & play via music
                wav1 = os.path.join(SOUND_DIR, f"{letter.upper()}.wav")
                wav2 = os.path.join(SOUND_DIR, f"{letter.lower()}.wav")
                path = wav1 if os.path.exists(wav1) else (wav2 if os.path.exists(wav2) else None)
                if path:
                    try:
                        pygame.mixer.music.load(path)
                        pygame.mixer.music.play()
                        print(f"[DEBUG] music.play() → {path}")
                    except Exception as e:
                        print(f"[ERROR] mixer.music failed: {e}")
                else:
                    print(f"[WARN] Missing sound for '{letter}'")

                # capture RT & hold
                onset  = time.time()
                pressed= False
                rt     = None
                dur    = None
                kd_ts  = None

                while time.time() - onset < LETTER_DELAY_MS/1500:
                    for ev in pygame.event.get():
                        if ev.type==pygame.KEYDOWN and ev.key==pygame.K_SPACE and not pressed:
                            pressed = True
                            rt      = time.time() - onset
                            kd_ts   = time.time()
                        elif ev.type==pygame.KEYUP   and ev.key==pygame.K_SPACE and pressed and dur is None:
                            dur = time.time() - kd_ts
                        elif ev.type==pygame.QUIT:
                            pygame.quit(); exit()
                    pygame.time.wait(10)

                pygame.mixer.music.stop()

                # log
                resp = [
                    self.pid,
                    f"Run{trial}",
                    round(onset - t0, 4),
                    letter,
                    n,
                    desc,
                    "-".join(map(str,self.n_seq)),
                    "space" if pressed else "",
                    round(rt, 4) if rt is not None else "",
                    round(dur,4) if dur is not None else ""
                ]
                all_resps.append(resp)

            # inter‑block
            if blk_i < len(self.n_seq)-1:
                SCREEN.fill(BLACK)
                msg = FONT.render(f"{n}-back done. Next: {self.n_seq[blk_i+1]}-back", True, WHITE)
                SCREEN.blit(msg, msg.get_rect(center=(info.current_w//2, info.current_h//2)))
                pygame.display.flip()
                wait_key([pygame.K_SPACE])

        # E) Stop eye tracking
        stop_eye_recording(self.pid, f"Run{trial}", trial_folder)

        # F) Write CSV + rating
        csv_path = os.path.join(trial_folder, "main.csv")
        with open(csv_path, 'a', newline='', encoding='utf-8') as f:
            w = csv.writer(f)
            w.writerows(all_resps)
            print(f"[DEBUG] Wrote {len(all_resps)} rows → {csv_path}")

            # difficulty rating
            SCREEN.fill(BLACK)
            rmsg = FONT.render("Rate difficulty 1–5", True, WHITE)
            SCREEN.blit(rmsg, rmsg.get_rect(center=(info.current_w//2, info.current_h//2)))
            pygame.display.flip()
            k = wait_key([pygame.K_1,pygame.K_2,pygame.K_3,pygame.K_4,pygame.K_5])
            rating = {pygame.K_1:1,pygame.K_2:2,pygame.K_3:3,pygame.K_4:4,pygame.K_5:5}[k]
            w.writerow(["Difficulty Rating", rating])
            print(f"[DEBUG] Appended rating {rating}")

        # G) Trial‑done flash
        SCREEN.fill(BLACK)
        dmsg = FONT.render(f"Trial {trial} complete!", True, WHITE)
        SCREEN.blit(dmsg, dmsg.get_rect(center=(info.current_w//2, info.current_h//2)))
        pygame.display.flip()
        pygame.time.wait(800)

if __name__ == "__main__":
    AuditoryNBack().run()
