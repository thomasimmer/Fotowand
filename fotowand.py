import argparse
import os
import time
import pygame
import pygame.freetype  
import random
import subprocess
import sys
from datetime import datetime
from threading import Thread
from PIL import Image, ExifTags
import requests
import traceback
import secrets


current_img_surface = None
current_x_offset = None
current_y_offset = None

def parse_arguments():
    parser = argparse.ArgumentParser(description="Media slideshow with optional parameters.")
    
    parser.add_argument("folder", type=str, help="Path to the folder containing media files.")
    parser.add_argument("API_KEY", type=str, help="API key for the OpenCage Geocoder.")
    parser.add_argument("--Display_Time", type=int, default=30, help="Time between pictures(default: 30).")
    parser.add_argument("--GL_fontsize", type=int, default=21, help="Font size for text display (default: 21).")
    parser.add_argument("--GL_fadetime", type=float, default=0.4, help="Fade time in seconds for transitions (default: 0.4).")
    parser.add_argument("--GL_anz_2_year", type=int, default=250, help="Number of files to select from the last 2 years (default: 250).")
    parser.add_argument("--GL_anz_5_year", type=int, default=250, help="Number of files to select from the last 5 years (default: same as GL_anz_2_year).")
    parser.add_argument("--GL_anz_all", type=int, default=500, help="Number of files to select from all files (default: 2 * GL_anz_2_year).")
    parser.add_argument("--Displ_Time_Size", type=int, default=30, help="Show time size in Pixels (0=No Time)")
    
    return parser.parse_args()

def get_year_from_path(filepath):
    """Extracts the year from the directory path."""
    try:
        parts = filepath.split(os.sep)
        for part in parts:
            if part.isdigit() and len(part) == 4:  # Check for a 4-digit year
                return int(part)
    except Exception as e:
        print(f"Error extracting year from path '{filepath}': {e}")
        traceback.print_exc()
    return None

def get_image_metadata(filepath):
    """Extracts EXIF metadata from an image."""
    try:
        img = Image.open(filepath)
        exif = img._getexif()
        if not exif:
            return None, None
        
        date = exif.get(36867)  # EXIF DateTimeOriginal
        if date:
            try:
                date_obj = time.strptime(date, '%Y:%m:%d %H:%M:%S')
                formatted_date = time.strftime('%d.%m.%Y', date_obj)
            except ValueError:
                formatted_date = ""
        else:
            formatted_date = ""

        gps_info = exif.get(34853)  # EXIF GPSInfo
        

        if gps_info:
            gps_lat = gps_info.get(2)  # GPS Latitude
            gps_lat_ref = gps_info.get(1)  # GPS Latitude Ref (N/S)
            gps_lon = gps_info.get(4)  # GPS Longitude
            gps_lon_ref = gps_info.get(3)  # GPS Longitude Ref (E/W)
            print(f"gps_lat: '{gps_lat}' '{gps_lat_ref}' gps_lon: '{gps_lon}' '{gps_lon_ref}' ")
        
            if gps_lat and gps_lon:
                lat = convert_to_degrees(gps_lat)
                lon = convert_to_degrees(gps_lon)
                if gps_lat_ref != 'N': lat = -lat
                if gps_lon_ref != 'E': lon = -lon
                location = get_location_name(lat, lon)
                print(f"Location: '{location}' ")
                return formatted_date, location
        return formatted_date, None
    except Exception as e:
        print(f"Error extracting metadata from image '{filepath}': {e}")
        traceback.print_exc()
    return None, None

def convert_to_degrees(value):
    """
    Helper function to convert the GPS coordinates stored in the EXIF to degrees in float format.

    Args:
        value (tuple): The GPS coordinate as a tuple (degrees, minutes, seconds)

    Returns:
        float: The coordinate in degrees
    """
    d = float(value[0])
    m = float(value[1])
    s = float(value[2])
    return d + (m / 60.0) + (s / 3600.0)

def get_location_name(lat, lon):
    """Gets the nearest larger location name using the OpenCage Geocoder API."""
    try:
        url = f"https://api.opencagedata.com/geocode/v1/json?q={lat}+{lon}&key={API_KEY}"
        response = requests.get(url, timeout=5)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx and 5xx)
        data = response.json()
        if data['results']:
            return data['results'][0]['formatted']
        return "Unknown Location"
    except requests.ConnectionError:
        print(f"Network error: Unable to connect to OpenCage API for coordinates ({lat}, {lon}).")
    except requests.Timeout:
        print(f"Timeout error: OpenCage API request timed out for coordinates ({lat}, {lon}).")
    except requests.RequestException as e:
        print(f"HTTP error while fetching location name: {e}")
    except Exception as e:
        print(f"Unexpected error fetching location name for coordinates ({lat}, {lon}): {e}")
        traceback.print_exc()
    return "Unknown Location"

