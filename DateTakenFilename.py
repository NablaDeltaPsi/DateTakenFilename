import tkinter as tk
import tkinter.font
from datetime import datetime
import datetime as dt
import piexif
import glob
import os
import sys
import ctypes
import shutil
import numpy as np

version = '1.0'

def blanks(number):
    string = ""
    for i in range(number):
        string = string + " "
    return string

def pts(number):
    return str(number) + "p"

def str2bool(string):
    if string.strip().lower() == "True":
        return True
    else:
        return False

def two_digits(integer):
    if integer < 10:
        string = "0" + str(integer)
    else:
        string = str(integer)
    return string

def check_date(y, m, d, h, mnt):
    try:
        dt.datetime(y, m, d, h, mnt)
        return True
    except:
        return False

def load_files(entered_files):
    all_files = glob.glob(entered_files, recursive=False)

    if len(entered_files) == 0:
        tk.messagebox.showerror(title="Error", message="Interrupt: Enter filenames!")
        sys.exit()

    if not os.path.isabs(os.path.dirname(entered_files)) or entered_files[0] == "\\":
        tk.messagebox.showerror(title="Error", message="Interrupt: Path (" + os.path.dirname(entered_files) + ") not valid!")
        sys.exit()

    for i in range(len(all_files)):
        if not os.path.isfile(all_files[i]):
            tk.messagebox.showerror(title="Error", message="Interrupt: " + all_files[i] + " is not a file!")
            sys.exit()

    if not all_files:
        tk.messagebox.showerror(title="Error", message="Couldn't find any files!")
        sys.exit()
    
    return all_files

def setImageDateTime(filename, date_taken):
    exif_dict = piexif.load(filename)
    # new_date = datetime(2018, 1, 1, 0, 0, 0).strftime("%Y:%m:%d %H:%M:%S")
    new_date = datetime(*date_taken[:6]).strftime("%Y:%m:%d %H:%M:%S")
    exif_dict['0th'][piexif.ImageIFD.DateTime] = new_date
    exif_bytes = piexif.dump(exif_dict)
    piexif.insert(exif_bytes, filename)

def setExifDateTime(filename, date_taken):
    exif_dict = piexif.load(filename)
    # new_date = datetime(2018, 1, 1, 0, 0, 0).strftime("%Y:%m:%d %H:%M:%S")
    new_date = datetime(*date_taken[:6]).strftime("%Y:%m:%d %H:%M:%S")
    exif_dict['Exif'][piexif.ExifIFD.DateTimeOriginal] = new_date
    #exif_dict['Exif'][piexif.ExifIFD.DateTimeDigitized] = new_date
    exif_bytes = piexif.dump(exif_dict)
    piexif.insert(exif_bytes, filename)

def displayEXIF(filename):
    info = piexif.ImageIFD.__dict__
    l = ['%s = %s' % (v, k) for k, v in info.items()]
    l.sort()
    for item in l:
        print(item)

    exif_dict = piexif.load(filename)
    for ifd_name in exif_dict:
        print(ifd_name + ":")
        if not ifd_name == "Exif":
            continue
        for key in exif_dict[ifd_name]:
            print(key, exif_dict[ifd_name][key])

def getImageDateTakenAttribute(filename):
    try:
        exif_dict = piexif.load(filename)
        # DT  = exif_dict['0th'][piexif.ImageIFD.DateTime]
        DTO = exif_dict['Exif'][piexif.ExifIFD.DateTimeOriginal]
        # DTD = exif_dict['Exif'][piexif.ExifIFD.DateTimeDigitized]
    except:
        DTO = 'empty'
    return DTO

def date_filename_type(filename):
    if not len(filename) >= 6:
        return 0
    elif not (filename[0:6].isnumeric() and filename[6] == "_"):
        return 0
    elif not len(filename) >= 11:
        return 1
    elif not (filename[7:11].isnumeric() and filename[11] == "_"):
        return 1
    else:
        return 2

