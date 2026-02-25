import tkinter as tk
import subprocess
import threading
import re
import colorsys
import time

CHIP_TOOL = "/home/ubuntu/apps/chip-tool"
ENDPOINT = "1"

devices = {}
bulb_counter = 2
cert = True


def remove_ansi(text):
    ansi_escape = re.compile(r'\x1B[@-_][0-?]*[ -/]*[@-~]')
    return ansi_escape.sub('', text)


def append_log(log, msg):
    print(msg)

    def safe_insert():
        if log.winfo_exists():
            log.insert(tk.END, msg + "\n")
            log.see(tk.END)

    try:
        log.after(0, safe_insert)
    except:
        pass


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


def all_on(log):
    if not devices:
        append_log(log, "No devices connected")
        return
    for name in devices:
        node = devices[name]["node_id"]
        run_chip_tool([CHIP_TOOL, "onoff", "on", str(node), ENDPOINT], log)
        time.sleep(0.15)

def all_off(log):
    if not devices:
        append_log(log, "No devices connected")
        return
    for name in devices:
        node = devices[name]["node_id"]
        run_chip_tool([CHIP_TOOL, "onoff", "off", str(node), ENDPOINT], log)
        time.sleep(0.15)


def warm_light(log):
    if not devices:
        append_log(log, "No devices connected")
        return
    for name in devices:
        node = devices[name]["node_id"]
        run_chip_tool([CHIP_TOOL, "onoff", "on", str(node), ENDPOINT], log)
        run_chip_tool([CHIP_TOOL, "levelcontrol", "move-to-level", "200", "5", "0", "0", str(node), ENDPOINT], log)
        run_chip_tool([CHIP_TOOL, "colorcontrol", "move-to-hue-and-saturation", "20", "200", "5", "0" , "0" , str(node), ENDPOINT], log)
        time.sleep(0.15)

def night_dim(log):
    if not devices:
        append_log(log, "No devices connected")
        return
    for name in devices:
        node = devices[name]["node_id"]
        run_chip_tool([CHIP_TOOL, "onoff", "on", str(node), ENDPOINT], log)
        run_chip_tool([CHIP_TOOL, "colorcontrol", "move-to-hue-and-saturation", "20", "200", "5", "0" , "0" , str(node), ENDPOINT], log)
        time.sleep(0.15)

def open_bulb_window(root, bulb_name, log):
    win = tk.Toplevel(root)
    win.title(bulb_name)
    win.geometry("320x450")

    tk.Label(win, text=bulb_name, font=("Arial", 14)).pack(pady=10)
    node_id = devices[bulb_name]["node_id"]

    def turn_on():
        run_chip_tool([CHIP_TOOL, "onoff", "on", str(node_id), ENDPOINT], log)

    def turn_off():
        run_chip_tool([CHIP_TOOL, "onoff", "off", str(node_id), ENDPOINT], log)

    def remove():
        devices.pop(bulb_name, None)
        append_log(log, f"{bulb_name} removed")
        win.destroy()
        show_home(root)

    def set_brightness(level):
        run_chip_tool([CHIP_TOOL, "levelcontrol", "move-to-level", str(level), "5", "0", "0", str(node_id), ENDPOINT], log)

    tk.Button(win, text="ON", width=20, command=turn_on).pack(pady=5)
    tk.Button(win, text="OFF", width=20, command=turn_off).pack(pady=5)
    tk.Button(win, text="REMOVE", width=20, command=remove).pack(pady=5)

    tk.Label(win, text="Brightness").pack()
    brightness_scale = tk.Scale(win, from_=0, to=254, orient="horizontal", length=250, command=set_brightness)
    brightness_scale.set(128)
    brightness_scale.pack(pady=15)

    tk.Label(win, text="Color Picker").pack()
    canvas_size = 200
    color_canvas = tk.Canvas(win, width=canvas_size, height=canvas_size)
    color_canvas.pack(pady=10)

    for x in range(canvas_size):
        hue = x / canvas_size
        for y in range(canvas_size):
            sat = 1 - (y / canvas_size)
            r, g, b = colorsys.hsv_to_rgb(hue, sat, 1)
            color = "#%02x%02x%02x" % (int(r * 255), int(g * 255), int(b * 255))
            color_canvas.create_line(x, y, x + 1, y, fill=color)

    def pick_color(event):
        x = event.x
        y = event.y
        if 0 <= x < canvas_size and 0 <= y < canvas_size:
            hue_val = int((x / canvas_size) * 254)
            sat_val = int((1 - y / canvas_size) * 254)
            r, g, b = colorsys.hsv_to_rgb(x / canvas_size, 1 - (y / canvas_size), 1)
            devices[bulb_name]["color"] = "#%02x%02x%02x" % (int(r * 255), int(g * 255), int(b * 255))
            run_chip_tool([CHIP_TOOL, "colorcontrol", "move-to-hue-and-saturation", str(hue_val), str(sat_val), "5", "0" , "0" , str(node_id), ENDPOINT], log)
            show_home(root)  

    color_canvas.bind("<Button-1>", pick_color)
    color_canvas.bind("<B1-Motion>", pick_color)

