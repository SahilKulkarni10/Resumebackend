# import os
# import re
# import string
# import PyPDF2
# from flask import Flask, jsonify, request, render_template
# from flask_cors import CORS

# app = Flask(__name__)

# CORS(app)

# UPLOAD_FOLDER = './uploads/resume/'
# if not os.path.exists(UPLOAD_FOLDER):
#     os.makedirs(UPLOAD_FOLDER)

# app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# COMMON_SKILLS = [
#     "html", "css", "javascript", "react", "node", "python", "java", "c++",
#     "sql", "mongodb", "ai", "ml", "data analysis", "machine learning", "deep learning", "mern", "docker"
# ]

# SKILL_WEIGHTS = {
#     "html": 1, "css": 1, "javascript": 2, "react": 2, "node": 2, "python": 3, "java": 3,
#     "sql": 2, "mongodb": 2, "ai": 3, "ml": 3, "data analysis": 2, "machine learning": 4,
#     "deep learning": 4, "mern": 2, "docker": 2
# }


# @app.route('/')
# def index():
#     """Render the index HTML page."""
#     return render_template('index.html')


# @app.route('/parseresume', methods=['POST'])
# def uploadResumes():
#     """Handle resume uploads and analyze their content."""

#     if 'file' not in request.files:
#         return jsonify({"error": "No file part"}), 400

#     files = request.files.getlist('file')
#     if len(files) == 0:
#         return jsonify({"error": "No files selected"}), 400

#     def read_pdf(file_path):
#         """Read text content from a PDF file."""
#         with open(file_path, 'rb') as file:
#             reader = PyPDF2.PdfReader(file)
#             text = ''
#             for page in reader.pages:
#                 text += page.extract_text() + ' '
#         return text.strip()

#     def cleanResume(resumeText):
#         """Clean the resume text by removing unwanted characters."""
#         resumeText = re.sub(r'http\S+\s*', ' ', resumeText)
#         resumeText = re.sub(r'RT|cc', ' ', resumeText)
#         resumeText = re.sub(r'#\S+', '', resumeText)
#         resumeText = re.sub(r'@\S+', '  ', resumeText)
#         resumeText = re.sub(r'[%s]' % re.escape(string.punctuation), ' ', resumeText)
#         resumeText = re.sub(r'[^\x00-\x7f]', r' ', resumeText)
#         resumeText = re.sub(r'\s+', ' ', resumeText)
#         return resumeText.lower()

#     def calculate_ats_score(required_skills, resume_text):
#         """Calculate ATS score based on required skills and resume content."""
#         matched_skills = []
#         score = 0
#         total_weight = 0

#         for skill in required_skills:
#             if skill in resume_text:
#                 matched_skills.append(skill)
#                 score += SKILL_WEIGHTS.get(skill, 1)
#             total_weight += SKILL_WEIGHTS.get(skill, 1)

#         ats_score = (score / total_weight) * 100 if total_weight > 0 else 0
#         return round(ats_score, 2), matched_skills


#     required_skills = request.form.get('requiredSkills', '').split(',')
#     required_skills = [skill.strip().lower() for skill in required_skills if skill.strip()]

#     resume_data = []

#     for file in files:
#         filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
#         file.save(filepath)


#         if file.filename.endswith('.pdf'):
#             resume_text = read_pdf(filepath)
#         else:
#             return jsonify({"error": "Unsupported file type. Please upload a PDF file."}), 400

#         cleaned_resume = cleanResume(resume_text)
#         ats_score, matched_skills = calculate_ats_score(required_skills, cleaned_resume)

#         resume_data.append({
#             'filename': file.filename,
#             'ats_score': ats_score,
#             'matched_skills': matched_skills,
#             'resume_text': cleaned_resume
#         })


#     sorted_resumes = sorted(resume_data, key=lambda x: x['ats_score'], reverse=True)[:5]

#     req_skill = request.form.get('skill', '').lower()
#     skill_count = {skill: 0 for skill in COMMON_SKILLS}


#     for resume in sorted_resumes:
#         for skill in COMMON_SKILLS:
#             skill_count[skill] += resume['resume_text'].count(skill.lower())

#     skill_frequency = skill_count.get(req_skill, 0)

