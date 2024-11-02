import tkinter as tk
import cv2
from PIL import Image, ImageTk
from picamera2 import Picamera2
import time
import RPi.GPIO as GPIO
import threading
import csv

# Set GPIO mode
GPIO.setmode(GPIO.BCM)

# Define GPIO pins
TRIG = 23
ECHO = 24

# Set up
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)


class CameraApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Vein Camera App")

        # Initialize Picamera2
        self.picam2 = Picamera2()
        config = self.picam2.create_preview_configuration()
        self.picam2.configure(config)

        # Start the camera
        self.picam2.start()

        # Create a canvas for video
        self.canvas = tk.Canvas(master, width=640, height=400)
        self.canvas.pack()

        # Create capture button
        self.capture_button = tk.Button(master, text="Capture", command=self.capture)
        self.capture_button.pack(pady=20)

        # Start the video stream
        self.update_video()

        # Initialize distance variable
        self.distance = None

    def update_video(self):
        # Capture frame-by-frame
        frame = self.picam2.capture_array()  # Capture frame
        img = Image.fromarray(frame)  # Convert to Image
        imgtk = ImageTk.PhotoImage(image=img)  # Convert to PhotoImage

        self.canvas.create_image(0, 0, anchor=tk.NW, image=imgtk)  # Display image
        self.master.imgtk = imgtk  # Keep a reference to avoid garbage collection

        # Start distance measurement in a separate thread
        threading.Thread(target=self.measure_distance).start()

        self.master.after(10, self.update_video)  # Repeat every 10 ms

    def measure_distance(self):
        # This method now runs in a separate thread
        GPIO.output(TRIG, True)
        time.sleep(0.00001)  # 10 microseconds
        GPIO.output(TRIG, False)

        # Measure the pulse duration
        pulse_start = time.time()
        while GPIO.input(ECHO) == 0:
            pulse_start = time.time()
        pulse_end = time.time()
        while GPIO.input(ECHO) == 1:
            pulse_end = time.time()

        # Calculate the distance in cm
        pulse_duration = pulse_end - pulse_start
        self.distance = pulse_duration * 17150  # Speed of sound is ~34300 cm/s
        self.distance = round(self.distance, 2)  # Round to 2 decimal places

        # Update the GUI with the distance
        self.master.after(0, self.update_distance_display)

    def update_distance_display(self):
        # Display the distance on the canvas
        if self.distance is not None:
            self.canvas.create_text(10, 10, anchor=tk.NW, text=f"Distance: {self.distance} cm", fill="white",
                                    font=("Arial", 16))

    def capture(self):
        # Capture an image
        frame = self.picam2.capture_array()  # Capture frame
        image_path = f"Gambar/capture_{time.strftime('%Y%m%d_%H%M%S')}_Distance:_{self.distance}cm.jpg"
        cv2.imwrite(image_path, frame)  # Save image using OpenCV
        print(f"Captured: {image_path}")

        # Save to CSV
        csv_file_path = "data.csv"
        with open(csv_file_path, mode='a', newline='') as file:
            writer = csv.writer(file)
            namefile = f"{time.strftime('%Y%m%d_%H%M%S')}"
            writer.writerow([namefile, self.distance])
            print(f"Saved to CSV: {time.strftime('%Y%m%d_%H%M%S')}, Distance: {self.distance} cm")

    def close(self):
        self.picam2.stop()
        GPIO.cleanup()  # Clean up GPIO
        self.master.quit()


if __name__ == "__main__":
    root = tk.Tk()
    app = CameraApp(root)

    # Close the application properly
    root.protocol("WM_DELETE_WINDOW", app.close)
    root.mainloop()

