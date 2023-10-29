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

# uart = serial.Serial("/dev/ttyS0", baudrate=57600, timeout=1)
uart = serial.Serial("COM9", baudrate=57600, timeout=1)

finger = adafruit_fingerprint.Adafruit_Fingerprint(uart)

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

        emp_uuid, finger_print_id, fullname, description, shift, image, created_at, created_by_id = rows[
            0]

        conn.commit()

        select_checks_query = f"Select * FROM fingerprintapp_checkincheckout where employee_id = '{emp_uuid}' and date_trunc('day', created_at) = current_date order by created_at;"
        cur.execute(select_checks_query)
        checks = cur.fetchall()

        new_uuid = uuid.uuid4()
        created_at = datetime.now(timezone.utc)

        if (len(checks) > 0):
            reading_id, created_at_reading, entrance_type, employee_id, duration = checks[-1]

            time_difference = created_at - created_at_reading
            if time_difference.total_seconds() > 10:
                if entrance_type == 'check in':
                    new_duration = time_difference.total_seconds()
                    new_entrance_type = 'check out'
                    insert_query = "INSERT INTO fingerprintapp_checkincheckout (id, employee_id,created_at,entrance_type,duration) VALUES (%s,%s,%s,%s,%s);"
                    cur.execute(insert_query, (str(new_uuid), emp_uuid,
                                created_at, new_entrance_type, new_duration))
                else:
                    new_duration = 0
                    new_entrance_type = 'check in'
                    insert_query = "INSERT INTO fingerprintapp_checkincheckout (id, employee_id,created_at,entrance_type,duration) VALUES (%s,%s,%s,%s,%s);"
                    cur.execute(insert_query, (str(new_uuid), emp_uuid,
                                created_at, new_entrance_type, new_duration))
            else:
                messagebox.showerror("Error", "Complete Your Session !.")
                return False

        else:
            duration = 0
            new_entrance_type = 'check in'
            insert_query = "INSERT INTO fingerprintapp_checkincheckout (id, employee_id,created_at,entrance_type,duration) VALUES (%s,%s,%s,%s,%s);"
            cur.execute(insert_query, (str(new_uuid), emp_uuid,
                        created_at, new_entrance_type, duration))
        conn.commit()
        fingerprint_data = list(rows[0])
        fingerprint_data.insert(len(fingerprint_data), new_entrance_type)
        fingerprint_data = tuple(fingerprint_data)
        return fingerprint_data

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

        scan_button_style = ttk.Style()
        scan_button_style.configure("Big.TButton",
                                    font=("Arial", 20, 'bold'),
                                    background="sky blue",
                                    foreground="black")

        # Step 2: Apply the style to your button

        # Using grid to organize layout

        # Create frames for each row
        # for i in range(3):
        #     frame = ttk.Frame(self, padding="10")
        #     frame.grid(row=i, column=0, sticky=(tk.W, tk.E))
        #
        #     # Add image (using a label as a placeholder)
        #     img_label = ttk.Label(frame, text="Image {}".format(i + 1))
        #     img_label.grid(row=0, column=0, rowspan=2)
        #
        #     # Add check_in and check_out labels and values
        #     check_in_label = ttk.Label(frame, text="Check_in:")
        #     check_in_label.grid(row=0, column=1)
        #     check_in_value = ttk.Label(frame, text="Value {}".format(i + 1))
        #     check_in_value.grid(row=0, column=2)
        #
        #     check_out_label = ttk.Label(frame, text="Check_out:")
        #     check_out_label.grid(row=1, column=1)
        #     check_out_value = ttk.Label(frame, text="Value {}".format(i + 1))
        #     check_out_value.grid(row=1, column=2)
        #
        #     # Add name and description
        #     name_label = ttk.Label(frame, text="Name:")
        #     name_label.grid(row=0, column=3)
        #     description_label = ttk.Label(frame, text="Description:")
        #     description_label.grid(row=1, column=3)

        # # Left Side for Image
        # self.emp_image_1 = ttk.Label(
        #     self, background="white", borderwidth=1, relief="solid")
        # self.emp_image_1.grid(row=0, column=0, rowspan=6, padx=2, pady=2)
        #
        # # Left Side for Image
        # self.emp_image_2 = ttk.Label(self, background="white")
        # self.emp_image_2.grid(row=1, column=0, rowspan=6, padx=2, pady=4)
        #
        # # Left Side for Image
        # self.emp_image_3 = ttk.Label(self, background="white")
        # self.emp_image_3.grid(row=2, column=0, rowspan=6, padx=2, pady=6)

        # Left Side for Image
        self.emp_image = ttk.Label(self, background="white")
        self.emp_image.grid(row=0, column=0, rowspan=6, padx=2, pady=2)
        # Right Side for Other Content
        self.find_button = ttk.Button(
            self, text="SCAN", command=self.find, style="Big.TButton")
        self.find_button.grid(row=0, column=1, pady=10, sticky="nsew")
        self.entrance_title = ttk.Label(self, text="Entrance Type.",
                                        font=("Arial", 22, 'bold'),
                                        foreground="black",
                                        background="white",
                                        anchor="center",
                                        justify="center")
        self.entrance_title.grid(row=1, column=1, pady=10, sticky="nsew")
        self.title_label = ttk.Label(self, text="Employee Name.", font=("Arial", 22, 'bold'), foreground="black", background="white",
                                     anchor="center",
                                     justify="center")
        self.title_label.grid(row=2, column=1, pady=10, sticky="nsew")
        self.description_label = ttk.Label(self, text="Employee Description", font=("Arial", 18), foreground="black", background="white",
                                           anchor="center",
                                           justify="center")
        self.description_label.grid(row=3, column=1, pady=10, sticky="nsew")
        self.time_display = ttk.Label(self, text="00:00:00", font=("Arial", 24), foreground="black", background="white",
                                      anchor="center",
                                      justify="center")
        self.time_display.grid(row=4, column=1, pady=30, sticky="nsew")
        self.exit_btn = ttk.Button(
            self, text="Exit", command=self.exit, style="Big.TButton")
        self.exit_btn.grid(row=5, column=1, pady=10, sticky="nsew")

        # Configure the column weights to distribute space
        self.grid_columnconfigure(0, weight=2)  # Image column
        self.grid_columnconfigure(1, weight=2)  # Content column

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
            uuid, finger_print_id, fullname, description, shift, image, created_at, created_by_id, new_entrance_type = fingerprint_info
            self.title_label.config(text=fullname)
            self.description_label.config(text=description)
            self.emp_image_path_after_scan = image
            if (self.emp_image_path_after_scan != ''):
                image = Image.open('../../../media/' +
                                   self.emp_image_path_after_scan)
                image = image.resize((400, 400))  # Resize to 300x300 pixels
                self.photo = ImageTk.PhotoImage(image)
                self.emp_image.config(image=self.photo)
            if new_entrance_type == 'check in':
                self.entrance_title.config(text="Checked In")
                self.start()
            else:
                self.entrance_title.config(text="Checked Out")
                self.stop()
           # messagebox.showinfo("Detected", f"Detected #{finger.finger_id} with confidence {finger.confidence}")
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
