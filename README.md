# Media Slideshow Application

## Overview
This Python-based application displays a media slideshow of images and videos from a specified folder. It includes features such as metadata extraction, GPS-based location resolution, and smooth fade transitions between slides.

---

## Features
- **Dynamic File Selection**: Select files based on age (recent 2 years, last 5 years, or all).
- **EXIF Metadata Extraction**: Display the creation date and GPS-based location of images.
- **Smooth Transitions**: Fade in and fade out effects for slides.
- **Keyboard Navigation**: Use arrow keys to navigate slides and ESC to exit.
- **Customizable Parameters**: Set font size, fade duration, and file selection rules.

---

## Requirements

### Python Packages
- `pygame`
- `Pillow`
- `requests`

### System Requirements
- Python 3.6 or later
- Internet connection (for location resolution using OpenCage Geocoder API)

---

## Usage

### Command-line Arguments
The program accepts the following arguments:

#### **Required Arguments**
- `folder`: Path to the folder containing media files.
- `API_KEY`: API key for the OpenCage Geocoder.

#### **Optional Arguments**
- `--Display_Time`: Time (in seconds) to display each slide (default: 30).
- `--GL_fontsize`: Font size for text overlay (default: 21).
- `--GL_fadetime`: Duration (in seconds) for fade transitions (default: 0.4).
- `--GL_anz_2_year`: Number of files to select from the last 2 years (default: 250).
- `--GL_anz_5_year`: Number of files to select from the last 5 years (default: 250).
- `--GL_anz_all`: Number of files to select from all files (default: 500).

### Example
```bash
python media_slideshow.py "/path/to/media" "your_api_key" --Display_Time 20 --GL_fadetime 0.5
```

---

## Code Structure

### **1. Argument Parsing**
The `parse_arguments` function handles all command-line arguments, ensuring mandatory parameters are provided and optional parameters use sensible defaults.

### **2. File Handling**
- `collect_and_filter_files`: Collects media files and categorizes them by year.
- `select_files`: Selects files based on the defined rules.

### **3. EXIF and Metadata Handling**
- `get_image_metadata`: Extracts metadata (creation date, GPS coordinates) from images.
- `get_location_name`: Resolves GPS coordinates into human-readable locations using the OpenCage Geocoder API.

### **4. Display Logic**
- `display_image`: Handles image scaling, metadata overlay, and fade transitions.
- `draw_text`: Renders metadata text on the screen.

### **5. Main Slideshow Logic**
- `play_media`: Manages the slideshow, including navigation, file selection, and media playback.

---

## Error Handling
- **File Handling**: Warnings are displayed if no files are found for recent years or if invalid paths are provided.
- **Network Errors**: Graceful handling of connection errors and timeouts during API requests.
- **Keyboard Interrupt**: Ensures the program exits cleanly when interrupted.

---

## Improvements and Customization
- **Dynamic Rules**: Update the selection logic to include more flexible criteria.
- **Additional Transitions**: Add support for slide effects such as crossfade or zoom.
- **Localization**: Translate metadata text into multiple languages.

---

## Troubleshooting

### Common Issues
1. **`requests.exceptions.ConnectionError`**:
   - Check your internet connection.
   - Ensure the OpenCage Geocoder API key is valid.

2. **Invalid File Paths**:
   - Verify the folder path provided.

### Debugging
Run the script with `print` statements or log outputs enabled to trace issues.

---

