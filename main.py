import time
import serial
from tkinter import ttk
import tkinter as tk
from tkinter import messagebox
import tkinter.simpledialog
import psycopg2
from PIL import Image, ImageTk
from tkinter import filedialog
import os
import shutil
import uuid
from datetime import datetime, timezone, timedelta
import adafruit_fingerprint
import urllib.request
# import base64
import io
from PIL import ImageTk, Image

# uart = serial.Serial("/dev/ttyS0", baudrate=57600, timeout=1)
# uart = serial.Serial("COM9", baudrate=57600, timeout=1)

# finger = adafruit_fingerprint.Adafruit_Fingerprint(uart)

##################################################


def db_connection_select_fingerprint(finger_print_id):

    try:

        # Database connection parameters
        dbname = 'test'
        user = 'test'
        password = 'test'
        host = 'localhost'
        port = '5432'  # Typically 5432 for PostgreSQL
        conn = psycopg2.connect(
            dbname=dbname,
            user=user,
            password=password,
            host=host,
            port=port
        )

        cur = conn.cursor()
        select_query = f"Select * FROM fingerprintapp_employee where finger_print_id = '{finger_print_id}';"
        cur.execute(select_query)
        rows = cur.fetchall()

        id, finger_print_id, fullname, description,  image, created_at, created_by_id, user_type_id = rows[
            0]

        get_user_type_query = f"Select title FROM fingerprintapp_usertype where id = '{user_type_id}';"
        cur.execute(get_user_type_query)
        user_type_title = cur.fetchall()
        user_type_title = list(user_type_title[0])
        conn.commit()

        fingerprint_data = list(rows[0])
        fingerprint_data = tuple(fingerprint_data)
        return [fingerprint_data, user_type_title[0]]

    except Exception as error:
        print(error)
        return [False, error]
    finally:
        cur.close()
        conn.close()


def get_fingerprint():
    """Get a finger-print image, template it, and see if it matches!"""
    print("Waiting for image...")
    while finger.get_image() != adafruit_fingerprint.OK:
        pass
    print("Templating...")
    if finger.image_2_tz(1) != adafruit_fingerprint.OK:
        return False
    print("Searching...")
    if finger.finger_search() != adafruit_fingerprint.OK:
        return False
    return True


# pylint: disable=too-many-branches
def get_fingerprint_detail():
    """Get a finger-print image, template it, and see if it matches!
    This time, print out each error instead of just returning on failure"""
    print("Getting image...", end="")
    i = finger.get_image()
    if i == adafruit_fingerprint.OK:
        print("Image taken")
    else:
        if i == adafruit_fingerprint.NOFINGER:
            print("No finger detected")
        elif i == adafruit_fingerprint.IMAGEFAIL:
            print("Imaging error")
        else:
            print("Other error")
        return False

    print("Templating...", end="")
    i = finger.image_2_tz(1)
    if i == adafruit_fingerprint.OK:
        print("Templated")
    else:
        if i == adafruit_fingerprint.IMAGEMESS:
            print("Image too messy")
        elif i == adafruit_fingerprint.FEATUREFAIL:
            print("Could not identify features")
        elif i == adafruit_fingerprint.INVALIDIMAGE:
            print("Image invalid")
        else:
            print("Other error")
        return False

    print("Searching...", end="")
    i = finger.finger_fast_search()
    # pylint: disable=no-else-return
    # This block needs to be refactored when it can be tested.
    if i == adafruit_fingerprint.OK:
        print("Found fingerprint!")
        return True
    else:
        if i == adafruit_fingerprint.NOTFOUND:
            print("No match found")
        else:
            print("Other error")
        return False


##################################################


def get_num(max_number):
    """Use input() to get a valid number from 0 to the maximum size
    of the library. Retry till success!"""
    i = -1
    while (i > max_number - 1) or (i < 0):
        try:
            i = int(input("Enter ID # from 0-{}: ".format(max_number - 1)))
        except ValueError:
            pass
    return i


