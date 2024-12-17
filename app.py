from flask import Flask, render_template, request, redirect, url_for, send_file
import yt_dlp
import os

app = Flask(__name__)

# Define the directory for downloads (optional, only used for local file storage if needed)
app.config['DOWNLOAD_FOLDER'] = 'downloads'
if not os.path.exists(app.config['DOWNLOAD_FOLDER']):
    os.makedirs(app.config['DOWNLOAD_FOLDER'])

def get_video_formats(url):
    """Extract available video formats and map resolutions to qualities like 144p, 360p."""
    formats = []
    try:
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            for fmt in info_dict.get('formats', []):
                if fmt.get('vcodec') != 'none':
                    resolution = fmt.get('height')  # Extract height to determine quality
                    quality = f"{resolution}p" if resolution else "Unknown Quality"
                    formats.append({
                        'format_id': fmt['format_id'],
                        'quality': quality,
                        'ext': fmt['ext']
                    })
    except Exception as e:
        print(f"Error: {e}")
    return formats

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = request.form['url']
        return redirect(url_for('analyze_video', url=url))
    return render_template('index.html')

@app.route('/analyze_video', methods=['GET'])
def analyze_video():
    url = request.args.get('url')
    formats = get_video_formats(url)
    return render_template('analyze_video.html', formats=formats, url=url)

@app.route('/download_video', methods=['POST'])
def download_video():
    url = request.form['url']
    format_id = request.form['format_id']

    # Prepare the download without blocking the page
    ydl_opts = {
        'format': format_id,
        'outtmpl': os.path.join(app.config['DOWNLOAD_FOLDER'], '%(title)s_%(height)s.%(ext)s'),
        'quiet': True,  # Don't show unnecessary output in the console
    }

    # Start the download in the background (without blocking)
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info_dict)

    # Trigger the download and stop the page from loading further
    return redirect(url_for('trigger_download', filename=filename))

@app.route('/trigger_download', methods=['GET'])
def trigger_download():
    filename = request.args.get('filename')
    
    # Serve the file as an attachment, triggering a direct download
    return send_file(filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
