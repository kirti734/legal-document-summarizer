Set-ExecutionPolicy RemoteSigned

.\venv\Scripts\Activate.ps1

pip install



import pytesseract
from PIL import Image
import PyPDF2
import io
import logging
import os
import spacy
import re
import logging
from collections import defaultdict
import os
import logging
from flask import Flask, render_template, request, jsonify, flash
from werkzeug.utils import secure_filename
from werkzeug.middleware.proxy_fix import ProxyFix
import uuid

python app.py