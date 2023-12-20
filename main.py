import json
import os
from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename
import secrets
import uuid

app = Flask(__name__)

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
POSTS_FOLDER = os.path.join(os.getcwd(), 'posts')
ALLOWED_EXTENSIONS = {'mp4', 'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['POSTS_FOLDER'] = POSTS_FOLDER


def allowed_file(filename):
  return '.' in filename and filename.rsplit(
      '.', 1)[1].lower() in ALLOWED_EXTENSIONS


def generate_random_filename():
  return secrets.token_hex(16)


def generate_unique_id():
  return str(uuid.uuid4())


def save_post_data_to_json(post_data):
  unique_id = generate_unique_id()

  # Generate unique filenames based on the unique ID
  video_filename = f'{unique_id}.mp4'
  thumbnail_filename = f'{unique_id}.png'

  video_file_path = os.path.join(app.config['UPLOAD_FOLDER'], video_filename)
  thumbnail_file_path = os.path.join(app.config['UPLOAD_FOLDER'],
                                     thumbnail_filename)

  post_data['video'].save(video_file_path)
  post_data['thumbnail'].save(thumbnail_file_path)

  post_data['video_filename'] = video_filename
  post_data['thumbnail_filename'] = thumbnail_filename
  post_data['id'] = unique_id

  post_file_path = os.path.join(app.config['POSTS_FOLDER'],
                                f'{unique_id}.json')
  with open(post_file_path, 'w') as file:
    # Serialize only the necessary information
    serialized_data = {
        'title': post_data['title'],
        'video_filename': video_filename,
        'thumbnail_filename': thumbnail_filename,
        'id': unique_id
    }
    json.dump(serialized_data, file, indent=2)

  json_file_path = os.path.join(app.config['POSTS_FOLDER'], 'datajson',
                                'post.json')
  posts_data = []

  if os.path.exists(json_file_path):
    with open(json_file_path, 'r') as file:
      try:
        posts_data = json.load(file)
      except json.decoder.JSONDecodeError:
        pass

  posts_data.append(serialized_data)

  with open(json_file_path, 'w') as file:
    json.dump(posts_data, file, indent=2)


@app.route('/upload', methods=['POST'])
def upload_file():
  if 'video' not in request.files or 'thumbnail' not in request.files:
    return redirect(request.url)

  video_file = request.files['video']
  thumbnail_file = request.files['thumbnail']

  if video_file.filename == '' or thumbnail_file.filename == '':
    return redirect(request.url)

  if video_file and allowed_file(
      video_file.filename) and thumbnail_file and allowed_file(
          thumbnail_file.filename):
    post_data = {
        'title': request.form.get('title'),
        'video': video_file,
        'thumbnail': thumbnail_file
    }

    save_post_data_to_json(post_data)

    return 'Success! The files have been uploaded and saved.'
  else:
    return 'Invalid file types. Allowed file types are: mp4, png, jpg, jpeg, gif.'


@app.route('/')
def index():
  # Get a list of all video files in the UPLOAD_FOLDER
  video_files = [
      f for f in os.listdir(app.config['UPLOAD_FOLDER']) if f.endswith('.mp4')
  ]

  # Render the index.html template and pass the list of video files
  return render_template('index.html', video_files=video_files)


@app.route('/uploads/<filename>')
def uploaded_file_upload(filename):
  return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/posts/datajson/<filename>')
def uploaded_file_posts(filename):
  return send_from_directory(app.config['POSTS_FOLDER'],
                             f'datajson/{filename}')


if __name__ == '__main__':
  os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
  os.makedirs(app.config['POSTS_FOLDER'], exist_ok=True)
  app.run(host='0.0.0.0', port=81, debug=True)