def get_date_from_filename(filename):
    filetype = date_filename_type(filename)
    if filetype == 0:
        return 0, 0, 0, 0, 0
    elif filetype == 1:
        return int(filename[0:2]), int(filename[2:4]), int(filename[4:6]), 0, 0
    else:
        return int(filename[0:2]), int(filename[2:4]), int(filename[4:6]), int(filename[7:9]), int(filename[9:11])
    

def renameWithUserCheck(old_files, new_files, backup):
    
    print(old_files)
    print(new_files)

    # CONSISTENCY CHECK
    if not len(new_files) == len(old_files):
        print("\n" + ">> Interrupt: Something went wrong (code issue)!")
        return

    # LIST OF CHANGED FILES
    changing_files_from = []
    changing_files_to = []
    for i in range(len(old_files)):
        if not new_files[i] == old_files[i]:
            changing_files_from.append(old_files[i])
            changing_files_to.append(new_files[i])

    # GET MAXIMUM LENGTH FOR PRINTING
    max_length_from = 1
    max_length_to = 1
    for i in range(len(changing_files_from)):
        if len(os.path.basename(changing_files_from[i])) > max_length_from:
            max_length_from = len(os.path.basename(changing_files_from[i]))
        if len(os.path.basename(changing_files_to[i])) > max_length_to:
            max_length_to = len(os.path.basename(changing_files_to[i]))

    # USER CHECK
    print("\n" + blanks(3) + "User check" + "\n")
    message = "Do you want to rename these files?" + "\n\n"
    if not len(changing_files_from) == 0:
        message = message + "Path: " + os.path.dirname(changing_files_from[0]) + os.sep + "\n\n"
    for i in range(len(changing_files_from)):
        message = message + \
        os.path.basename(changing_files_from[i]).ljust(max_length_from) + "  >  " + \
        os.path.basename(changing_files_to[i]).ljust(max_length_to)   + "\n"
    msb = OwnMessagebox("Check files", message)
    if msb.choice==-1 or msb.choice==0:
        print("\n" + ">> Interrupted by user.")
        return

    # SKIP EMPTY HERE
    if len(changing_files_from) == 0:
        print("\n" + ">> Skip: Empty changing list.")
        return

    # BACKUP
    if backup and not len(changing_files_from) == 0:
        # first, find where to put the old files
        basic_path = os.path.dirname(changing_files_from[0]) + os.sep
        folders_found = 0
        while True:
            maybe_new_path = basic_path + "_old_files_" + str(folders_found + 1)
            if not os.path.exists(maybe_new_path):
                os.mkdir(maybe_new_path)
                new_path = maybe_new_path
                break
            else:
                folders_found = folders_found + 1
        print(blanks(3) + "Backup to: " + new_path + os.sep)
        # copy backup
        for i in range(len(changing_files_from)):
            shutil.copy2(basic_path + os.path.basename(changing_files_from[i]), new_path + os.sep + os.path.basename(changing_files_from[i]))
            print(blanks(3) + "COPY TO: " + new_path + os.sep + os.path.basename(changing_files_from[i]))

    # RENAME
    for i in range(len(changing_files_from)):
        if not os.path.isfile(changing_files_to[i]):
            print(blanks(3) + "OLD: " + changing_files_from[i])
            print(blanks(3) + "NEW: " + changing_files_to[i])
            os.rename(changing_files_from[i], changing_files_to[i])
        else:
            print(">> Skip: " + changing_files_to[i] + " already exists!")

