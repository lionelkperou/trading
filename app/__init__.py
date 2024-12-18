from flask import Flask
from config import Config
import os

app = Flask(__name__)
app.config.from_object(Config)

# Assurez-vous que le dossier d'upload existe
upload_folder = os.path.join(app.root_path, '..', 'uploads')
if not os.path.exists(upload_folder):
    os.makedirs(upload_folder)

app.config['UPLOAD_FOLDER'] = upload_folder

from app import routes