import tkinter as tk
from PIL import ImageTk, ImageOps, Image


def is_within_delete_zone(x, y, marker_x, marker_y):
    marker_radius = 10
    distance = ((x - marker_x) ** 2 + (y - marker_y) ** 2) ** 0.5
    return distance <= marker_radius


class Application(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        self.geometry("1920x1080")
        self.map_file = None
        self.map_image = None
        self.marker_color = "red"
        self.title("Map Application")
        self.canvas = tk.Canvas(self)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.canvas.bind("<Button-1>", self.on_canvas_left_click)
        self.canvas.bind("<Button-3>", self.on_canvas_right_click)
        self.canvas.bind("<MouseWheel>", self.on_mousewheel)
        self.canvas.bind("<Tab>", lambda event: self.toggle_marker_color())
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.scrollbar_y = tk.Scrollbar(self, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.configure(yscrollcommand=self.scrollbar_y.set)

        self.scrollbar_x = tk.Scrollbar(self, orient=tk.HORIZONTAL, command=self.canvas.xview)
        self.scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.configure(xscrollcommand=self.scrollbar_x.set)
        self.toggle_button = tk.Button(self, text="Toggle Color", command=self.toggle_marker_color)
        self.toggle_button.pack(side=tk.RIGHT)

        self.zoom_factor = 1.0
        self.image = None
        self.image_width = 0
        self.image_height = 0
        self.resized_image = None

        self.canvas_image = None
        self.markers = []

        self.text_entry = tk.Entry(self, width=30)
        self.text_entry.pack()

        self.load_map_file()
        self.load_markers("markers.txt")

    def load_map_file(self):
        try:
            self.map_file = "rLyxAPO.jpeg"  # Set the map file name here
            self.image = Image.open(self.map_file)
            self.image_width, self.image_height = self.image.size
            self.resized_image = self.image
            self.update_canvas()
        except IOError:
            print("Failed to open the map image file.")

    def draw_map(self):
        self.map_image = ImageTk.PhotoImage(self.image)
        self.canvas.create_image(0, 0, anchor="nw", image=self.map_image)

    def update_canvas(self):
        self.canvas.delete("marker")  # Delete all markers

        canvas_width = int(self.image_width * self.zoom_factor)
        canvas_height = int(self.image_height * self.zoom_factor)
        self.canvas.config(scrollregion=(0, 0, canvas_width, canvas_height))
        self.canvas.config(width=self.canvas.winfo_width(), height=self.canvas.winfo_height())

        self.resized_image = ImageOps.fit(self.image, (canvas_width, canvas_height))
        image_tk = ImageTk.PhotoImage(self.resized_image)

        self.canvas_image = self.canvas.create_image(0, 0, anchor=tk.NW, image=image_tk)
        self.canvas.image = image_tk

        for marker in self.markers:
            x, y, text, color = marker
            self.draw_marker(x, y, text, color)  # Redraw the markers

        self.canvas.configure(scrollregion=self.canvas.bbox(tk.ALL))

    def draw_markers(self):
        for marker in self.markers:
            x, y, text, color = marker
            self.draw_marker(x, y, text, color)

    def draw_marker(self, x, y, text, color):
        if x is not None and y is not None:
            marker_x = int(x * self.zoom_factor)
            marker_y = int(y * self.zoom_factor)
            marker_radius = 10

            oval_id = self.canvas.create_oval(
                marker_x - marker_radius, marker_y - marker_radius,
                marker_x + marker_radius, marker_y + marker_radius,
                outline=color, width=2, tags="marker"
            )
            text_id = self.canvas.create_text(
                marker_x + marker_radius + 5, marker_y, text=text, anchor=tk.W, tags="marker"
            )

            return oval_id, text_id

        return None, None

    def toggle_marker_color(self):
        if self.marker_color == "red":
            self.marker_color = "blue"
        else:
            self.marker_color = "red"
        self.update_canvas()

    def add_marker(self, event):
        # if self.text_entry.get().strip() == "":
        #   return

        x, y = self.get_canvas_coordinates(event)
        text = self.text_entry.get()
        color = self.marker_color
        self.markers.append((x, y, text, color))
        self.draw_marker(x, y, text, color)
        self.save_markers("markers.txt")

    def get_canvas_coordinates(self, event=None):
        if event:
            x = self.canvas.canvasx(event.x) / self.zoom_factor
            y = self.canvas.canvasy(event.y) / self.zoom_factor
            return int(x), int(y)
        else:
            return None, None

    def on_canvas_left_click(self, event):
        if event:
            self.get_canvas_coordinates(event)
            self.text_entry.delete(0, tk.END)
            self.add_marker(event)

    def on_canvas_right_click(self, event):
        x, y = self.get_canvas_coordinates(event)
        if x is not None and y is not None:
            self.delete_marker(x, y)

    def delete_marker(self, x, y):
        marker_index = None
        for index, marker in enumerate(self.markers):
            marker_x, marker_y, *_ = marker
            if is_within_delete_zone(x, y, marker_x, marker_y):
                marker_index = index
                break
        if marker_index is not None:
            self.markers.pop(marker_index)
            self.save_markers("markers.txt")
            self.update_canvas()

    def on_mousewheel(self, event):
        zoom_in = event.delta > 0

        if zoom_in and self.zoom_factor < 2.0:
            self.zoom_factor += 0.1
        elif not zoom_in and self.zoom_factor > 0.5:
            self.zoom_factor -= 0.1

        self.update_canvas()

    def save_markers(self, file_path):
        try:
            with open(file_path, 'w') as file:
                for marker in self.markers:
                    x, y, text, color = marker
                    file.write(f"{x},{y},{text},{color}\n")
        except IOError as e:
            print(f"Failed to save markers. Error: {str(e)}")

    def load_markers(self, file_path):
        self.markers = []
        try:
            with open(file_path, 'r') as file:
                for line in file:
                    marker_data = line.strip().split(',')
                    if len(marker_data) < 3:
                        continue
                    x, y, text = marker_data[:3]
                    color = marker_data[3] if len(marker_data) > 3 else "red"
                    if x == "None" or y == "None":
                        continue
                    self.markers.append((float(x), float(y), text, color))
            self.update_canvas()
        except FileNotFoundError:
            print("Marker file not found. Creating a new markers file.")
            self.save_markers(file_path)


if __name__ == "__main__":
    map_file = "rLyxAPO.jpeg"
    app = Application()
    app.mainloop()