class FingerprintApp(tk.Tk):

    def __init__(self):
        super().__init__()
        # Font styles

        self.image_name_with_extension = ''
        self.emp_image_path_after_scan = ''
        self.screen_width = self.winfo_screenwidth()
        self.screen_height = self.winfo_screenheight()
        self.geometry(f"{self.screen_width}x{self.screen_height}")

        self.label_font = ("Arial", 12)

        self.entry_font = ("Arial", 14)

        self.count = 0  # Counter in seconds
        self.running = False  # Track if the counter is running

        # Create a container frame
        container = ttk.Frame(self)
        container.grid(row=0, column=0, padx=10, pady=10, columnspan=3)

        scan_button_style = ttk.Style()
        scan_button_style.configure("Big.TButton",
                                    font=("Arial", 20, 'bold'),
                                    background="sky blue",
                                    foreground="black")

        self.exit_button_style = ttk.Style()
        self.exit_button_style.configure("TButton",
                                         font=("Arial", 20, 'bold'),
                                         background="red",
                                         foreground="black")

        # First Column
        self.emp_image1 = ttk.Label(self, borderwidth=2, text=datetime.now().strftime("%Y-%m-%d %I:%M %p"),
                                    font=(
                                        "Arial", 18),
                                    relief="solid", padding=2, background="white")

        self.emp_image1.grid(row=0, column=0, rowspan=2,
                             padx=2, pady=2)

        # Second Column
        self.emp_name_1 = ttk.Label(self, text="Employee Name.", font=(
            "Arial", 22, 'bold'), foreground="black", background="white", anchor="center", justify="center")
        self.emp_name_1.grid(row=0, column=1, pady=2, sticky="nsew")
        self.emp_desc_1 = ttk.Label(self, text="Employee Description", font=(
            "Arial", 18), foreground="black", background="white", anchor="center", justify="center")
        self.emp_desc_1.grid(row=1, column=1, pady=2, sticky="nsew")

        self.check_in_1 = ttk.Label(self, text="Check In", font=(
            "Arial", 22, 'bold'), foreground="black", background="white", anchor="center", justify="center")
        self.check_in_1.grid(row=0, column=2, pady=2, sticky="nsew")
        self.check_out_1 = ttk.Label(self, text="Check Out", font=(
            "Arial", 18), foreground="black", background="white", anchor="center", justify="center")
        self.check_out_1.grid(row=1, column=2, pady=2, sticky="nsew")

        #
        self.emp_image2 = ttk.Label(self, borderwidth=2, text='Trainer Image..',
                                    font=(
                                        "Arial", 18),
                                    relief="solid", padding=50, background="white")
        self.emp_image2.grid(row=2, column=0, rowspan=2,
                             padx=2, pady=2)

        self.emp_name_2 = ttk.Label(self, text="Employee Name.", font=(
            "Arial", 22, 'bold'), foreground="black", background="white", anchor="center", justify="center")
        self.emp_name_2.grid(row=2, column=1, pady=2, sticky="nsew")
        self.emp_desc_2 = ttk.Label(self, text="Employee Description", font=(
            "Arial", 18), foreground="black", background="white", anchor="center", justify="center")
        self.emp_desc_2.grid(row=3, column=1, pady=2, sticky="nsew")

        self.check_in_2 = ttk.Label(self, text="Employee Name.", font=(
            "Arial", 22, 'bold'), foreground="black", background="white", anchor="center", justify="center")
        self.check_in_2.grid(row=2, column=2, pady=2, sticky="nsew")
        self.check_out_2 = ttk.Label(self, text="Employee Description", font=(
            "Arial", 18), foreground="black", background="white", anchor="center", justify="center")
        self.check_out_2.grid(row=3, column=2, pady=2, sticky="nsew")
        #
        self.emp_image3 = ttk.Label(
            self, borderwidth=2, text='Trainee Image..',
            font=(
                "Arial", 18),
            relief="solid", padding=50,  background="white")
        self.emp_image3.grid(row=4, column=0, rowspan=2,
                             padx=2, pady=2)

        self.emp_name_3 = ttk.Label(self, text="Employee Name.", font=(
            "Arial", 22, 'bold'), foreground="black", background="white", anchor="center", justify="center")
        self.emp_name_3.grid(row=4, column=1, pady=2, sticky="nsew")
        self.emp_desc_3 = ttk.Label(self, text="Employee Description", font=(
            "Arial", 18), foreground="black", background="white", anchor="center", justify="center")
        self.emp_desc_3.grid(row=5, column=1, pady=2, sticky="nsew")

        self.check_in_3 = ttk.Label(self, text="Employee Name.", font=(
            "Arial", 22, 'bold'), foreground="black", background="white", anchor="center", justify="center")
        self.check_in_3.grid(row=4, column=2, pady=2, sticky="nsew")
        self.check_out_3 = ttk.Label(self, text="Employee Description", font=(
            "Arial", 18), foreground="black", background="white", anchor="center", justify="center")
        self.check_out_3.grid(row=5, column=2, pady=2, sticky="nsew")

        # Right Side for Other Content
        self.find_button = ttk.Button(
            self, text="SCAN", command=self.find, style="Big.TButton", padding=10)
        self.find_button.grid(row=6, column=1, pady=10, padx=2, sticky="nsew")

        self.exit_btn = ttk.Button(
            self, text="Exit", command=self.exit, style="TButton", padding=10)
        self.exit_btn.grid(row=6, column=2, pady=10, padx=2, sticky="nsew")

        # Configure the column weights to distribute space
        self.grid_columnconfigure(0, weight=2)
        self.grid_columnconfigure(1, weight=2)
        self.grid_columnconfigure(2, weight=2)

        # Configure the row weights
        for i in range(6):
            self.grid_rowconfigure(i, weight=1)

    def start(self):
        if not self.running:
            self.count = 0
            self.running = True
            self.update_counter()

    def stop(self):
        self.running = False

    def update_counter(self):
        if self.running:  # A simple condition to keep the counter running
            delta = timedelta(seconds=self.count)
            hours, remainder = divmod(self.count, 3600)
            minutes, seconds = divmod(remainder, 60)
            time_string = f"{hours:02}:{minutes:02}:{seconds:02}"
            self.time_display.config(text=time_string)
            self.count += 1
            self.after(1000, self.update_counter)  # Update every 1000ms or 1s

    def exit(self):
        self.destroy()

    def find(self):
        if get_fingerprint():
            fingerprint_info = db_connection_select_fingerprint(
                finger.finger_id)
            if fingerprint_info[0] == False:
                messagebox.showerror("Error", fingerprint_info[1])
                return
            id, finger_print_id, fullname, description, image, created_at, created_by_id, user_type_id = fingerprint_info[
                0]
            user_type = fingerprint_info[1]
            if user_type == 'Examiner':
                self.emp_name_1.config(text=fullname)
                self.emp_desc_1.config(text=description)
                with urllib.request.urlopen('http://127.0.0.1:8000/media' + image) as u:
                    raw_data = u.read()
                    image = Image.open(io.BytesIO(raw_data))
                    # Resize the image
                    new_width = 200
                    new_height = 200
                    resized_image = image.resize((new_width, new_height))
                    # Convert the resized image to PhotoImage
                    self.image = ImageTk.PhotoImage(resized_image)
                    # Set the image to the label
                    self.emp_image1.config(image=self.image)
            if user_type == 'Trainer':
                self.emp_name_2.config(text=fullname)
                self.emp_desc_2.config(text=description)
                with urllib.request.urlopen('http://127.0.0.1:8000/media' + image) as u:
                    raw_data = u.read()
                    image = Image.open(io.BytesIO(raw_data))
                    # Resize the image
                    new_width = 200
                    new_height = 200
                    resized_image = image.resize((new_width, new_height))
                    # Convert the resized image to PhotoImage
                    self.image = ImageTk.PhotoImage(resized_image)
                    # Set the image to the label
                    self.emp_image2.config(image=self.image)
            # trainee
            self.emp_name_3.config(text=fullname)
            self.emp_desc_3.config(text=description)
            with urllib.request.urlopen('http://127.0.0.1:8000/media' + image) as u:
                raw_data = u.read()
                image = Image.open(io.BytesIO(raw_data))
                # Resize the image
                new_width = 200
                new_height = 200
                resized_image = image.resize((new_width, new_height))
                # Convert the resized image to PhotoImage
                self.image = ImageTk.PhotoImage(resized_image)
                # Set the image to the label
                self.emp_image3.config(image=self.image)
        else:
            messagebox.showerror("Error", "Finger not found.")

# Function to get number for enroll or delete (simplified for GUI use)


def get_num():
    try:
        number = tk.simpledialog.askinteger("Input", "Enter ID # from 1-999:")
        return number
    except:
        return -1


if __name__ == "__main__":
    app = FingerprintApp()
    app.mainloop()