def draw_text(screen, text1, text):
    """Draws text on the screen."""
    print(f"Draw Text: '{text}' ")

    #font = pygame.freetype.Font(pygame.freetype.get_default_font(), 30)
    font = pygame.freetype.Font(None, GL_fontsize)
    text_surface = font.render_to(screen, (0,screen.get_height()-((2*GL_fontsize)+2)), text, (255,255,255),(0,0,0))
    text_surface = font.render_to(screen, (0,screen.get_height()-(GL_fontsize+1)), text1, (255,255,255),(0,0,0))
    if Displ_Time_Size > 0:
        font1 = pygame.freetype.Font(None, Displ_Time_Size)
        text_surface = font1.render_to(screen, ((screen.get_width()-5-(5*Displ_Time_Size)),10+Displ_Time_Size),time.strftime("%H:%M"), (255,255,255),(0,0,0))
    pygame.display.update() 


def display_image(filepath, screen, fade_duration=1,text="", filepath1=""):
    """Displays an image with correct orientation and aspect ratio."""

    global current_img_surface  # Use the global variable to track the current image
    global current_x_offset
    global current_y_offset

    try:
        pygame.mouse.set_visible(False)  # Hide the mouse cursor
        img = Image.open(filepath)
        
        # Correct orientation using EXIF data
        for orientation in ExifTags.TAGS.keys():
            if ExifTags.TAGS[orientation] == 'Orientation':
                break
        exif = img._getexif()
        if exif and orientation in exif:
            if exif[orientation] == 3:
                img = img.rotate(180, expand=True)
            elif exif[orientation] == 6:
                img = img.rotate(270, expand=True)
            elif exif[orientation] == 8:
                img = img.rotate(90, expand=True)
        
        # Scale to fit screen while maintaining aspect ratio
        screen_width, screen_height = screen.get_size()
        img_ratio = img.width / img.height
        screen_ratio = screen_width / screen_height

        if img_ratio > screen_ratio:  # Wider image
            new_width = screen_width
            new_height = int(screen_width / img_ratio)
        else:  # Taller image
            new_height = screen_height
            new_width = int(screen_height * img_ratio)

        img = img.resize((new_width, new_height), Image.ANTIALIAS)
        img_surface = pygame.image.fromstring(img.tobytes(), img.size, img.mode)

        # Center image on screen
        x_offset = (screen_width - new_width) // 2
        y_offset = (screen_height - new_height) // 2
      
        # Fade effect using an overlay surface
        fade_steps = int(25*fade_duration)
        overlay = pygame.Surface((screen_width, screen_height))
        overlay.fill((0, 0, 0))

        if current_img_surface:  # Only fade out if there's a current image
            for alpha in range(0, 256, 256 // fade_steps):
                screen.fill((0, 0, 0))  # Clear screen
                current_img_surface.set_alpha(255 - alpha)  # Decrease current image opacity
                screen.blit(current_img_surface, (current_x_offset, current_y_offset))  # Draw current image
                pygame.display.flip()
                time.sleep(fade_duration / fade_steps)


        for alpha in range(0, 256, 256 // fade_steps):
            screen.fill((0, 0, 0))  # Clear screen
            screen.blit(img_surface, (x_offset, y_offset))  # Draw image
            overlay.set_alpha(255 - alpha)  # Reduce overlay opacity
            screen.blit(overlay, (0, 0))  # Apply overlay
            pygame.display.flip()
            time.sleep(fade_duration / fade_steps)

        current_img_surface = img_surface.copy()
        current_x_offset = x_offset
        current_y_offset = y_offset
        
        draw_text(screen, text, filepath1)

        pygame.display.flip()


    except Exception as e:
        print(f"Error displaying image '{filepath}': {e}")
        traceback.print_exc()


def collect_and_filter_files(folder):
    """Collects files from directories and categorizes them by year."""
    current_year = datetime.now().year
    last_five_years = range(current_year - 4, current_year + 1)
    all_files = []
    recent_two_years_files = []
    last_five_years_files = []
    print(folder)
    try:
        for root, _, filenames in os.walk(folder):
            for filename in filenames:
                if filename.lower().endswith(('.png', '.jpg', '.jpeg')): #, '.mp4', '.mov' extension für Video File possible
                    filepath = os.path.join(root, filename)
                    year = get_year_from_path(filepath)
                    all_files.append(filepath)
                    if year in {current_year, current_year - 1}:
                        recent_two_years_files.append(filepath)
                    elif year in last_five_years:
                        last_five_years_files.append(filepath)
    except Exception as e:
        print(f"Error collecting or filtering files in folder '{folder}': {e}")
        traceback.print_exc()

    return all_files, recent_two_years_files, last_five_years_files


def secure_sample(file_list, sample_size):
    """Sicheres, zufälliges Sampling ohne Wiederholung."""
    if len(file_list) <= sample_size:
        return file_list.copy()
    return [file_list[i] for i in secrets.SystemRandom().sample(range(len(file_list)), sample_size)]

def select_files(all_files, recent_two_years_files, last_five_years_files, GL_anz_2_year, GL_anz_5_year, GL_anz_all):
    """Dateien mit echtem Zufall sicher auswählen."""
    try:
        # Zufällige Auswahl der Dateien mit kryptographisch sicherem Zufall
        recent_two_years_selected = secure_sample(recent_two_years_files, GL_anz_2_year) if recent_two_years_files else []
        last_five_years_selected = secure_sample(last_five_years_files, GL_anz_5_year) if last_five_years_files else []
        all_selected = secure_sample(all_files, GL_anz_all) if all_files else []

        # Ergebnisse zusammenführen und erneut mischen
        combined_selection = list(set(recent_two_years_selected + last_five_years_selected + all_selected))
        secrets.SystemRandom().shuffle(combined_selection)

        return combined_selection

    except Exception as e:
        print("Fehler bei der Dateiauswahl:")
        traceback.print_exc()
        return []


def play_media(folder, display_time):
    try:
        pygame.init()
        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        pygame.font.init() 
        
        index = 0

        while True:
            if index == 0:
                all_files, recent_two_years_files, last_five_years_files = collect_and_filter_files(folder)
                # Select files based on rules
                selected_files = select_files(all_files, recent_two_years_files, last_five_years_files,GL_anz_2_year, GL_anz_5_year, GL_anz_all)

            filepath = selected_files[index]
            filepath1 = filepath
            filepath1 = filepath1.replace(folder, "")
            print(f"File '{index}' to show: '{filepath1}'")
            
            if filepath.lower().endswith(('.png', '.jpg', '.jpeg')):
                # Display image with metadata
                date, location = get_image_metadata(filepath)
                screen.fill((0, 0, 0))
                text = f""
                if date and location:
                     text = f"{date} | Ort: {location}"
                elif date:
                    text = f"{date}"
                elif location:
                    text = f"Ort: {location}"

                display_image(filepath, screen,GL_fadetime, text, filepath1)
                #draw_text(screen, text, filepath1)


            """ Extension for Videofile possible
            elif filepath.lower().endswith(('.mp4', '.mov')):
                # Play video
                process = subprocess.Popen(['omxplayer', '--no-keys', '--loop', filepath])
                time.sleep(display_time)
                process.terminate()
            """

            # Wait for input or move to the next file
            start_time = time.time()
            while time.time() - start_time < display_time:
                for event in pygame.event.get():
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_RIGHT:  # Next item
                            index = (index + 1) % len(selected_files)
                            start_time = time.time()
                            break
                        elif event.key == pygame.K_LEFT:  # Previous item
                            index = (index - 1) % len(selected_files)
                            start_time = time.time()
                            break
                        elif event.key == pygame.K_ESCAPE:  # Exit program
                            pygame.quit()
                            return
                    elif event.type == pygame.QUIT:
                        pygame.quit()
                        return
        
            # Automatically move to the next file after the display time
            index = (index + 1) % len(selected_files)
            
    except Exception as e:
        print(f"Unexpected error: {e}")
        traceback.print_exc()
    finally:
        pygame.quit()

if __name__ == "__main__":
    args = parse_arguments()

    folder = args.folder
    API_KEY = args.API_KEY
    Display_Time = args.Display_Time
    GL_fontsize = args.GL_fontsize
    GL_fadetime = args.GL_fadetime
    GL_anz_2_year = args.GL_anz_2_year
    GL_anz_5_year = args.GL_anz_5_year
    GL_anz_all = args.GL_anz_all
    Displ_Time_Size = args.Displ_Time_Size


    if not os.path.isdir(folder):
        print(f"Error: The specified path '{folder}' is not a directory.")
        sys.exit(1)

    try:
        print(f"Folder: {folder}")
        print(f"Display_Time: {Display_Time}")
        print(f"API_KEY: {API_KEY}")
        print(f"Font Size: {GL_fontsize}")
        print(f"Fade Time: {GL_fadetime}")
        print(f"Files (2 Years): {GL_anz_2_year}")
        print(f"Files (5 Years): {GL_anz_5_year}")
        print(f"Files (All): {GL_anz_all}")
        print(f"Display Time Size: {Displ_Time_Size}")

        # Call play_media or equivalent with these parameters
        play_media(folder, Display_Time)
        pygame.mouse.set_visible(True)  # Hide the mouse cursor

    except KeyboardInterrupt:
        print("\nProgram terminated by user.")
        pygame.mouse.set_visible(True)  # Hide the mouse cursor
