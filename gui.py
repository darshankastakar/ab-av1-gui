import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
import threading
import sv_ttk
import darkdetect
from tkinterdnd2 import DND_FILES, TkinterDnD
import os
import sys

class AbAv1Gui(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()
        
        self.title("ab-av1 GUI")
        self.geometry("800x600")

        self.process = None
        self.is_cancelled = False
        
        # Check for ab-av1.exe before proceeding
        self.check_ab_av1_executable()

        # Set the theme to match the system theme
        sv_ttk.set_theme(darkdetect.theme())

        self.create_widgets()

    def check_ab_av1_executable(self):
        # Check in current directory
        if os.path.exists("ab-av1"):
            return
        
        # Check in PATH
        if os.system("where ab-av1 >nul 2>&1") == 0:
            return

        # If not found, show error and exit
        messagebox.showerror(
            "Error",
            "ab-av1 not found. Please ensure it's in the same directory as gui.py or in your system PATH."
        )
        sys.exit(1)

    def create_widgets(self):
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill="both", expand=True)
        main_frame.columnconfigure(0, weight=1)

        # --- Input Files Section ---
        input_frame = ttk.LabelFrame(main_frame, text="Input Files", padding=10)
        input_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        input_frame.columnconfigure(0, weight=1)

        self.input_files = []
        
        list_frame = ttk.Frame(input_frame)
        list_frame.grid(row=0, column=0, sticky="ew")
        list_frame.columnconfigure(0, weight=1)

        self.file_listbox = tk.Listbox(list_frame, selectmode=tk.EXTENDED, height=6)
        self.file_listbox.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        self.file_listbox.drop_target_register(DND_FILES)
        self.file_listbox.dnd_bind('<<DropEnter>>', self.drop_enter)
        self.file_listbox.dnd_bind('<<DropLeave>>', self.drop_leave)
        self.file_listbox.dnd_bind('<<Drop>>', self.drop)
        
        list_scroll = ttk.Scrollbar(list_frame, command=self.file_listbox.yview, style="TScrollbar")
        list_scroll.grid(row=0, column=1, sticky="ns", pady=(0, 5))
        self.file_listbox.config(yscrollcommand=list_scroll.set)

        button_frame = ttk.Frame(input_frame)
        button_frame.grid(row=1, column=0, sticky="w")

        self.add_button = ttk.Button(button_frame, text="Add Files...", command=self.add_files)
        self.add_button.pack(side="left", padx=(0, 5))
        self.remove_button = ttk.Button(button_frame, text="Remove Selected", command=self.remove_selected_files)
        self.remove_button.pack(side="left", padx=(0, 5))
        self.clear_button = ttk.Button(button_frame, text="Clear All", command=self.clear_all_files)
        self.clear_button.pack(side="left")

        # --- Options Section ---
        options_frame = ttk.LabelFrame(main_frame, text="Encoding Options", padding=10)
        options_frame.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        options_frame.columnconfigure(1, weight=1)

        ttk.Label(options_frame, text="Encoder:").grid(row=0, column=0, padx=(0, 10), pady=5, sticky="w")
        self.encoder_var = tk.StringVar(value="libsvtav1")
        encoder_options = [
            "libsvtav1", "libx264", "libx265", "libvpx-vp9",
            "av1_qsv", "hevc_qsv", "h264_qsv",
            "av1_nvenc", "hevc_nvenc", "h264_nvenc"
        ]
        self.encoder_combobox = ttk.Combobox(options_frame, textvariable=self.encoder_var, values=encoder_options, state="readonly")
        self.encoder_combobox.grid(row=0, column=1, pady=5, sticky="ew")
        self.encoder_combobox.bind("<<ComboboxSelected>>", self.update_preset_options)

        ttk.Label(options_frame, text="Preset:").grid(row=1, column=0, padx=(0, 10), pady=5, sticky="w")
        self.preset_var = tk.StringVar()
        self.preset_combobox = ttk.Combobox(options_frame, textvariable=self.preset_var, state="readonly")
        self.preset_combobox.grid(row=1, column=1, pady=5, sticky="ew")
        self.update_preset_options()

        ttk.Label(options_frame, text="Min VMAF:").grid(row=2, column=0, padx=(0, 10), pady=5, sticky="w")
        self.min_vmaf_var = tk.DoubleVar(value=95.0)
        self.min_vmaf_entry = ttk.Entry(options_frame, textvariable=self.min_vmaf_var)
        self.min_vmaf_entry.grid(row=2, column=1, pady=5, sticky="ew")

        # --- Scaling ---
        scale_frame = ttk.Frame(options_frame)
        scale_frame.grid(row=3, column=0, columnspan=2, pady=5, sticky="w")
        
        self.scale_enabled_var = tk.BooleanVar(value=False)
        self.scale_checkbutton = ttk.Checkbutton(scale_frame, text="Scale Output:", variable=self.scale_enabled_var, command=self.toggle_scale_widgets)
        self.scale_checkbutton.pack(side="left", padx=(0, 5))

        self.scale_width_var = tk.StringVar()
        self.scale_width_entry = ttk.Entry(scale_frame, textvariable=self.scale_width_var, width=7, state="disabled")
        self.scale_width_entry.pack(side="left", padx=(0, 5))
        
        ttk.Label(scale_frame, text="x").pack(side="left", padx=(0, 5))

        self.scale_height_var = tk.StringVar()
        self.scale_height_entry = ttk.Entry(scale_frame, textvariable=self.scale_height_var, width=7, state="disabled")
        self.scale_height_entry.pack(side="left")

        # --- Command & Log Section ---
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.grid(row=3, column=0, sticky="nsew")
        main_frame.rowconfigure(3, weight=1)
        
        command_frame = ttk.LabelFrame(bottom_frame, text="Command", padding=10)
        command_frame.pack(fill="x", pady=(0, 10))
        command_frame.columnconfigure(0, weight=1)

        self.command_preview_var = tk.StringVar()
        preview_entry = ttk.Entry(command_frame, textvariable=self.command_preview_var, state="readonly")
        preview_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))

        action_buttons_frame = ttk.Frame(command_frame)
        action_buttons_frame.grid(row=0, column=1, sticky="e")

        self.generate_button = ttk.Button(action_buttons_frame, text="Preview", command=self.generate_commands)
        self.generate_button.pack(side="left", padx=(0, 5))
        self.run_button = ttk.Button(action_buttons_frame, text="Run All", command=self.run_encode, style="Accent.TButton")
        self.run_button.pack(side="left", padx=(0, 5))
        self.cancel_button = ttk.Button(action_buttons_frame, text="Cancel", command=self.cancel_encode, state="disabled")
        self.cancel_button.pack(side="left")

        log_frame = ttk.LabelFrame(bottom_frame, text="Output Log", padding=10)
        log_frame.pack(fill="both", expand=True)
        log_frame.rowconfigure(0, weight=1)
        log_frame.columnconfigure(0, weight=1)

        self.log_text = tk.Text(log_frame, wrap="word", state="disabled", relief="flat")
        self.log_text.grid(row=0, column=0, sticky="nsew")
        
        log_scroll_y = ttk.Scrollbar(log_frame, command=self.log_text.yview, style="TScrollbar")
        log_scroll_y.grid(row=0, column=1, sticky="ns")
        self.log_text.config(yscrollcommand=log_scroll_y.set)


    def add_files(self):
        filenames = filedialog.askopenfilenames(
            title="Select Input Files",
            filetypes=(("Video Files", "*.mkv *.mp4 *.avi *.mov"), ("All files", "*.* "))
        )
        if filenames:
            for f in filenames:
                if f not in self.input_files:
                    self.input_files.append(f)
                    self.file_listbox.insert(tk.END, f)

    def remove_selected_files(self):
        selected_indices = self.file_listbox.curselection()
        for i in reversed(selected_indices):
            self.file_listbox.delete(i)
            del self.input_files[i]

    def clear_all_files(self):
        self.file_listbox.delete(0, tk.END)
        self.input_files.clear()

    def drop_enter(self, event):
        event.widget.focus_force()
        print(f"DropEnter: {event.widget}")
        return event.action

    def drop_leave(self, event):
        print(f"DropLeave: {event.widget}")
        return event.action

    def drop(self, event):
        print(f"Drop: {event.widget} {event.data}")
        if event.data:
            # Use self.tk.splitlist to correctly parse the Tcl list of file paths
            files = self.tk.splitlist(event.data)
            for f in files:
                if f not in self.input_files:
                    self.input_files.append(f)
                    self.file_listbox.insert(tk.END, f)
        return event.action

    def toggle_scale_widgets(self):
        state = "normal" if self.scale_enabled_var.get() else "disabled"
        self.scale_width_entry.config(state=state)
        self.scale_height_entry.config(state=state)

    def update_preset_options(self, event=None):
        encoder = self.encoder_var.get()
        
        if encoder == "libsvtav1":
            values = [str(i) for i in range(14)]
            self.preset_combobox.config(values=values)
            if self.preset_var.get() not in values:
                self.preset_var.set("8")
        elif encoder.endswith("_qsv"):
            values = ["veryfast", "faster", "fast", "medium", "slow", "slower", "veryslow"]
            self.preset_combobox.config(values=values)
            if self.preset_var.get() not in values:
                self.preset_var.set("medium")
        elif encoder.endswith("_nvenc"):
            values = [str(i) for i in range(19)]
            self.preset_combobox.config(values=values)
            if self.preset_var.get() not in values:
                self.preset_var.set("8")
        elif encoder in ["libx264", "libx265"]:
            values = ["ultrafast", "superfast", "veryfast", "faster", "fast", "medium", "slow", "slower", "veryslow", "placebo"]
            self.preset_combobox.config(values=values)
            if self.preset_var.get() not in values:
                 self.preset_var.set("medium")
        else: # for libvpx-vp9 etc.
            values = [str(i) for i in range(11)]
            self.preset_combobox.config(values=values)
            if self.preset_var.get() not in values:
                self.preset_var.set("8")

    def generate_commands(self):
        if not self.input_files:
            self.log_message("Please add at least one input file.")
            return []

        commands = []
        for input_file in self.input_files:
            command = ["ab-av1", "auto-encode"]
            command.extend(["--input", input_file])
            command.extend(["--encoder", self.encoder_var.get()])
            command.extend(["--preset", str(self.preset_var.get())])
            command.extend(["--min-vmaf", str(self.min_vmaf_var.get())])

            if self.scale_enabled_var.get():
                width = self.scale_width_var.get()
                height = self.scale_height_var.get()
                if width and height:
                    command.extend(["--vfilter", f"scale={width}:{height}"])

            commands.append(command)
        
        # For preview, just show the first command
        self.command_preview_var.set(" ".join(f'\"{c}\"' if " " in c else c for c in commands[0]))
        return commands

    def run_encode(self):
        commands = self.generate_commands()
        if not commands:
            return

        self.log_text.config(state="normal")
        self.log_text.delete(1.0, "end")
        self.log_text.config(state="disabled")
        
        self.is_cancelled = False
        self.lock_ui()
        # Run in a separate thread to avoid blocking the GUI
        thread = threading.Thread(target=self.execute_commands, args=(commands,))
        thread.start()

    def execute_commands(self, commands):
        for i, command in enumerate(commands):
            if self.is_cancelled:
                break
            
            self.after(0, self.log_message, f"\n--- Starting encode {i+1} of {len(commands)} ---\n")
            self.after(0, self.log_message, f"Running command: {' '.join(command)}\n")

            self.process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )

            for line in iter(self.process.stdout.readline, ''):
                if self.is_cancelled:
                    # Need to ensure the process is terminated before breaking
                    self.process.terminate()
                    break
                self.after(0, self.log_message, line)
            
            if self.is_cancelled:
                break

            self.process.stdout.close()
            return_code = self.process.wait()

            if return_code == 0:
                self.after(0, self.log_message, f"\n--- Encode {i+1} finished successfully. ---\n")
            else:
                self.after(0, self.log_message, f"\n--- Encode {i+1} failed with exit code {return_code}. ---\n")

        if self.is_cancelled:
            self.after(0, self.log_message, "\n--- Batch encode cancelled by user. ---")
        else:
            self.after(0, self.log_message, "\n--- All encodes finished. ---")
        
        self.process = None
        self.after(0, self.unlock_ui)


    def cancel_encode(self):
        if self.process:
            self.is_cancelled = True
            self.process.terminate() # Ask the process to terminate

    def lock_ui(self):
        self.add_button.config(state="disabled")
        self.remove_button.config(state="disabled")
        self.clear_button.config(state="disabled")
        self.encoder_combobox.config(state="disabled")
        self.preset_combobox.config(state="disabled")
        self.min_vmaf_entry.config(state="disabled")
        self.scale_checkbutton.config(state="disabled")
        self.scale_width_entry.config(state="disabled")
        self.scale_height_entry.config(state="disabled")
        self.generate_button.config(state="disabled")
        self.run_button.config(state="disabled")
        self.cancel_button.config(state="normal")

    def unlock_ui(self):
        self.add_button.config(state="normal")
        self.remove_button.config(state="normal")
        self.clear_button.config(state="normal")
        self.encoder_combobox.config(state="normal")
        self.preset_combobox.config(state="normal")
        self.min_vmaf_entry.config(state="normal")
        self.scale_checkbutton.config(state="normal")
        self.toggle_scale_widgets() # Set scale entry state based on checkbox
        self.generate_button.config(state="normal")
        self.run_button.config(state="normal")
        self.cancel_button.config(state="disabled")

    def log_message(self, message):
        self.log_text.config(state="normal")
        self.log_text.insert("end", message)
        self.log_text.see("end")
        self.log_text.config(state="disabled")


if __name__ == "__main__":
    app = AbAv1Gui()
    app.mainloop()