#     return jsonify(
#         skill=req_skill,
#         frequency=skill_frequency,
#         skills=skill_count,
#         top_resumes=sorted_resumes
#     )


# if __name__ == '__main__':
#     app.run(debug=True, host='0.0.0.0', port=5000)

import os
import re
import string
import PyPDF2
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS

app = Flask(__name__)

CORS(app)

# Create a folder for resume uploads if it doesn't exist
UPLOAD_FOLDER = './uploads/resume/'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Define common skills and their corresponding weights for ATS score calculation
COMMON_SKILLS = [
    "html", "css", "javascript", "react", "node", "python", "java", "c++",
    "sql", "mongodb", "ai", "ml", "data analysis", "machine learning", "deep learning", "mern", "docker"
]

SKILL_WEIGHTS = {
    "html": 1, "css": 1, "javascript": 2, "react": 2, "node": 2, "python": 3, "java": 3,
    "sql": 2, "mongodb": 2, "ai": 3, "ml": 3, "data analysis": 2, "machine learning": 4,
    "deep learning": 4, "mern": 2, "docker": 2
}


@app.route('/')
def index():
    """Render the index HTML page."""
    return render_template('index.html')


@app.route('/parseresume', methods=['POST'])
def uploadResumes():
    """Handle resume uploads and analyze their content."""

    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    files = request.files.getlist('file')
    if len(files) == 0:
        return jsonify({"error": "No files selected"}), 400

    def read_pdf(file_path):
        """Read text content from a PDF file."""
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ''
            for page in reader.pages:
                text += page.extract_text() + ' '
        return text.strip()

    def cleanResume(resumeText):
        """Clean the resume text by removing unwanted characters."""
        resumeText = re.sub(r'http\S+\s*', ' ', resumeText)
        resumeText = re.sub(r'RT|cc', ' ', resumeText)
        resumeText = re.sub(r'#\S+', '', resumeText)
        resumeText = re.sub(r'@\S+', '  ', resumeText)
        resumeText = re.sub(r'[%s]' % re.escape(string.punctuation), ' ', resumeText)
        resumeText = re.sub(r'[^\x00-\x7f]', r' ', resumeText)
        resumeText = re.sub(r'\s+', ' ', resumeText)
        return resumeText.lower()

    def calculate_ats_score(required_skills, resume_text):
        """Calculate ATS score based on required skills and resume content."""
        matched_skills = []
        score = 0
        total_weight = 0

        for skill in required_skills:
            if skill in resume_text:
                matched_skills.append(skill)
                score += SKILL_WEIGHTS.get(skill, 1)
            total_weight += SKILL_WEIGHTS.get(skill, 1)

        ats_score = (score / total_weight) * 100 if total_weight > 0 else 0
        return round(ats_score, 2), matched_skills

    required_skills = request.form.get('requiredSkills', '').split(',')
    required_skills = [skill.strip().lower() for skill in required_skills if skill.strip()]

    resume_data = []

    for file in files:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)

        if file.filename.endswith('.pdf'):
            resume_text = read_pdf(filepath)
        else:
            return jsonify({"error": "Unsupported file type. Please upload a PDF file."}), 400

        cleaned_resume = cleanResume(resume_text)
        ats_score, matched_skills = calculate_ats_score(required_skills, cleaned_resume)

        resume_data.append({
            'filename': file.filename,
            'ats_score': ats_score,
            'matched_skills': matched_skills,
            'resume_text': cleaned_resume
        })

    sorted_resumes = sorted(resume_data, key=lambda x: x['ats_score'], reverse=True)[:5]

    req_skill = request.form.get('skill', '').lower()
    skill_count = {skill: 0 for skill in COMMON_SKILLS}

    for resume in sorted_resumes:
        for skill in COMMON_SKILLS:
            skill_count[skill] += resume['resume_text'].count(skill.lower())

    skill_frequency = skill_count.get(req_skill, 0)

    return jsonify(
        skill=req_skill,
        frequency=skill_frequency,
        skills=skill_count,
        top_resumes=sorted_resumes
    )


if __name__ == '__main__':
    # Run the app with dynamic port binding (for both local and production environments)
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5001)))
