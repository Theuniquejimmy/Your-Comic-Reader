import streamlit as st
import zipfile
from PIL import Image
import io

from ultralytics import YOLO

# Load your model once outside the function so it doesn't reload on every click
model = YOLO("comic_panels.pt") 

def detect_panels(image):
    # Run YOLO inference
    results = model.predict(source=image, conf=0.5) # conf=0.5 ignores low-confidence noise
    
    # Extract the raw boxes to a standard Python list
    raw_boxes = results[0].boxes.xyxy.tolist()
    
    # Pass them through our grouping algorithm
    return sort_panels_reading_order(raw_boxes)

# --- 2. CBZ/ZIP Extraction ---
@st.cache_data
def load_comic_pages(uploaded_file):
    pages = []
    with zipfile.ZipFile(uploaded_file, 'r') as archive:
        # Filter for image files and sort them alphabetically (standard reading order)
        valid_extensions = ('.png', '.jpg', '.jpeg')
        image_names = sorted([name for name in archive.namelist() if name.lower().endswith(valid_extensions)])
        
        for name in image_names:
            image_data = archive.read(name)
            image = Image.open(io.BytesIO(image_data))
            pages.append(image)
    return pages

# --- 3. State Management ---
if 'page_index' not in st.session_state:
    st.session_state.page_index = 0
if 'panel_index' not in st.session_state:
    st.session_state.panel_index = -1 # -1 means "Show Full Page"
if 'current_panels' not in st.session_state:
    st.session_state.current_panels = []

# --- 4. Main UI ---
st.title("Comic Reader: Guided View")

uploaded_file = st.file_uploader("Upload a .cbz or .zip comic", type=["cbz", "zip"])

if uploaded_file is not None:
    pages = load_comic_pages(uploaded_file)
    total_pages = len(pages)
    
    if total_pages > 0:
        # Get current page image
        current_image = pages[st.session_state.page_index]
        
        # Run detection if we haven't for this page yet
        if not st.session_state.current_panels:
            st.session_state.current_panels = detect_panels(current_image)

        # --- Navigation Logic ---
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.write(f"Page {st.session_state.page_index + 1} of {total_pages}")
            
            # Button to progress through the reading experience
            if st.button("Next (Space)", use_container_width=True):
                st.session_state.panel_index += 1
                
                # If we've looked at all panels, move to the next page
                if st.session_state.panel_index >= len(st.session_state.current_panels):
                    if st.session_state.page_index < total_pages - 1:
                        st.session_state.page_index += 1
                        st.session_state.panel_index = -1 # Reset to full page view
                        st.session_state.current_panels = [] # Clear old panels
                        st.rerun()
                    else:
                        st.success("End of comic!")
                        st.session_state.panel_index -= 1 # Keep it at the last panel
                else:
                    st.rerun()

        # --- Display Logic ---
        st.divider()
        
        if st.session_state.panel_index == -1:
            # Show Full Page
            st.subheader("Full Page View")
            st.image(current_image, use_container_width=True)
        else:
            # Show Cropped Panel
            current_box = st.session_state.current_panels[st.session_state.panel_index]
            panel_image = current_image.crop(current_box)
            st.subheader(f"Panel {st.session_state.panel_index + 1}")
            st.image(panel_image, use_container_width=True)
            
        # Optional: Reset button to start over
        if st.sidebar.button("Reset Comic"):
            st.session_state.page_index = 0
            st.session_state.panel_index = -1
            st.session_state.current_panels = []
            st.rerun()
			
def sort_panels_reading_order(boxes):
    """
    Sorts YOLOv8 bounding boxes into Left-to-Right, Top-to-Bottom reading order.
    boxes: List of lists/tuples [x1, y1, x2, y2]
    """
    if not boxes:
        return []

    # 1. Add the center Y coordinate to each box for grouping calculations
    # New format: [x1, y1, x2, y2, center_y]
    boxes_with_centers = []
    for box in boxes:
        center_y = (box[1] + box[3]) / 2.0
        boxes_with_centers.append([box[0], box[1], box[2], box[3], center_y])

    # 2. Sort all panels strictly by their top edge (y1) to start
    boxes_with_centers.sort(key=lambda b: b[1])

    rows = []
    current_row = [boxes_with_centers[0]]

    # 3. Group panels into rows based on vertical overlap
    for box in boxes_with_centers[1:]:
        # Find the vertical boundaries of the current row
        row_top = min(b[1] for b in current_row)
        row_bottom = max(b[3] for b in current_row)
        
        box_center_y = box[4]
        
        # If the box's center falls within the vertical space of the current row, 
        # it belongs to this row.
        if row_top <= box_center_y <= row_bottom:
            current_row.append(box)
        else:
            # Otherwise, the current row is finished. Save it and start a new row.
            rows.append(current_row)
            current_row = [box]
            
    # Don't forget to add the final row
    if current_row:
        rows.append(current_row)

    # 4. Sort each row Left-to-Right and format back to original
    sorted_boxes = []
    for row in rows:
        # Sort the row by the left edge (x1)
        row.sort(key=lambda b: b[0])
        
        # Strip out the center_y and append to the final list
        for b in row:
             sorted_boxes.append([b[0], b[1], b[2], b[3]])

    return sorted_boxes