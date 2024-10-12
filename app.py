from flask import Flask, request, jsonify, send_from_directory, render_template
import subprocess
import threading
import re
import os

app = Flask(__name__)

# Store progress globally
progress = 0
output_dir = "C:/Users/benz9/Downloads"

# Regex pattern for matching progress in yt-dlp output
progress_regex = re.compile(r"\[download\]\s+([\d.]+)%")

def parse_progress(line):
    """
    Parse the progress percentage from yt-dlp's output line.
    """
    match = progress_regex.search(line)
    if match:
        return float(match.group(1))
    return None

def download_video(url):
    global progress

    # yt-dlp command for downloading the video
    command = ['yt-dlp', '--newline', '-o', f'{output_dir}/%(title)s.%(ext)s', url]
    
    # Run the command and capture stdout in real-time
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

    filename = None  # Initialize filename
    
    for line in process.stdout:
        print(line.strip())

        # Parse and update the progress
        parsed_progress = parse_progress(line)
        if parsed_progress is not None:
            progress = parsed_progress
            print(f"Progress updated: {progress}%")

        # Capture the filename when it's downloaded
        if "Destination:" in line:
            full_path = line.split("Destination: ")[1].strip()  # Extract the full file path
            filename = os.path.basename(full_path)  # Get just the filename

    process.wait()

    if process.returncode == 0:
        print("Download completed successfully.")
    else:
        print(f"Download failed with return code {process.returncode}.")

    return filename  # Return the downloaded filename

@app.route('/')
def index():
    """
    Serve the index.html file.
    """
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def start_download():
    """
    Start a new download in a separate thread.
    """
    global progress
    progress = 0  # Reset progress

    data = request.json
    url = data.get('url')

    if not url:
        return jsonify({"error": "No URL provided"}), 400

    # Start the download and get the filename
    filename = download_video(url)

    return jsonify({"status": "Download started", "filePath": filename}), 200

@app.route('/progress', methods=['GET'])
def get_progress():
    """
    Get the current download progress.
    """
    return jsonify({"progress": progress}), 200

@app.route('/downloads/<filename>')
def download_file(filename):
    """
    Serve the downloaded file to the client (allow them to download to their local machine).
    """
    return send_from_directory(output_dir, filename)

if __name__ == '__main__':
    # Ensure the output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    app.run(debug=True, threaded=True)
