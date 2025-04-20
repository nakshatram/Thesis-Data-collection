import tkinter as tk
from gui import Gui
from datetime import datetime
import os

def create_experiment_folder(participant_id):
    base_dir = "participants_data"
    os.makedirs(base_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    participant_path = os.path.join(base_dir, f"{participant_id}_{timestamp}")
    os.makedirs(participant_path, exist_ok=True)
    for trial_num in range(1, 6):
        trial_folder = os.path.join(participant_path, f"trial_{trial_num}")
        os.makedirs(trial_folder, exist_ok=True)
        main_file = os.path.join(trial_folder, "main.csv")
        with open(main_file, 'w', newline='', encoding='utf-8') as file:
            file.write("Participant ID,Run ID,Timestamp,Stimulus,N-back Level,Lighting Condition,N-back Sequence,Key Press,Response Time,Key Duration\n")
        eye_file = os.path.join(trial_folder, "eye_data.csv")
        with open(eye_file, 'w', newline='', encoding='utf-8') as file:
            file.write("Participant ID,Run ID,Timestamp,Left Pupil Dilation,Right Pupil Dilation,Blink\n")
    return participant_path

if __name__ == "__main__":
    root = tk.Tk()
    app = Gui(root, create_experiment_folder)
    root.mainloop()
