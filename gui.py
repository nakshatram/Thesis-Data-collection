import tkinter as tk
import tkinter.messagebox as mbox
import random
import os
from generate_letter_seq import generate_letter_seq
from eye_tracking import calibrate_eye_tracker, start_eye_recording, stop_eye_recording
import sound_manager
from PIL import Image, ImageTk

class Gui:
    def __init__(self, root, setup_experiment_folder):
        self.root = root
        self.setup_experiment_folder = setup_experiment_folder
        self.trial_num = 1
        self.participant_id = ""
        self.participant_path = ""
        # Define lighting conditions; for trials 1-4 we choose from these; trial 5 is fixed.
        self.lighting_conditions = {
            '1': "Complete Darkness (0–5 lux)",
            '2': "Rather Dark (10–50 lux)",
            '3': "Low Light (≈200 lux)",
            '4': "Rather Bright (300–500 lux)",
            '5': "Bright Light (>1000 lux)"
        }
        self.lighting_order = []  # For trials 1-4; trial 5 will use condition '5'
        self.setup_gui()

    def setup_gui(self):
        self.root.title("N-back Experiment")
        # Clear any existing widgets.
        for widget in self.root.winfo_children():
            widget.destroy()
        tk.Label(self.root, text="Participant ID:").pack()
        self.id_entry = tk.Entry(self.root)
        self.id_entry.pack()
        tk.Label(self.root, text="Select N-back Sequence (e.g., 1-2-3):").pack()
        self.sequence_entry = tk.Entry(self.root)
        self.sequence_entry.pack()
        self.start_btn = tk.Button(self.root, text="Start Experiment", command=self.start_experiment)
        self.start_btn.pack()
        self.msg_label = tk.Label(self.root, text="")
        self.msg_label.pack()

    def start_experiment(self):
        self.participant_id = self.id_entry.get().strip()
        sequence_input = self.sequence_entry.get().strip()
        if not self.participant_id or not sequence_input:
            self.msg_label.config(text="Please enter Participant ID and N-back sequence (e.g., 1-2-3).")
            return
        try:
            self.n_back_sequence = [int(n) for n in sequence_input.split("-")]
            if len(self.n_back_sequence) != 3:
                raise ValueError
        except ValueError:
            self.msg_label.config(text="Invalid N-back sequence. Please enter like 1-2-3.")
            return
        self.participant_path = self.setup_experiment_folder(self.participant_id)
        calibrate_eye_tracker()
        # For trials 1-4: randomize from options '1' to '4'
        self.lighting_order = random.sample(['1', '2', '3', '4'], 4)
        self.run_trial()

    def run_trial(self):
        if self.trial_num > 5:
            mbox.showinfo("Experiment Completed", "Thank you for participating!")
            self.root.quit()
            return
        # For trial 5, fix lighting condition as '5' (Bright Light); otherwise use randomized order.
        if self.trial_num == 5:
            current_key = '5'
        else:
            current_key = self.lighting_order[self.trial_num - 1]
        self.current_lighting_desc = self.lighting_conditions[current_key]
        # Re-create msg_label since previous widgets might have been destroyed.
        self.msg_label = tk.Label(self.root, text=f"Trial {self.trial_num}: Prepare to set lighting condition.")
        self.msg_label.pack()
        self.prompt_lighting_adjustment()

    def prompt_lighting_adjustment(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        instruction = f"Please adjust the lab lights to:\n{self.current_lighting_desc}"
        tk.Label(self.root, text=instruction, font=("Helvetica", 16), fg="green").pack(pady=20)
        continue_btn = tk.Button(self.root, text="Continue", command=self.show_fixation_cross)
        continue_btn.pack(pady=10)

    def show_fixation_cross(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        try:
            fixation_image = Image.open("fixation_cross.png")
            fixation_image = fixation_image.resize((100, 100))
            self.fixation_photo = ImageTk.PhotoImage(fixation_image)
            tk.Label(self.root, image=self.fixation_photo).pack(pady=10)
        except Exception as e:
            tk.Label(self.root, text="+", font=("Helvetica", 48)).pack(pady=10)
        condition_text = f"Participant: {self.participant_id}\nLighting: {self.current_lighting_desc}\nN-back Sequence: {'-'.join(map(str, self.n_back_sequence))}"
        tk.Label(self.root, text=condition_text, font=("Helvetica", 14), fg="blue").pack(pady=5)
        self.root.after(2000, self.run_n_back_tasks)

    def run_n_back_tasks(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        self.trial_folder = os.path.join(self.participant_path, f"trial_{self.trial_num}")
        os.makedirs(self.trial_folder, exist_ok=True)
        # Start eye tracking for the entire trial.
        start_eye_recording(self.participant_id, f"Run{self.trial_num}", self.trial_folder)
        # For each N-back task (each level) in the sequence, run the task and show a break between them.
        for i, n_back in enumerate(self.n_back_sequence):
            seq, targets = generate_letter_seq(n_back, 10)
            sound_manager.play_n_back_sequence(
                seq,
                self.trial_folder,
                self.participant_id,
                self.trial_num,
                n_back,
                self.current_lighting_desc,
                "-".join(map(str, self.n_back_sequence))
            )
            if i < len(self.n_back_sequence) - 1:
                mbox.showinfo("Task Completed", f"{n_back}-back task complete.\nNext will be {self.n_back_sequence[i+1]}-back task.\nPress OK to continue.")
        # After all tasks in trial, stop eye tracking.
        stop_eye_recording(self.participant_id, f"Run{self.trial_num}", self.trial_folder)
        mbox.showinfo("Trial Completed", f"Trial {self.trial_num} is complete.\nPress OK to proceed to the next trial.")
        self.trial_num += 1
        self.run_trial()



def create_experiment_folder(participant_id):
    import os
    from datetime import datetime
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
