import os
import sys
import uuid
import json
import tempfile
import time
from flask import Flask, request, jsonify
from flask_cors import CORS

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config
from parsers.document_parser import extract_text, extract_text_from_content, clean_extracted_text
from agents.orchestrator import AgentOrchestrator

app = Flask(__name__)
allowed_origins = list(dict.fromkeys([
    *config.CORS_ORIGINS,
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
]))
CORS(app, origins=allowed_origins)
app.config["MAX_CONTENT_LENGTH"] = config.MAX_UPLOAD_SIZE

# in-memory document store (replace with postgres in production)
document_store = {}

# initialize orchestrator once at startup
orchestrator = AgentOrchestrator()
