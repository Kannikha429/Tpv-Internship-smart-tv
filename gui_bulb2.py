import tkinter as tk
import subprocess
import threading

CHIP_TOOL = "/home/ubuntu/apps/chip-tool"
ENDPOINT = "1"

devices = {}
bulb_counter = 2
cert = True


def append_log(log, msg):
    print(msg)
    log.insert(tk.END, msg + "\n")
    log.see(tk.END)


def run_chip_tool(cmd, log):
    def task():
        try:
            append_log(log, "Running: " + " ".join(cmd))
            p = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            for line in p.stdout:
                append_log(log, line.rstrip())
            p.wait()
        except Exception as e:
            append_log(log, f"Error: {e}")

    threading.Thread(target=task, daemon=True).start()


def open_bulb_window(root, bulb_name, log):
    win = tk.Toplevel(root)
    win.title(bulb_name)
    win.geometry("250x200")

    tk.Label(win, text=bulb_name, font=("Arial", 14)).pack(pady=10)

    node_id = devices[bulb_name]["node_id"]

    def turn_on():
        run_chip_tool(
            [CHIP_TOOL, "onoff", "on", str(node_id), ENDPOINT],
            log
        )

    def turn_off():
        run_chip_tool(
            [CHIP_TOOL, "onoff", "off", str(node_id), ENDPOINT],
            log
        )

    def remove():
        devices.pop(bulb_name, None)
        append_log(log, f"{bulb_name} removed")
        win.destroy()
        show_home(root)

    tk.Button(win, text="ON", width=15, command=turn_on).pack(pady=5)
    tk.Button(win, text="OFF", width=15, command=turn_off).pack(pady=5)
    tk.Button(win, text="REMOVE", width=15, command=remove).pack(pady=5)


def show_home(root):
    for w in root.winfo_children():
        w.destroy()

    top = tk.Frame(root)
    top.pack(fill="x")

    tk.Label(top, text="Matter Controller", font=("Arial", 14)).pack(side="left", padx=10)
    tk.Button(top, text="+", width=3, command=lambda: show_add_device(root)).pack(side="right", padx=10)

    body = tk.Frame(root)
    body.pack(fill="both", expand=True)

    left = tk.Frame(body)
    left.pack(side="left", padx=10)

    listbox = tk.Listbox(left, width=20, height=10)
    listbox.pack()

    for b in devices:
        listbox.insert(tk.END, b)

    log = tk.Text(root, height=10)
    log.pack(fill="both", padx=10, pady=10)

    def select_bulb(event):
        sel = listbox.curselection()
        if not sel:
            return
        bulb_name = listbox.get(sel[0])
        open_bulb_window(root, bulb_name, log)

    listbox.bind("<<ListboxSelect>>", select_bulb)


def show_add_device(root):
    for w in root.winfo_children():
        w.destroy()

    tk.Label(root, text="Add Matter Device", font=("Arial", 14)).pack(pady=10)

    tk.Label(root, text="Pairing Code").pack()
    code_entry = tk.Entry(root, width=30)
    code_entry.pack(pady=3)

    tk.Label(root, text="WiFi SSID").pack()
    ssid_var = tk.StringVar(value="SMTV_TP-Link_3368")
    wifi_list = ["SMTV_TP-Link_3368", "TPV", "TP-Link_AX1500_2G"]
    tk.OptionMenu(root, ssid_var, *wifi_list).pack(pady=3)

    tk.Label(root, text="WiFi Password").pack()
    pwd_entry = tk.Entry(root, width=30)
    pwd_entry.pack(pady=3)

    log = tk.Text(root, height=8)
    log.pack(fill="both", padx=10, pady=10)

    def pair_device():
        global bulb_counter

        pairing_code = code_entry.get().strip()
        ssid = ssid_var.get()
        password = pwd_entry.get().strip()

        if not pairing_code or not password:
            append_log(log, "Enter pairing code and password")
            return

        node_id = bulb_counter

        append_log(log, "Pairing started...")

        cmd = [
            CHIP_TOOL,
            "pairing",
            "code-wifi",
            str(node_id),
            ssid,
            password,
            pairing_code,
        ]

        if cert:
            cmd.extend(["--bypass-attestation-verifier", "true"])

        p = subprocess.Popen(
		cmd,
		stdout=subprocess.PIPE,
		stderr=subprocess.STDOUT,
		text=True,
		buffsize=1
	)
        
	for line in p.stdout:
	    append_log(log,line.rstrip())
	p.wait() 

        if p.returncode != 0:
            append_log(log, "Pairing failed")
            return

        append_log(log, "Pairing successful")

        read_cmd = [
            CHIP_TOOL,
            "basicinformation",
            "read",
            "product-name",
            str(node_id),
            "0"
        ]

        read_result = subprocess.run(read_cmd, capture_output=True, text=True)
        append_log(log, read_result.stdout)

        bulb_name = f"Bulb {node_id}"  

        for line in read_result.stdout.splitlines():
            if "ProductName:" in line:
                bulb_name = line.split(":")[-1].strip()
                break

        append_log(log, f"Device name detected: {bulb_name}")

        devices[bulb_name] = {
            "node_id": node_id,
            "ssid": ssid
        }

        bulb_counter += 1

    tk.Button(root, text="Pair", command=pair_device).pack(pady=5)
    tk.Button(root, text="Back", command=lambda: show_home(root)).pack()


def app():
    root = tk.Tk()
    root.title("Matter Controller")
    root.geometry("500x520")
    show_home(root)
    root.mainloop()


app()
