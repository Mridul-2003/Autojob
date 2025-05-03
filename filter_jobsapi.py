from flask import Flask,request,jsonify
from filter_jobs import FilterData
from dotenv import load_dotenv
import os
app = Flask(__name__)
load_dotenv()
CONNECTION_STRING = os.get_env("CONNECTION_STRING")
TABLE_NAME = os.get_env("TABLE_NAME")
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
@app.route("/filter_jobs",methods=['POST'])
def filter_jobs():
    search_keyword = request.form.get('search_keyword')
    resume_file = request.files.get('resume')

    if not search_keyword or not resume_file:
        return jsonify({"error": "Missing search_keyword or resume file"}), 400

    # Save resume to a temporary path
    resume_path = os.path.join(UPLOAD_FOLDER, resume_file.filename)
    resume_file.save(resume_path)

    filter_data = FilterData(CONNECTION_STRING,TABLE_NAME)
    job_data = filter_data.fetch_job_data(top_n=5)
    if job_data:
        filtered_jobs = filter_data.filter_jobs(job_data, search_keyword,resume_path)
        return jsonify({"filterd_jobs":filtered_jobs})
    else:
        return jsonify({"msg":"No filtered jobs found"})