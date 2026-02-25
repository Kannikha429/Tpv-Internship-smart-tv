import tkinter as tk
import subprocess
import threading
import time

CHIP_TOOL = "/home/ubuntu/apps/chip-tool"
ENDPOINT = "1"

devices = {
    "Bulb 1": "3",
    "Bulb 2": "4",
    "Bulb 3": "5",
    "Bulb 4": "6",
    "Bulb 5": "7",
}

current_device = None

def get_wifi_list():
    try:
        result=subprocess.check_output(
            ["nmcli", "-t", "-f", "SSID", "dev", "wifi" ,"list"],
        )
        ssids = list(set([line.strip() for line in result.split("\n") if line.strip()]))
        return ssids
    except Exception as e:
        print("Wifi scan failed:",e)
        return[]


def append_log(log_widget, message):
    print(message)
    log_widget.insert(tk.END, message + "\n")
    log_widget.see(tk.END)


def run(cmd, log_widget):
    def task():
        try:
            p = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
            for line in p.stdout:
                append_log(log_widget, line.rstrip())
            p.wait()
        except Exception as e:
            append_log(log_widget, f"Error: {e}")

    threading.Thread(target=task, daemon=True).start()


def turn_on(log_widget):
    if not current_device:
        append_log(log_widget, "Select a device first")
        return
    run([CHIP_TOOL, "onoff", "on", devices[current_device], ENDPOINT], log_widget)


def turn_off(log_widget):
    if not current_device:
        append_log(log_widget, "Select a device first")
        return
    run([CHIP_TOOL, "onoff", "off", devices[current_device], ENDPOINT], log_widget)


def auto_run_bulbs(root, status):
    def task():
        while True:
            for name, node_id in devices.items():
                root.after(0, lambda n=name: status.set(f"AUTO -> ON {n}"))
                subprocess.run(
                    [CHIP_TOOL, "onoff", "on", node_id, ENDPOINT],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                )
                time.sleep(10)

                root.after(0, lambda n=name: status.set(f"AUTO -> OFF {n}"))
                subprocess.run(
                    [CHIP_TOOL, "onoff", "off", node_id, ENDPOINT],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                )
                time.sleep(10)

    threading.Thread(target=task, daemon=True).start()


def create_log_panel(root):
    frame = tk.Frame(root)
    frame.pack(fill="both", expand=True, padx=10, pady=10)

    scrollbar = tk.Scrollbar(frame)
    scrollbar.pack(side="right", fill="y")

    log = tk.Text(frame, height=10, yscrollcommand=scrollbar.set)
    log.pack(fill="both", expand=True)

    scrollbar.config(command=log.yview)
    return log


def show_home(root, status):
    for w in root.winfo_children():
        w.destroy()
    top = tk.Frame(root)
    top.pack(fill="x")

    tk.Label(
        top,
        text="Matter Controller",
        font=("Arial", 14)
    ).pack(side="left", padx=10)

    tk.Button(
        top,
        text="+",
        font=("Arial", 16),
        width=3,
        command=lambda: show_add_device(root, status)
    ).pack(side="right", padx=10)
    
    tk.Label(root, textvariable=status).pack(pady=5)

    body = tk.Frame(root)
    body.pack(fill="both", expand=True)

    
    left = tk.Frame(body)
    left.pack(side="left", fill="y", padx=10)

    listbox = tk.Listbox(left, width=22)
    listbox.pack(fill="y")

    for d in devices:
        listbox.insert(tk.END, d)

    def select_device(event):
        global current_device
        sel = listbox.curselection()
        if sel:
            current_device = listbox.get(sel[0])

    listbox.bind("<<ListboxSelect>>", select_device)

    right = tk.Frame(body)
    right.pack(side="right", expand=True)

    log_widget = create_log_panel(root)

    tk.Button(
        right,
        text="ON",
        width=15,
        command=lambda: turn_on(log_widget)
    ).pack(pady=5)

    tk.Button(
        right,
        text="OFF",
        width=15,
        command=lambda: turn_off(log_widget)
    ).pack(pady=5)


def show_add_device(root, status):
    for w in root.winfo_children():
        w.destroy()

    tk.Label(root, text="Add Matter Device", font=("Arial", 14)).pack(pady=10)

    tk.Label(root, text="Pairing Code").pack()
    code_entry = tk.Entry(root, width=30)
    code_entry.pack(pady=3)

    tk.Label(root, text="WiFi SSID").pack()
    ssid_entry = tk.Entry(root, width=30)
    ssid_entry.pack(pady=3)

    tk.Label(root, text="WiFi Password").pack()
    pwd_entry = tk.Entry(root, width=30)
    pwd_entry.pack(pady=3)

    log_widget = create_log_panel(root)

    def pair():
        pairing_code = code_entry.get().strip()
        ssid = ssid_entry.get().strip()
        password = pwd_entry.get().strip()

        if not pairing_code or not ssid or not password:
            append_log(log_widget, "Enter pairing code, SSID and password")
            return 

        node_id = "2"
        device_name = f"Bulb {node_id}"

        append_log(log_widget, "Pairing started...")
        cert=True
        
        def task():
            try:
                cmd = [
                    CHIP_TOOL,
                    "pairing",
                    "code-wifi",
                    node_id,
                    ssid,
                    password,
                    pairing_code,
                    "--bypass-attestation-verifier",
                    "true",
                ]
                
                print("Running command:", " ".join(cmd))
                p = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                )

                for line in p.stdout:
                    append_log(log_widget, line.rstrip())

                p.wait()

                if p.returncode == 0:
                    devices[device_name] = node_id
                    append_log(log_widget, f"Paired successfully: {device_name}")
                else:
                    append_log(log_widget, "Pairing failed. Check logs above.")

            except Exception as e:
                append_log(log_widget, f"Error: {e}")

        threading.Thread(target=task, daemon=True).start()

    tk.Button(root, text="Pair", command=pair).pack(pady=8)
    tk.Button(
        root,
        text="Back",
        command=lambda: show_home(root, status)
    ).pack()


def app():
    root = tk.Tk()
    root.title("Matter Controller")
    root.geometry("420x520")

    status = tk.StringVar(value="Auto mode running")
    show_home(root, status)

    root.after(1000, lambda: auto_run_bulbs(root, status))
    root.mainloop()


app()