def show_home(root):
    for w in root.winfo_children():
        w.destroy()

    top = tk.Frame(root)
    top.pack(fill="x")
    tk.Label(top, text="Matter Controller", font=("Arial", 14)).pack(side="left", padx=10)
    tk.Button(top, text="+", width=3, command=lambda: show_add_device(root)).pack(side="right", padx=10)

    quick = tk.Frame(root)
    quick.pack(fill="x", pady=4)
    dummy_log = tk.Text(root)

    all_on_btn = tk.Button(quick, text="All ON", width=10, command=lambda: all_on(dummy_log))
    all_off_btn = tk.Button(quick, text="All OFF", width=10, command=lambda: all_off(dummy_log))
    warm_light_btn = tk.Button(quick, text="Warm Light", width=12, command=lambda: warm_light(dummy_log))
    night_dim_btn = tk.Button(quick, text="Night Dim", width=12, command=lambda: night_dim(dummy_log))

    state = tk.NORMAL if devices else tk.DISABLED
    all_on_btn.config(state=state)
    all_off_btn.config(state=state)
    warm_light_btn.config(state=state)
    night_dim_btn.config(state=state)

    all_on_btn.pack(side="left", padx=5)
    all_off_btn.pack(side="left", padx=5)
    warm_light_btn.pack(side="left", padx=5)
    night_dim_btn.pack(side="left", padx=5)

    body = tk.Frame(root)
    body.pack(fill="both", expand=True)
    left = tk.Frame(body)
    left.pack(side="left", fill="both", expand=True, padx=10)

    tile_container = tk.Frame(left)
    tile_container.pack(fill="both", expand=True)

    log = tk.Text(root, height=10)
    log.pack(fill="both", padx=10, pady=10)

    row = 0
    for bulb_name in devices:
        tile_color = devices[bulb_name].get("color", "#ffffff")
        tile = tk.Frame(tile_container, width=220, height=50, bd=1, relief="solid", bg=tile_color)
        tile.grid(row=row, column=0, padx=5, pady=5)
        tile.grid_propagate(False)

        label = tk.Label(tile, text=bulb_name, bg=tile_color)
        label.pack(expand=True)

        tile.bind("<Button-1>", lambda e, name=bulb_name: open_bulb_window(root, name, log))
        label.bind("<Button-1>", lambda e, name=bulb_name: open_bulb_window(root, name, log))
        row += 1

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

        cmd = [CHIP_TOOL, "pairing", "code-wifi", str(node_id), ssid, password, pairing_code]
        if cert:
            cmd.extend(["--bypass-attestation-verifier", "true"])

        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        for line in p.stdout:
            append_log(log, line.rstrip())
        p.wait()

        if p.returncode != 0:
            append_log(log, "Pairing failed")
            return

        append_log(log, "Pairing successful.")

        read_cmd = [CHIP_TOOL, "basicinformation", "read", "product-name", str(node_id), "0"]
        read_result = subprocess.run(read_cmd, capture_output=True, text=True)
        output_clean = remove_ansi(read_result.stdout)

        bulb_name = f"Bulb {node_id}"
        match = re.search(r'ProductName.*?:\s*(.*)', output_clean)

        if match:
            extracted = match.group(1)
            extracted = re.sub(r'0x[0-9A-Fa-f]+\s*=\s*', '', extracted)
            extracted = extracted.replace('"', '').strip()
            if extracted:
                bulb_name = extracted

        devices[bulb_name] = {"node_id": node_id, "ssid": ssid, "color": "#ffffff"}
        bulb_counter += 1

        append_log(log, f"{bulb_name} device name detected.")

        def show_big_tile():
            popup = tk.Toplevel(root)
            popup.title("Device Added")
            popup.geometry("320x320")
            popup.resizable(False, False)
            popup.grab_set()

            tile_frame = tk.Frame(popup, width=280, height=230, bg="#ffffff", bd=2, relief="solid")
            tile_frame.pack(pady=20)
            tile_frame.pack_propagate(False)

            icon_label = tk.Label(tile_frame, text="💡", font=("Arial", 52), bg="#ffffff")
            icon_label.pack(expand=True)

            name_label = tk.Label(tile_frame, text=bulb_name, font=("Arial", 15, "bold"),
                                  bg="#ffffff", wraplength=250, justify="center")
            name_label.pack(pady=(0, 8))

            node_label = tk.Label(tile_frame, text=f"Node ID: {node_id}", font=("Arial", 10),
                                  bg="#ffffff", fg="#666666")
            node_label.pack()

            tk.Button(popup, text="OK", width=15, command=popup.destroy).pack(pady=10)

        root.after(0, show_big_tile)

    tk.Button(root, text="Pair", command=pair_device).pack(pady=5)
    tk.Button(root, text="Back", command=lambda: show_home(root)).pack()

def app():
    root = tk.Tk()
    root.title("Matter Controller")
    root.geometry("550x600")
    show_home(root)
    root.mainloop()


app()