def setDateTakenWithUserCheck(files, backup, y, m, d, *args):

    # treat optional time input
    if not ((len(args) == 0) or (len(args) == 2)):
        print("\n" + ">> Interrupt: Something went wrong (code issue)!")
        return
    if len(args) == 2:
        time_input = 1
        h = args[0]
        mnt = args[1]
    else:
        time_input = 0

    # CONSISTENCY CHECK
    if (not len(y) == len(files)) or (not len(m) == len(files)) or (not len(d) == len(files)):
        print("\n" + ">> Interrupt: Something went wrong (code issue)!")
        return
    if time_input:
        if (not len(h) == len(files)) or (not len(mnt) == len(files)):
            print("\n" + ">> Interrupt: Something went wrong (code issue)!")
            return

    # GET MAXIMUM LENGTH FOR PRINTING
    max_length = 1
    for i in range(len(files)):
        if len(os.path.basename(files[i])) > max_length:
            max_length = len(os.path.basename(files[i]))

    # USER CHECK
    print("\n" + blanks(3) + "User check" + "\n")
    message = "Do you want to change date_taken of these files?" + "\n\n"
    if not len(files) == 0:
        message = message + "Path: " + os.path.dirname(files[0]) + os.sep + "\n\n"
    for i in range(len(files)):
        if time_input:
            message = message + \
            os.path.basename(files[i]).ljust(max_length) + "  >  " + \
            os.path.basename(two_digits(d[i]) + "." + two_digits(m[i]) + "." + str(y[i]) + " " + two_digits(h[i]) + ":" + two_digits(mnt[i])).ljust(17)   + "\n"
        else:
            message = message + \
            os.path.basename(files[i]).ljust(max_length) + "  >  " + \
            os.path.basename(two_digits(d[i]) + "." + two_digits(m[i]) + "." + str(y[i])).ljust(17)   + "\n"
    msb = OwnMessagebox("Check files", message)
    if msb.choice==-1 or msb.choice==0:
        print("\n" + ">> Interrupted by user.")
        return

    # BACKUP
    if backup and not len(files) == 0:
        # first, find where to put the old files
        basic_path = os.path.dirname(files[0]) + os.sep
        folders_found = 0
        while True:
            maybe_new_path = basic_path + "_old_files_" + str(folders_found + 1)
            if not os.path.exists(maybe_new_path):
                os.mkdir(maybe_new_path)
                new_path = maybe_new_path
                break
            else:
                folders_found = folders_found + 1
        print(blanks(3) + "Backup to: " + new_path + os.sep)
        # copy backup
        for i in range(len(files)):
            shutil.copy2(basic_path + os.path.basename(files[i]), new_path + os.sep + os.path.basename(files[i]))
            print(blanks(3) + "COPY TO: " + new_path + os.sep + os.path.basename(files[i]))

    # SET DATE TAKEN
    for i in range(len(files)):
        try:
            if time_input:
                print(blanks(3) + "Set date_taken to: " + two_digits(d[i]) + "." + two_digits(m[i]) + "." + str(y[i]) + " " + two_digits(h[i]) + ":" + two_digits(mnt[i]))
                setExifDateTime(files[i], [y[i], m[i], d[i], h[i], mnt[i], 0])
            else:
                print(blanks(3) + "Set date_taken to: " + two_digits(d[i]) + "." + two_digits(m[i]) + "." + str(y[i]))
                setExifDateTime(files[i], [y[i], m[i], d[i], 0, 0, 0])
        except:
            print(">> Skip: Could not set date_taken by some reason...")



class OwnMessagebox():

    def __init__(self, title, msg):

        self.choice = -1
        self.root = tk.Toplevel()
        self.root.title(title)
        x = int(self.root.winfo_fpixels('400p'))
        y = int(self.root.winfo_fpixels('300p'))
        w = int(self.root.winfo_fpixels('200p'))
        h = int(self.root.winfo_fpixels('100p'))
        self.root.geometry(f"{x}x{y}+{w}+{h}")       

        self.label_message = tk.Text(self.root, wrap="none")
        self.label_message.place(x=pts(10), y=pts(10), relwidth=1.0, width=pts(-35), relheight=1.0, height=pts(-65), anchor='nw')
        self.label_message.insert('end', msg)
        self.label_message.config(state='disabled')

        self.scrollbx = tk.Scrollbar(self.root, orient='horizontal', command=self.label_message.xview)
        self.scrollbx.place(x=pts(10), rely=1.0, y=pts(-55), relwidth = 1.0, width=pts(-35), height=pts(15), anchor='nw')
        self.label_message['xscrollcommand'] = self.scrollbx.set

        self.scrollby = tk.Scrollbar(self.root, orient='vertical', command=self.label_message.yview)
        self.scrollby.place(relx=1.0, x=pts(-25), y=pts(10), width=pts(15), height=pts(-65), relheight = 1.0, anchor='nw')
        self.label_message['yscrollcommand'] = self.scrollby.set

        self.button_yes = tk.Button(self.root, text="Yes",command=self.chose_yes)
        self.button_yes.place(relx=0.5, x=pts(-5), rely=1.0, y=pts(-30), width=pts(70), height=pts(20), anchor='ne')
        self.button_no = tk.Button(self.root, text="No",command=self.chose_no)
        self.button_no.place( relx=0.5, x=pts(+5), rely=1.0, y=pts(-30), width=pts(70), height=pts(20), anchor='nw')

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.wait_window()

    def on_closing(self):
        self.root.destroy()
        
    def chose_yes(self):
        self.root.destroy()
        self.choice = 1

    def chose_no(self):
        self.root.destroy()
        self.choice = 0

