import cv2
import yaml
import numpy as np
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk

# Predefined list of labels with parent-child relationships
labels = [
    {"name": "root", "parent": "null"},
    {"name": "hip", "parent": "root"},
    {"name": "torso", "parent": "hip"},
    {"name": "neck", "parent": "torso"},
    {"name": "right_shoulder", "parent": "torso"},
    {"name": "right_elbow", "parent": "right_shoulder"},
    {"name": "right_hand", "parent": "right_elbow"},
    {"name": "left_shoulder", "parent": "torso"},
    {"name": "left_elbow", "parent": "left_shoulder"},
    {"name": "left_hand", "parent": "left_elbow"},
    {"name": "right_hip", "parent": "root"},
    {"name": "right_knee", "parent": "right_hip"},
    {"name": "right_foot", "parent": "right_knee"},
    {"name": "left_hip", "parent": "root"},
    {"name": "left_knee", "parent": "left_hip"},
    {"name": "left_foot", "parent": "left_knee"}
]

current_label_index = 0
points = []
img = None
original_img = None  # Keep a separate copy of the original image
display_img = None  # Image used for display
tk_img = None
polygon_points = []  # To store points for polygon
drawing_polygon = False

def load_image():
    global img, original_img, display_img, tk_img, points, canvas, current_label_index, polygon_points, drawing_polygon
    # Ask user to select an image file
    image_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.jpeg *.png")])
    if image_path:
        original_img = cv2.imread(image_path)
        img = original_img.copy()  # Make a copy for drawing
        display_img = original_img.copy()  # For displaying in the GUI
        
        # Reset points, label index, polygon points, and drawing mode
        points.clear()
        polygon_points.clear()
        current_label_index = 0
        drawing_polygon = False
        label_var.set(f"Label the point: {labels[current_label_index]['name']}")
        
        # Convert the image to PIL format and display it
        display_img_pil = Image.fromarray(cv2.cvtColor(display_img, cv2.COLOR_BGR2RGB))
        tk_img = ImageTk.PhotoImage(display_img_pil)
        canvas.config(scrollregion=canvas.bbox(tk.ALL))
        canvas.create_image(0, 0, anchor=tk.NW, image=tk_img)

def click_event(event):
    global points, tk_img, img, original_img, current_label_index, polygon_points, drawing_polygon
    x, y = event.x, event.y
    if drawing_polygon:
        polygon_points.append((x, y))
        if len(polygon_points) > 1:
            # Draw lines between points on the display image
            cv2.line(display_img, polygon_points[-2], polygon_points[-1], (255, 255, 255), 2)
        display_img_pil = Image.fromarray(cv2.cvtColor(display_img, cv2.COLOR_BGR2RGB))
        tk_img = ImageTk.PhotoImage(display_img_pil)
        canvas.create_image(0, 0, anchor=tk.NW, image=tk_img)
    else:
        if len(points) < len(labels):
            points.append({
                "loc": [x, y],
                "name": labels[current_label_index]["name"],
                "parent": labels[current_label_index]["parent"]
            })
            # Draw a white circle at the point on the display image
            cv2.circle(display_img, (x, y), 5, (255, 255, 255), -1)
            display_img_pil = Image.fromarray(cv2.cvtColor(display_img, cv2.COLOR_BGR2RGB))
            tk_img = ImageTk.PhotoImage(display_img_pil)
            canvas.create_image(0, 0, anchor=tk.NW, image=tk_img)
            current_label_index = (current_label_index + 1) % len(labels)
            label_var.set(f"Label the point: {labels[current_label_index]['name']}")

def save_points():
    if points:
        width = original_img.shape[1]
        height = original_img.shape[0]
        skeleton = []

        for point in points:
            skeleton.append({
                "loc": point["loc"],
                "name": point["name"],
                "parent": point["parent"]
            })

        data = {
            "width": width,
            "height": height,
            "skeleton": skeleton
        }

        # Ask user where to save the file
        file_path = filedialog.asksaveasfilename(defaultextension=".yaml", filetypes=[("YAML files", "*.yaml")])
        if file_path:
            with open(file_path, 'w') as file:
                yaml.dump(data, file)
            print(f"Points saved to {file_path}")
    else:
        print("No points to save.")

def start_drawing_polygon():
    global drawing_polygon
    drawing_polygon = True
    label_var.set("Click to define vertices of the polygon. Click 'Finish Drawing Polygon' when done.")

def finish_drawing_polygon():
    global img, display_img, tk_img, polygon_points, drawing_polygon
    drawing_polygon = False
    if len(polygon_points) > 2:
        # Close the polygon by drawing a line from the last point to the first
        cv2.line(display_img, polygon_points[-1], polygon_points[0], (255, 255, 255), 2)
        # Fill the polygon
        mask = np.zeros_like(original_img[:, :, 0], dtype=np.uint8)  # Single channel for mask
        cv2.fillPoly(mask, [np.array(polygon_points)], 255)
        separated_img = np.zeros_like(original_img)  # Start with black background
        separated_img[mask == 255] = [255, 255, 255]  # Fill polygon area with white
        
        # Display the separated image
        separated_img_pil = Image.fromarray(cv2.cvtColor(separated_img, cv2.COLOR_BGR2RGB))
        tk_img = ImageTk.PhotoImage(separated_img_pil)
        canvas.create_image(0, 0, anchor=tk.NW, image=tk_img)
        
        # Ask user where to save the separated image
        file_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png")])
        if file_path:
            cv2.imwrite(file_path, separated_img)
            print(f"Separated character image saved to {file_path}")
    else:
        print("Not enough points to draw polygon.")

def save_image_with_points():
    if original_img is not None and points:
        annotated_img = original_img.copy()
        for point in points:
            loc = tuple(point["loc"])
            # Draw a white circle at the point
            cv2.circle(annotated_img, loc, 5, (255, 255, 255), -1)

        # Ask user where to save the annotated image
        file_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png")])
        if file_path:
            cv2.imwrite(file_path, annotated_img)
            print(f"Annotated image saved to {file_path}")
    else:
        print("No image or points to save.")

# Initialize Tkinter window
root = tk.Tk()
root.title("Character Labeling for Animated Drawings")

# Create canvas for image display
canvas = tk.Canvas(root, width=600, height=400)
canvas.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

# Bind mouse event for drawing polygon
canvas.bind("<Button-1>", click_event)

# Create frame for buttons
button_frame = tk.Frame(root)
button_frame.pack(side=tk.RIGHT, fill=tk.Y)

# Load image button
load_image_button = tk.Button(button_frame, text="Load Image", command=load_image)
load_image_button.pack(pady=10)

# Start drawing polygon button
start_polygon_button = tk.Button(button_frame, text="Start Drawing Polygon", command=start_drawing_polygon)
start_polygon_button.pack(pady=10)

# Finish drawing polygon button
finish_polygon_button = tk.Button(button_frame, text="Finish Drawing Polygon", command=finish_drawing_polygon)
finish_polygon_button.pack(pady=10)

# Save points button
save_points_button = tk.Button(button_frame, text="Save yaml", command=save_points)
save_points_button.pack(pady=10)

# Save image with points button
save_image_button = tk.Button(button_frame, text="Save joint overlay", command=save_image_with_points)
save_image_button.pack(pady=10)

label_var = tk.StringVar()
label_var.set("Load an image to start labeling.")
label_instruction = tk.Label(button_frame, textvariable=label_var, wraplength=200)
label_instruction.pack(pady=20)

# Run the Tkinter event loop
root.mainloop()

# Print the recorded points
print("Recorded points:")
for point in points:
    print(point)
