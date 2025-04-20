import os
import time
import csv
import threading
import tobii_research as tr  # Ensure Tobii Pro SDK is installed and compatible

# Global variables for the eye tracker and CSV writing.
eye_tracker_available = False
eye_tracker = None
csv_file = None
csv_writer = None
participant_id_global = None
run_id_global = None

gaze_data_lock = threading.Lock()
gaze_data_buffer = []  # List to store (timestamp, left_pupil, right_pupil, blink_flag)

# Blink detection counters
global prev_blink, blink_count
prev_blink = 0
blink_count = 0

# Attempt to find and connect to the eye tracker.
trackers = tr.find_all_eyetrackers()
if trackers:
    eye_tracker = trackers[0]
    eye_tracker_available = True
    print("Connected to:", eye_tracker)
    # Query and set the highest supported gaze output frequency
    try:
        freqs = eye_tracker.get_all_gaze_output_frequencies()
        print("Supported gaze frequencies:", freqs)
        max_freq = max(freqs)
        eye_tracker.set_gaze_output_frequency(max_freq)
        print(f"Using gaze frequency: {eye_tracker.get_gaze_output_frequency()} Hz")
    except Exception as e:
        print("Could not set gaze output frequency:", e)
else:
    print("No Tobii tracker found. Running with simulated data.")

# Callback to process real-time gaze data.
def gaze_data_callback(gaze_data):
    global prev_blink, blink_count
    # Debug: inspect available keys once
    if not hasattr(gaze_data_callback, '_keys_printed'):
        print("Gaze stream keys:", gaze_data.keys())
        setattr(gaze_data_callback, '_keys_printed', True)

    # Extract timestamp and pupil diameters
    ts = gaze_data.get('system_time_stamp', time.time())
    left_pupil  = gaze_data.get('left_pupil_diameter', None)
    right_pupil = gaze_data.get('right_pupil_diameter', None)

    # Validity codes: 0 = valid, non-zero = invalid/blink
    left_valid  = gaze_data.get('left_validity', gaze_data.get('left_pupil_validity', 0))
    right_valid = gaze_data.get('right_validity', gaze_data.get('right_pupil_validity', 0))
    blink_flag  = 1 if (left_valid != 0 or right_valid != 0) else 0

    # Detect blink onset (0 -> 1 transition)
    if blink_flag and not prev_blink:
        blink_count += 1
    prev_blink = blink_flag

    with gaze_data_lock:
        gaze_data_buffer.append((ts, left_pupil, right_pupil, blink_flag))

# Calibration function
def calibrate_eye_tracker():
    if eye_tracker_available and eye_tracker is not None:
        print("Starting calibration...")
        # Insert your actual calibration code here if available.
        time.sleep(2)
        print("Calibration completed.")
    else:
        print("Eye tracker not connected. Skipping calibration.")

# Start eye data collection
def start_eye_recording(participant_id, run_id, folder_path):
    global csv_file, csv_writer, participant_id_global, run_id_global, gaze_data_buffer, blink_count, prev_blink
    participant_id_global = participant_id
    run_id_global = run_id
    gaze_data_buffer = []
    blink_count = 0
    prev_blink = 0

    if eye_tracker_available and eye_tracker is not None:
        eye_file_path = os.path.join(folder_path, "eye_data.csv")
        csv_file = open(eye_file_path, 'a', newline='', encoding='utf-8')
        csv_writer = csv.writer(csv_file)
        eye_tracker.subscribe_to(tr.EYETRACKER_GAZE_DATA, gaze_data_callback, as_dictionary=True)
        print("Started eye tracking (subscribed to gaze stream). Data will buffer until stop.")
    else:
        print("Eye tracker not available; simulated data will be used if needed.")

# Stop eye data collection and write to CSV
def stop_eye_recording(participant_id, run_id, folder_path):
    global csv_file, csv_writer, gaze_data_buffer, blink_count
    if eye_tracker_available and eye_tracker is not None:
        eye_tracker.unsubscribe_from(tr.EYETRACKER_GAZE_DATA, gaze_data_callback)
        print("Stopped eye tracking (unsubscribed). Writing data.")

    if csv_file:
        with gaze_data_lock:
            for (ts, left, right, blink_flag) in gaze_data_buffer:
                csv_writer.writerow([participant_id, run_id, ts, left, right, blink_flag])
            # Append total blink count at end
            csv_writer.writerow([participant_id, run_id, 'Blink Count', blink_count])
            gaze_data_buffer = []
        csv_file.close()
        csv_file = None
        csv_writer = None
        print(f"Eye tracking data (+ {blink_count} blinks) written to {folder_path}/eye_data.csv")

# Optional simulated data for offline testing
def simulate_eye_data(duration_sec=10):
    import random
    sim = []
    start = time.time()
    while time.time() - start < duration_sec:
        ts = time.time() - start
        left = random.uniform(2, 5)
        right= random.uniform(2, 5)
        blink= random.randint(0, 1)
        sim.append((ts, left, right, blink))
        time.sleep(0.1)
    return sim

def collect_eye_data_simulated(participant_id, run_id, trial_num, folder_path):
    sim_data = simulate_eye_data(10)
    eye_file = os.path.join(folder_path, "eye_data.csv")
    with open(eye_file, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if f.tell() == 0:
            writer.writerow(["Participant ID","Run ID","Timestamp","Left Pupil Dilation","Right Pupil Dilation","Blink"])
        for (ts, left, right, blink) in sim_data:
            writer.writerow([participant_id, run_id, ts, left, right, blink])
    print(f"Simulated eye data saved for trial {trial_num}.")
