import tkinter as tk
import requests
import colorsys

SERVER = "http://192.168.0.247:5000"

ENDPOINT = "1"

devices = {
    "Bulb 2": {"node_id": 2, "state": False, "color": "#B8860B"}
}


def send_request(route, payload):
    try:
        r = requests.post(f"{SERVER}/{route}", json=payload, timeout=5)
        return r.json()
    except:
        print("Server not reachable")
        return None

def open_more_panel(root, bulb_name):
    win = tk.Toplevel(root)
    win.title(bulb_name + " Controls")
    win.geometry("320x420")

    node_id = devices[bulb_name]["node_id"]

    tk.Label(win, text=bulb_name,
             font=("Arial", 13, "bold")).pack(pady=10)

    tk.Label(win, text="Brightness").pack()

    def set_brightness(level):
        send_request("brightness", {
            "node_id": node_id,
            "level": int(level)
        })

    brightness_scale = tk.Scale(win, from_=0, to=254,
                                orient="horizontal",
                                length=250,
                                command=set_brightness)
    brightness_scale.pack(pady=10)

    tk.Label(win, text="Color Picker").pack()

    canvas_size = 180
    color_canvas = tk.Canvas(win,
                             width=canvas_size,
                             height=canvas_size)
    color_canvas.pack(pady=5)

    for x in range(canvas_size):
        hue = x / canvas_size
        for y in range(canvas_size):
            sat = 1 - (y / canvas_size)
            r, g, b = colorsys.hsv_to_rgb(hue, sat, 1)
            color = "#%02x%02x%02x" % (
                int(r*255), int(g*255), int(b*255))
            color_canvas.create_line(x, y, x+1, y, fill=color)

    def pick_color(event):
        x, y = event.x, event.y
        if 0 <= x < canvas_size and 0 <= y < canvas_size:
            hue_val = int((x / canvas_size) * 254)
            sat_val = int((1 - y / canvas_size) * 254)

            send_request("color", {
                "node_id": node_id,
                "hue": hue_val,
                "sat": sat_val
            })

    color_canvas.bind("<Button-1>", pick_color)
    color_canvas.bind("<B1-Motion>", pick_color)


def show_home(root):
    for w in root.winfo_children():
        w.destroy()

    tk.Label(root, text="Matter Controller",
             font=("Arial", 16)).pack(pady=10)

    for bulb_name in devices:

        tile_color = devices[bulb_name]["color"]

        tile = tk.Frame(root,
                        width=400,
                        height=100,
                        bd=2,
                        relief="solid",
                        bg=tile_color)
        tile.pack(pady=10)
        tile.pack_propagate(False)

        tk.Label(tile,
                 text=bulb_name,
                 bg=tile_color,
                 font=("Arial", 14, "bold")
                 ).pack(side="left", padx=15)

        def toggle_device(name=bulb_name):
            node = devices[name]["node_id"]
            state = devices[name].get("state", False)
            new_state = not state
            devices[name]["state"] = new_state

            endpoint = "off" if new_state else "on"

            send_request(endpoint, {"node_id": node})

            devices[name]["color"] = "#808080" if new_state else "#B8860B"

            show_home(root)

        tk.Button(tile,
                  text="Toggle",
                  command=toggle_device
                  ).pack(side="right", padx=10)

        tk.Button(tile,
                  text="⋮",
                  command=lambda n=bulb_name:
                  open_more_panel(root, n)
                  ).pack(side="right", padx=5)


def app():
    root = tk.Tk()
    root.title("Matter Controller Client")
    root.geometry("500x500")
    show_home(root)
    root.mainloop()


app()
