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
from py122u import nfc


# uart = serial.Serial("/dev/ttyS0", baudrate=57600, timeout=1)
uart = serial.Serial("COM9", baudrate=57600, timeout=1)

finger = adafruit_fingerprint.Adafruit_Fingerprint(uart)

##################################################


def insert_data_check_in(user_id, time):

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
        new_uuid = uuid.uuid4()
        cur = conn.cursor()
        insert_query = f"INSERT INTO fingerprintapp_checkin (id, user_id, created_at) VALUES ('{new_uuid}', '{user_id}', '{datetime.now()}');"
        cur.execute(insert_query)
        conn.commit()

    except Exception as error:
        print(error)
        return [False, error]
    finally:
        cur.close()
        conn.close()


def insert_data_check_out(user_id, time):

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
        new_uuid = uuid.uuid4()
        cur = conn.cursor()
        insert_query = f"INSERT INTO fingerprintapp_checkout (id, user_id, created_at) VALUES ('{new_uuid}', '{user_id}', '{datetime.now()}');"
        cur.execute(insert_query)
        conn.commit()

    except Exception as error:
        print(error)
        return [False, error]
    finally:
        cur.close()
        conn.close()


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

        id, finger_print_id, fullname, description,  image, created_at, created_by_id, user_type_id, card_id = rows[
            0]
        print(rows[0])
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
        self.examiner_checked_in = False
        self.trainer_checked_in = False
        self.trainee_checked_in = False
        # self.screen_width = self.winfo_screenwidth()
        # self.screen_height = self.winfo_screenheight()
        # self.geometry(f"{self.screen_width}x{self.screen_height}")
        self.attributes('-fullscreen', True)

        self.label_font = ("Arial", 12)

        self.entry_font = ("Arial", 14)

        self.count = 0  # Counter in seconds
        self.running = False  # Track if the counter is running

        # Create a container frame
        container = ttk.Frame(self)
        container.grid(row=0, column=0, padx=10, pady=10, columnspan=3)

        scan_button_style = ttk.Style()
        scan_button_style.configure("Big.TButton",
                                    font=("Arial", 16, 'bold'),
                                    background="sky blue",
                                    foreground="black")

        self.exit_button_style = ttk.Style()
        self.exit_button_style.configure("TButton",
                                         font=("Arial", 16, 'bold'),
                                         background="red",
                                         foreground="black")

        # First Column
        self.emp_image1 = ttk.Label(self, borderwidth=2, text="Examiner Image...",
                                    font=(
                                        "Arial", 18),
                                    relief="solid", padding=2, background="white")

        self.emp_image1.grid(row=0, column=0, rowspan=2,
                             padx=2, pady=1)

        # Second Column
        self.emp_name_1 = ttk.Label(self, text="Examiner Name.", font=(
            "Arial", 16, 'bold'), foreground="black", background="white", anchor="center", justify="center")
        self.emp_name_1.grid(row=0, column=1, pady=1, sticky="nsew")
        self.emp_desc_1 = ttk.Label(self, text="Examiner Description", font=(
            "Arial", 14), foreground="black", background="white", anchor="center", justify="center")
        self.emp_desc_1.grid(row=1, column=1, pady=1, sticky="nsew")

        self.check_in_1 = ttk.Label(self, text="Check In", font=(
            "Arial", 16, 'bold'), foreground="black", background="white", anchor="center", justify="center")
        self.check_in_1.grid(row=0, column=2, pady=1, sticky="nsew")
        self.check_out_1 = ttk.Label(self, text="Check Out", font=(
            "Arial", 14), foreground="black", background="white", anchor="center", justify="center")
        self.check_out_1.grid(row=1, column=2, pady=1, sticky="nsew")

        #
        self.emp_image2 = ttk.Label(self, borderwidth=2, text='Trainer Image..',
                                    font=(
                                        "Arial", 18),
                                    relief="solid", padding=2, background="white")
        self.emp_image2.grid(row=2, column=0, rowspan=2,
                             padx=2, pady=1)

        self.emp_name_2 = ttk.Label(self, text="Trainer Name.", font=(
            "Arial", 16, 'bold'), foreground="black", background="white", anchor="center", justify="center")
        self.emp_name_2.grid(row=2, column=1, pady=1, sticky="nsew")
        self.emp_desc_2 = ttk.Label(self, text="Trainer Description", font=(
            "Arial", 14), foreground="black", background="white", anchor="center", justify="center")
        self.emp_desc_2.grid(row=3, column=1, pady=1, sticky="nsew")

        self.check_in_2 = ttk.Label(self, text="Check In.", font=(
            "Arial", 16, 'bold'), foreground="black", background="white", anchor="center", justify="center")
        self.check_in_2.grid(row=2, column=2, pady=1, sticky="nsew")
        self.check_out_2 = ttk.Label(self, text="Check Out", font=(
            "Arial", 14), foreground="black", background="white", anchor="center", justify="center")
        self.check_out_2.grid(row=3, column=2, pady=1, sticky="nsew")
        #
        self.emp_image3 = ttk.Label(
            self, borderwidth=2, text='Trainee Image..',
            font=(
                "Arial", 18),
            relief="solid", padding=2,  background="white")
        self.emp_image3.grid(row=4, column=0, rowspan=2,
                             padx=2, pady=1)

        self.emp_name_3 = ttk.Label(self, text="Trainee Name.", font=(
            "Arial", 16, 'bold'), foreground="black", background="white", anchor="center", justify="center")
        self.emp_name_3.grid(row=4, column=1, pady=1, sticky="nsew")
        self.emp_desc_3 = ttk.Label(self, text="Trainee Description", font=(
            "Arial", 14), foreground="black", background="white", anchor="center", justify="center")
        self.emp_desc_3.grid(row=5, column=1, pady=1, sticky="nsew")

        self.check_in_3 = ttk.Label(self, text="Check In.", font=(
            "Arial", 16, 'bold'), foreground="black", background="white", anchor="center", justify="center")
        self.check_in_3.grid(row=4, column=2, pady=1, sticky="nsew")
        self.check_out_3 = ttk.Label(self, text="Check Out", font=(
            "Arial", 14), foreground="black", background="white", anchor="center", justify="center")
        self.check_out_3.grid(row=5, column=2, pady=1, sticky="nsew")

        # Right Side for Other Content
        self.find_button = ttk.Button(
            self, text="SCAN Finger", command=self.findFinger, style="Big.TButton", padding=10)
        self.find_button.grid(row=6, column=0, pady=10, padx=2, sticky="nsew")

        # Right Side for Other Content
        self.find_button = ttk.Button(
            self, text="SCAN Card", command=self.findCard, style="Big.TButton", padding=10)
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

    def exit(self):
        self.destroy()

    def findCard(self):
        try:
            reader = nfc.Reader()
            reader.connect()
            uid = reader.get_uid()
            uid_str = '-'.join(map(str, uid))
            uid_hex = ' '.join([hex(byte) for byte in uid])
            print(f"UID: {uid_str}")
            # reader.info()
            # print(info)
        except Exception as e:
            messagebox.showerror("Error", "Place your Card at the reader.")

    def findFinger(self):
        current_utc_time = datetime.utcnow().strftime("%Y-%m-%d %I:%M %p")
        if get_fingerprint():
            fingerprint_info = db_connection_select_fingerprint(
                finger.finger_id)
            if fingerprint_info[0] == False:
                messagebox.showerror("Error", fingerprint_info[1])
                return
            print(fingerprint_info[0])
            id, finger_print_id,  fullname, description, image, created_at, created_by_id, user_type_id, card_id = fingerprint_info[
                0]
            user_type = fingerprint_info[1]
            if user_type == 'Examiner':
                if self.examiner_checked_in == False:
                    self.examiner_checked_in = True
                    self.emp_name_1.config(text='Examiner: ' + fullname)
                    self.emp_desc_1.config(text=description)
                    self.check_in_1.config(
                        text='Check In At: ' + current_utc_time)
                    with urllib.request.urlopen('http://127.0.0.1:8000/media/' + image) as u:
                        raw_data = u.read()
                        image = Image.open(io.BytesIO(raw_data))
                        # Resize the image
                        new_width = 200
                        new_height = 200
                        resized_image = image.resize((new_width, new_height))
                        # Convert the resized image to PhotoImage
                        self.image_1 = ImageTk.PhotoImage(resized_image)
                        # Set the image to the label
                        self.emp_image1.config(image=self.image_1)
                        insert_data_check_in(id, current_utc_time)
                else:
                    self.examiner_checked_in = False
                    insert_data_check_out(id, current_utc_time)
                    self.check_out_1.config(
                        text='Check Out At: ' + current_utc_time)
            if user_type == 'Trainer':
                if self.trainer_checked_in == False:
                    self.trainer_checked_in = True
                    self.emp_name_2.config(text='Trainer: '+fullname)
                    self.emp_desc_2.config(text=description)
                    self.check_in_2.config(
                        text='Check In At: ' + current_utc_time)
                    with urllib.request.urlopen('http://127.0.0.1:8000/media/' + image) as u:
                        raw_data = u.read()
                        image = Image.open(io.BytesIO(raw_data))
                        # Resize the image
                        new_width = 200
                        new_height = 200
                        resized_image = image.resize((new_width, new_height))
                        # Convert the resized image to PhotoImage
                        self.image_2 = ImageTk.PhotoImage(resized_image)
                        # Set the image to the label
                        self.emp_image2.config(image=self.image_2)
                        insert_data_check_in(id, current_utc_time)
                else:
                    self.trainer_checked_in = False
                    insert_data_check_out(id, current_utc_time)
                    self.check_out_2.config(
                        text='Check Out At: ' + current_utc_time)
            # trainee
            if user_type == 'Trainee':
                if self.trainee_checked_in == False:
                    if self.trainer_checked_in == True:
                        self.trainee_checked_in = True
                        self.emp_name_3.config(text='Trainee: ' + fullname)
                        self.emp_desc_3.config(text=description)
                        self.check_in_3.config(
                            text='Check In At: ' + current_utc_time)
                        with urllib.request.urlopen('http://127.0.0.1:8000/media/' + image) as u:
                            raw_data = u.read()
                            image = Image.open(io.BytesIO(raw_data))
                            # Resize the image
                            new_width = 200
                            new_height = 200
                            resized_image = image.resize(
                                (new_width, new_height))
                            # Convert the resized image to PhotoImage
                            self.image_3 = ImageTk.PhotoImage(resized_image)
                            # Set the image to the label
                            self.emp_image3.config(image=self.image_3)
                        insert_data_check_in(id, current_utc_time)
                    else:
                        messagebox.showerror(
                            "Error", "Trainer Must Check In First!!!")
                else:
                    if self.trainer_checked_in == False:
                        self.trainee_checked_in = False
                        insert_data_check_out(id, current_utc_time)
                        self.check_out_3.config(
                            text='Check Out At: ' + current_utc_time)
                    else:
                        messagebox.showerror(
                            "Error", "Trainer Must Check Out First!!!")

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
