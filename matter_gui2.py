import tkinter as tk
import subprocess
import threading

CHIP_TOOL = "/home/ubuntu/apps/chip-tool"
ENDPOINT = "1"
LOG_FILE = "matter_controller.log"

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
        result = subprocess.check_output(
            ["nmcli", "-t", "-f", "SSID", "dev", "wifi", "list"],
            text=True
        )
        ssids = list(set([line.strip() for line in result.split("\n") if line.strip()]))
        return ssids
    except Exception as e:
        print("WiFi scan failed:", e)
        return []


def get_next_node_id():
    used = set(int(v) for v in devices.values())
    node_id = 1
    while node_id in used:
        node_id += 1
    return str(node_id)


def append_log(log_widget, message):
    print(message)
    log_widget.insert(tk.END, message + "\n")
    log_widget.see(tk.END)

    with open(LOG_FILE, "a") as f:
        f.write(message + "\n")


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

import time

def auto_run_bulbs(root, status):
    def task():
        while True:
            if not devices:
                root.after(0, lambda: status.set("Waiting for devices..."))
                time.sleep(2)
                continue

            for name, node_id in list(devices.items()):
                root.after(0, lambda n=name: status.set(f"AUTO → ON {n}"))
                print(f"AUTO ON → {name} ({node_id})")

                subprocess.run(
                    [CHIP_TOOL, "onoff", "on", node_id, ENDPOINT],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                )

                time.sleep(2)

                root.after(0, lambda n=name: status.set(f"AUTO → OFF {n}"))
                print(f"AUTO OFF → {name} ({node_id})")

                subprocess.run(
                    [CHIP_TOOL, "onoff", "off", node_id, ENDPOINT],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                )

                time.sleep(2)

    threading.Thread(target=task, daemon=True).start()



def remove_device(log_widget, listbox):
    global current_device
    sel = listbox.curselection()
    if not sel:
        append_log(log_widget, "No device selected")
        return

    device = listbox.get(sel[0])
    devices.pop(device, None)
    listbox.delete(sel[0])
    current_device = None
    append_log(log_widget, "Device removed")


def create_log_panel(root):
    log_frame = tk.Frame(root)
    log_frame.pack(fill="both", expand=True, padx=10, pady=10)

    scrollbar = tk.Scrollbar(log_frame)
    scrollbar.pack(side="right", fill="y")

    log_widget = tk.Text(
        log_frame,
        height=12,
        wrap="word",
        yscrollcommand=scrollbar.set
    )
    log_widget.pack(fill="both", expand=True)

    scrollbar.config(command=log_widget.yview)
    return log_widget


def show_home(root):
    for w in root.winfo_children():
        w.destroy()

    top = tk.Frame(root)
    top.pack(fill="x")

    tk.Label(top, text="Matter Controller", font=("Arial", 14)).pack(side="left", padx=10)
    tk.Button(
        top,
        text="+",
        font=("Arial", 16),
        command=lambda: show_add_device(root)
    ).pack(side="right", padx=10)

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

    tk.Button(
        right,
        text="REMOVE",
        width=15,
        command=lambda: remove_device(log_widget, listbox)
    ).pack(pady=5)


def show_add_device(root, status):
    for w in root.winfo_children():
        w.destroy()

    tk.Label(root, text="Add Matter Device", font=("Arial", 14)).pack(pady=10)
    tk.Label(root, text="Pairing Code").pack()
    code_entry = tk.Entry(root, width=30)
    code_entry.pack(pady=3)

    tk.Label(root, text="WiFi SSID").pack()

    wifi_frame = tk.Frame(root)
    wifi_frame.pack(pady=3)

    wifi_list = get_wifi_list()
    ssid_var = tk.StringVar()

    if wifi_list:
        ssid_var.set(wifi_list[0])
    else:
        ssid_var.set("")

    ssid_dropdown = tk.OptionMenu(wifi_frame, ssid_var, *wifi_list)
    ssid_dropdown.pack(side="left", padx=5)

    ssid_entry = tk.Entry(wifi_frame, width=20)
    ssid_entry.pack(side="left")

    tk.Label(root, text="WiFi Password").pack()
    pwd_entry = tk.Entry(root, width=30, show="*")
    pwd_entry.pack(pady=3)

    def pair():
        pairing_code = code_entry.get().strip()
        password = pwd_entry.get().strip()
        ssid = ssid_entry.get().strip() or ssid_var.get().strip()

        if not pairing_code or not ssid or not password:
            status.set("Enter pairing code, SSID and password")
            return

        node_id = get_next_node_id()
        device_name = f"Bulb {node_id}"
        status.set("Pairing started...")

        def task():
            try:
                cmd = [
                    CHIP_TOOL,
                    "pairing",
                    "code-wifi",
                    node_id,
                    pairing_code,
                    ssid,
                    password,
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
                    print(line.strip())      # prints logs in terminal
                    status.set(line.strip()) # shows logs in GUI

                p.wait()

                if p.returncode == 0:
                    devices[device_name] = node_id
                    status.set(f"Paired successfully: {device_name}")
                else:
                    status.set("Pairing failed. Check logs.")

            except Exception as e:
                status.set(f"Error: {e}")
                print("Error:", e)

        threading.Thread(target=task, daemon=True).start()
    tk.Button(root, text="Pair", command=pair).pack(pady=8)
    tk.Button(root, text="Back",
              command=lambda: show_home(root, status)).pack()

    tk.Label(root, textvariable=status, wraplength=380).pack(pady=10)

def app():
    root = tk.Tk()
    root.title("Matter Controller")
    root.geometry("420x420")

    status = tk.StringVar(value="Auto mode starting...")
    show_home(root, status)
    root.after(1000, lambda: auto_run_bulbs(root, status))

    root.mainloop()