class NewGUI():
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("DateTakenFilename v" + version + " (File format YYMMDD_HHMM_*)")

        # get fontsize
        self.fontsize = 11
        self.default_font = tk.font.nametofont("TkDefaultFont")
        self.text_font = tk.font.nametofont("TkTextFont")
        self.default_font.configure(size=self.fontsize)
        self.text_font.configure(size=self.fontsize)

        # reset saved window position
        if os.path.isfile("DateTakenFilename.conf"):
            with open("DateTakenFilename.conf", "r") as conf:
                lines = conf.readlines()
                self.root.geometry(lines[0].strip())
                linenr = 1
                configs = []
                while True:
                    try:
                        configs.append(lines[linenr].strip())
                    except:
                        break
                    linenr += 1
        else:
            self.root.geometry('730x52+421+21')
            configs =['/*.jpg', '', 'False', 'True', 'True', 'False']
        self.root.protocol("WM_DELETE_WINDOW",  self.on_close)

        # icon and DPI
        try:
            self.root.iconbitmap('DateTakenFilename.ico')
            self.root.update() # important: recalculate the window dimensions
        except:
            print("Found no icon.")
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except:
            print("No succeess of:    ctypes.windll.shcore.SetProcessDpiAwareness(1)")

        # menu bar
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # start
        menubar.add_command(label="Start", command=self.process)

        # mode
        mode = tk.Menu(menubar, tearoff=0)
        self.radio_mode = tk.StringVar(self.root)
        self.modes = [
            "#1 - From filename to date_taken",
            "#2 - From date_taken to filename",
            "#3 - Remove date/time from filename",
            "#4 - Add fix date from menubar to filename", # filename and date_taken would require two user checks
            "#5 - Shift datetime in filename by day/hour/minute (positive)",
            "#6 - Shift datetime in filename by day/hour/minute (negative)",
        ]
        if configs[1]:
            self.radio_mode.set(configs[1])
        else:
            self.radio_mode.set(self.modes[0])            
        for opt in self.modes:
            mode.add_radiobutton(label=opt, value=opt, variable=self.radio_mode)
        menubar.add_cascade(label="Mode", menu=mode)

        # options
        anzeige = tk.Menu(menubar, tearoff=0)
        self.check_overwrite = tk.BooleanVar()
        self.check_includetime = tk.BooleanVar()
        self.check_nodateyet = tk.BooleanVar()
        self.check_backup = tk.BooleanVar()
        self.check_overwrite.set(configs[2])
        self.check_includetime.set(configs[3])
        self.check_nodateyet.set(configs[4])
        self.check_backup.set(str2bool(configs[4]))
        anzeige.add_checkbutton(label="Overwrite existing date_taken (#1)", onvalue=1, offvalue=0, variable=self.check_overwrite)
        anzeige.add_checkbutton(label="Include time (#1, #2)", onvalue=1, offvalue=0, variable=self.check_includetime)
        anzeige.add_checkbutton(label="Only prepend where no date yet (#2)", onvalue=1, offvalue=0, variable=self.check_nodateyet)
        anzeige.add_checkbutton(label="Backup (#1, #2, #3)", onvalue=1, offvalue=0, variable=self.check_backup)
        menubar.add_cascade(label="Options", menu=anzeige)

        # year
        menu_year = tk.Menu(menubar, tearoff=0)
        self.radio_year = tk.StringVar(self.root)
        self.radio_year.set(datetime.now().year)
        for opt in range(2010,2041):
            menu_year.add_radiobutton(label=opt, value=opt, variable=self.radio_year)
        menubar.add_cascade(label="Year", menu=menu_year)

        # month
        menu_month = tk.Menu(menubar, tearoff=0)
        self.radio_month = tk.StringVar(self.root)
        self.radio_month.set(datetime.now().month)
        for opt in range(1,13):
            menu_month.add_radiobutton(label=opt, value=opt, variable=self.radio_month)
        menubar.add_cascade(label="Month", menu=menu_month)

        # day
        menu_day = tk.Menu(menubar, tearoff=0)
        self.radio_day = tk.StringVar(self.root)
        self.radio_day.set(datetime.now().day)
        opt_days = list(range(0,32)) + [365, 366] 
        for opt in opt_days:
            menu_day.add_radiobutton(label=opt, value=opt, variable=self.radio_day)
        menubar.add_cascade(label="Day", menu=menu_day)

        # hour
        menu_hour = tk.Menu(menubar, tearoff=0)
        self.radio_hour = tk.StringVar(self.root)
        self.radio_hour.set(0)
        for opt in range(0,25):
            menu_hour.add_radiobutton(label=opt, value=opt, variable=self.radio_hour)
        menubar.add_cascade(label="Hour", menu=menu_hour)

        # mnt
        menu_mnt = tk.Menu(menubar, tearoff=0)
        self.radio_mnt = tk.StringVar(self.root)
        self.radio_mnt.set(0)
        for opt in range(0,61,2):
            menu_mnt.add_radiobutton(label=opt, value=opt, variable=self.radio_mnt)
        menubar.add_cascade(label="Min", menu=menu_mnt)

        self.entry_path = tk.Entry()
        self.entry_path.place(relx=0.5, y=pts(13), height=pts(15), relwidth=0.9, anchor='center')
        self.entry_path.insert(0, configs[0])

        self.root.mainloop()

    def process(self):

        all_files = load_files(self.entry_path.get())
        
        if self.radio_mode.get() == self.modes[0]:
            self.mode_1_name_to_date(all_files)
        elif self.radio_mode.get() == self.modes[1]:
            self.mode_2_date_to_name(all_files)
        elif self.radio_mode.get() == self.modes[2]:
            self.mode_3_remove_date(all_files)
        elif self.radio_mode.get() == self.modes[3]:
            self.mode_4_fix_date_to_name(all_files)
        elif self.radio_mode.get() == self.modes[4]:
            self.mode_5_shift_datetime(all_files, 1)
        elif self.radio_mode.get() == self.modes[5]:
            self.mode_5_shift_datetime(all_files, -1)

        print("\n" + blanks(3) + "FINISHED")
        print(blanks(3) + "----------------------------- \n")


    def mode_1_name_to_date(self, all_files):
        print("\n" + blanks(3) + "-----------------------------")
        print(blanks(3) + "START: NAME TO DATE \n")

        set_for_files = []
        y = []
        m = []
        d = []
        h = []
        mnt = []

        for i in range(len(all_files)):
            thisfilename = os.path.basename(all_files[i])
            print("\n   " + all_files[i])
            
            y_, m_, d_, h_, mnt_ = get_date_from_filename(thisfilename)
            if not y_ or (self.check_includetime.get() and not h_ and not mnt_):
                continue

            # get date_taken
            thisdate = str(getImageDateTakenAttribute(all_files[i]))
            print(blanks(3) + "Current date_taken: " + thisdate)

            # only write date_taken if overwrite is active or date_taken is empty
            if self.check_overwrite.get() == 0 and (not thisdate == 'empty'):
                print(">> Skip: File already has a date!")
                continue
            
            # prepare date lists
            set_for_files.append(all_files[i])
            y.append(2000+y_)
            m.append(m_)
            d.append(d_)
            if self.check_includetime.get():
                h.append(h_)
                mnt.append(mnt_)
        
        if not set_for_files:
            tk.messagebox.showerror(title="Error", message="Found some files but nothing to process!")
            return

        # set date_taken with static method
        if self.check_includetime.get():
            setDateTakenWithUserCheck(set_for_files, self.check_backup.get(), y, m, d, h, mnt)
        else:
            setDateTakenWithUserCheck(set_for_files, self.check_backup.get(), y, m, d)


    def mode_2_date_to_name(self, all_files):
        print("\n" + blanks(3) + "-----------------------------")
        print(blanks(3) + "START: DATE TO NAME \n")
        new_files = []

        for i in range(len(all_files)):
            thisfilename = os.path.basename(all_files[i])
            print("\n   " + all_files[i])
            
            if thisfilename == "":
                print(">> Skip: Entered string is no file!")
                new_files.append(all_files[i])
                continue

            # check if the filename already starts with a date
            if self.check_nodateyet.get() == 1 and date_filename_type(thisfilename):
                print(">> Skip: Filename already starts with date.")
                new_files.append(all_files[i])
                continue

            # check if date exists
            thisdate = str(getImageDateTakenAttribute(all_files[i]))
            print(blanks(3) + "date_taken: " + thisdate)
            if thisdate == 'empty':
                print(">> Skip: No date_taken found!")
                new_files.append(all_files[i])
                continue

            # determine date
            thisdate = thisdate[2:len(thisdate)-1]
            y = thisdate[2:4]
            m = thisdate[5:7]
            d = thisdate[8:10]
            h = thisdate[11:13]
            mnt = thisdate[14:16]
            sec = thisdate[17:19]
            
            # new filename
            if self.check_includetime.get() == 1:
                new_files.append(os.path.dirname(all_files[i]) + os.path.sep + y + m + d + "_" + h + mnt + "_" + os.path.basename(all_files[i]))
            else:
                new_files.append(os.path.dirname(all_files[i]) + os.path.sep + y + m + d + "_" + os.path.basename(all_files[i]))

        if not new_files or new_files == all_files:
            tk.messagebox.showerror(title="Error", message="Found some files but nothing to process!")
            return

        # rename with static method
        renameWithUserCheck(all_files, new_files, self.check_backup.get())


    def mode_3_remove_date(self, all_files):
        print("\n" + blanks(3) + "-----------------------------")
        print(blanks(3) + "START: REMOVE DATE \n")

        new_files = []
        for i in range(len(all_files)):
            thisfilename = os.path.basename(all_files[i])
            print("\n   " + all_files[i])
            
            filenametype = date_filename_type(thisfilename)

            # check if the filename starts with a date
            if filenametype == 0:
                print(">> Skip: Filename does not start with date.")
                new_files.append(all_files[i])
                continue
            elif filenametype == 1:
                new_files.append(os.path.dirname(all_files[i]) + os.path.sep + os.path.basename(all_files[i])[7:len(all_files[i])])
            else:
                new_files.append(os.path.dirname(all_files[i]) + os.path.sep + os.path.basename(all_files[i])[12:len(all_files[i])])

        if not new_files or new_files == all_files:
            tk.messagebox.showerror(title="Error", message="Found some files but nothing to process!")
            return
        
        # rename with static method
        renameWithUserCheck(all_files, new_files, self.check_backup.get())


    def mode_4_fix_date_to_name(self, all_files):
        print("\n" + blanks(3) + "-----------------------------")
        print(blanks(3) + "START: DATE OFFSET TO NAME \n")

        # determine date
        y = two_digits(int(self.radio_year.get()) - 2000)
        m = two_digits(int(self.radio_month.get()))
        d = two_digits(int(self.radio_day.get()))
        h = two_digits(int(self.radio_hour.get()))
        mnt = two_digits(int(self.radio_mnt.get()))
        
        if not check_date(int(y) + 2000, int(m), int(d), int(h), int(mnt)):
            tk.messagebox.showerror(title="Error", message="Date is invalid!")
            return

        new_files = []
        for i in range(len(all_files)):
            thisfilename = os.path.basename(all_files[i])
            print("\n   " + all_files[i])
            
            if thisfilename == "":
                print(">> Skip: Entered string is no file!")
                new_files.append(all_files[i])
                continue

            # check if the filename already starts with a date
            if self.check_nodateyet.get() and date_filename_type(thisfilename):
                print(">> Skip: Filename already starts with date.")
                new_files.append(all_files[i])
                continue

            # new filename
            if self.check_includetime.get():
                new_files.append(os.path.dirname(all_files[i]) + os.path.sep + y + m + d + "_" + h + mnt + "_" + os.path.basename(all_files[i]))
            else:
                new_files.append(os.path.dirname(all_files[i]) + os.path.sep + y + m + d + "_" + os.path.basename(all_files[i]))

        if not new_files or new_files == all_files:
            tk.messagebox.showerror(title="Error", message="Found some files but nothing to process!")
            return

        # rename with static method
        renameWithUserCheck(all_files, new_files, self.check_backup.get())


    def mode_5_shift_datetime(self, all_files, dir):
        print("\n" + blanks(3) + "-----------------------------")
        print(blanks(3) + "START: SHIFT DATETIME \n")

        # determine new datetime
        td_d = dir * int(self.radio_day.get())
        td_h = dir * int(self.radio_hour.get())
        td_mnt = dir * int(self.radio_mnt.get())
 
        new_files = []
        for i in range(len(all_files)):
            thisfilename = os.path.basename(all_files[i])
            print("\n   " + all_files[i])
            
            if thisfilename == "":
                print(">> Skip: Entered string is no file!")
                new_files.append(all_files[i])
                continue

            # check if the filename already starts with a date
            filename_type = date_filename_type(thisfilename)
            if not filename_type:
                print(">> Skip: Filename does not start with a date.")
                new_files.append(all_files[i])
                continue
            
            # determie new date
            y_, m_, d_, h_, mnt_ = get_date_from_filename(thisfilename)
            if not y_ or (self.check_includetime.get() and not h_ and not mnt_):
                new_files.append(all_files[i])
                continue
            current_date = dt.datetime(y_ + 2000, m_, d_, h_, mnt_)
            new_date = current_date + dt.timedelta(days=td_d, hours=td_h, minutes=td_mnt)
            y = two_digits(new_date.year - 2000)
            m = two_digits(new_date.month)
            d = two_digits(new_date.day)
            h = two_digits(new_date.hour)
            mnt = two_digits(new_date.minute)

            # new filename
            if filename_type == 2:
                new_files.append(os.path.dirname(all_files[i]) + os.path.sep + y + m + d + "_" + h + mnt + "_" + os.path.basename(all_files[i])[12:])
            elif filename_type == 1:
                new_files.append(os.path.dirname(all_files[i]) + os.path.sep + y + m + d + "_" + os.path.basename(all_files[i])[6:])

        if not new_files or new_files == all_files:
            tk.messagebox.showerror(title="Error", message="Found some files but nothing to process!")
            return

        # rename with static method
        renameWithUserCheck(all_files, new_files, self.check_backup.get())


    def on_close(self):
        with open("DateTakenFilename.conf", "w") as conf: 
            conf.write(self.root.geometry() + "\n")
            conf.write(self.entry_path.get() + "\n")
            conf.write(str(self.radio_mode.get()) + "\n")
            conf.write(str(self.check_overwrite.get()) + "\n")
            conf.write(str(self.check_includetime.get()) + "\n")
            conf.write(str(self.check_nodateyet.get()) + "\n")
            conf.write(str(self.check_backup.get()))
        self.root.destroy()


if __name__ == '__main__':
    new = NewGUI()

