import os
import re
import string
import PyPDF2
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import google.generativeai as genai
import logging

app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CORS(app)

# Gemini API configuration
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')  # Set your API key in environment variables
if not GEMINI_API_KEY:
    logger.warning("GEMINI_API_KEY environment variable is not set. AI feedback will not work.")
genai.configure(api_key=GEMINI_API_KEY)

# Available Gemini models
AVAILABLE_MODELS = [
    "gemini-2.0-flash-exp",  # First choice - free experimental model
    "gemini-1.5-flash",
    "gemini-1.0-pro",    
    "gemini-pro"        
]

UPLOAD_FOLDER = './uploads/resume/'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


COMMON_SKILLS = [
    "html", "css", "javascript", "react", "node", "python", "java", "c++",
    "sql", "mongodb", "ai", "ml", "data analysis", "machine learning", "deep learning", "mern", "docker"
]

SKILL_WEIGHTS = {
    "html": 1, "css": 1, "javascript": 2, "react": 2, "node": 2, "python": 3, "java": 3,
    "sql": 2, "mongodb": 2, "ai": 3, "ml": 3, "data analysis": 2, "machine learning": 4,
    "deep learning": 4, "mern": 2, "docker": 2
}

# Helper functions moved outside to be accessible by multiple routes
def read_pdf(file_path):
    """Read text content from a PDF file."""
    try:
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ''
            for page in reader.pages:
                text += page.extract_text() + ' '
        return text.strip()
    except Exception as e:
        logger.error(f"Error reading PDF {file_path}: {str(e)}")
        return ""

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
        # Use regex with word boundaries to match whole words
        if re.search(r'\b' + re.escape(skill) + r'\b', resume_text):
            matched_skills.append(skill)
            score += SKILL_WEIGHTS.get(skill, 1)
        total_weight += SKILL_WEIGHTS.get(skill, 1)

    # Ensure we show a score even if only one skill matches
    if total_weight > 0:
        ats_score = (score / total_weight) * 100
    else:
        ats_score = 0
        
    return round(ats_score, 2), matched_skills


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

    # Sort resumes by matched skills first (prioritize those with matches), then by ATS score
    sorted_resumes = sorted(resume_data, key=lambda x: (len(x['matched_skills']) > 0, x['ats_score']), reverse=True)[:5]

    skill_count = {skill: 0 for skill in COMMON_SKILLS}

    for resume in sorted_resumes:
        for skill in COMMON_SKILLS:
            # Count whole word occurrences using regex
            skill_count[skill] += len(re.findall(r'\b' + re.escape(skill) + r'\b', resume['resume_text']))

    # Get the primary skill from the request or use the first required skill
    req_skill = request.form.get('skill', '').lower()
    if not req_skill and required_skills:
        req_skill = required_skills[0]
        
    skill_frequency = skill_count.get(req_skill, 0)

    return jsonify(
        skill=req_skill,
        frequency=skill_frequency,
        skills=skill_count,
        top_resumes=sorted_resumes
    )


@app.route('/resumefeedback', methods=['POST'])
def get_resume_feedback():
    """Generate AI feedback for resume improvement."""
    try:
        logger.info("Resume feedback request received")
        
        if 'file' not in request.files:
            logger.warning("No file part in request")
            return jsonify({"error": "No file part"}), 400
        
        files = request.files.getlist('file')
        if len(files) == 0:
            logger.warning("No files selected")
            return jsonify({"error": "No files selected"}), 400
        
        required_skills = request.form.get('requiredSkills', '').split(',')
        required_skills = [skill.strip().lower() for skill in required_skills if skill.strip()]
        logger.info(f"Required skills: {required_skills}")
        
        feedback_results = {}
        
        for file in files:
            logger.info(f"Processing file: {file.filename}")
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filepath)
            
            if file.filename.endswith('.pdf'):
                resume_text = read_pdf(filepath)
                if not resume_text:
                    feedback_results[file.filename] = "Could not extract text from PDF file."
                    continue
                
                # Generate feedback using Gemini AI
                feedback = generate_resume_feedback(resume_text, required_skills)
                feedback_results[file.filename] = feedback
                logger.info(f"Generated feedback for {file.filename}")
            else:
                feedback_results[file.filename] = "Unsupported file type. Please upload a PDF file."
                logger.warning(f"Unsupported file type for {file.filename}")
        
        return jsonify(feedback_results)
    except Exception as e:
        logger.error(f"Error in get_resume_feedback: {str(e)}")
        return jsonify({"error": str(e)}), 500

def generate_resume_feedback(resume_text, required_skills):
    """Use Gemini AI to generate feedback for resume improvement."""
    try:
        # Check if API key is configured
        if not GEMINI_API_KEY:
            logger.warning("API key not configured for Gemini")
            return "AI feedback unavailable. API key not configured. Please get a free API key from https://aistudio.google.com/app/apikey"
        
        # Format the prompt for Gemini
        skills_text = ", ".join(required_skills) if required_skills else "relevant industry skills"
        prompt = f"""
        As an ATS (Applicant Tracking System) expert, review the following resume:

        {resume_text}

        Consider these required skills: {skills_text}

        Provide specific, actionable feedback to improve this resume's ATS score. Focus on:
        1. Keyword optimization for required skills
        2. Resume structure and formatting issues
        3. Content gaps or improvements
        4. Specific suggestions to increase ATS compatibility
        
        FORMAT YOUR RESPONSE EXACTLY AS FOLLOWS:
        • First suggestion with specific examples and clear action items
        • Second suggestion focused on a different aspect of the resume
        • Third suggestion specifically about keywords and skills placement
        • Fourth suggestion about resume structure or formatting
        • Fifth suggestion about quantifiable achievements
        • Final suggestion with a high-impact improvement
        
        Each bullet point should be concise but specific, offering clear guidance. Start every line with the bullet point "•" character.
        """
        
        # Loop through available models
        for model_name in AVAILABLE_MODELS:
            try:
                logger.info(f"Trying model: {model_name}")
                
                # Initialize the model (with minimal settings to avoid errors)
                model = genai.GenerativeModel(model_name=model_name)
                
                # Generate content with simpler configuration
                logger.info(f"Generating content with {model_name}")
                
                response = model.generate_content(prompt)
                
                # If we get here, the model worked
                if response and hasattr(response, 'text'):
                    logger.info(f"Successfully generated feedback with {model_name}")
                    # Process the response to ensure consistent formatting
                    return format_ai_feedback(response.text)
                
            except Exception as e:
                error_message = str(e)
                logger.error(f"Error with model {model_name}: {error_message}")
                
                # Check for specific error types
                if "API_KEY_INVALID" in error_message:
                    return "• Your API key is invalid or missing. Please get a free API key from https://aistudio.google.com/app/apikey\n• Follow the instructions in the run_server.sh file\n• Update the script with your API key and run it again"
                
                # Continue to the next model if current one fails
                continue
        
        # If all models failed
        return "• AI feedback unavailable. Could not connect to AI models.\n• Get a free Gemini API key from https://aistudio.google.com/app/apikey\n• Make sure you have the correct API key format\n• Key should look like: AIzaSyC_1a...k4Rc"
        
    except Exception as e:
        logger.error(f"Error generating AI feedback: {str(e)}")
        return "• AI feedback temporarily unavailable\n• Please try again later\n• In the meantime, ensure your resume has clear section headings\n• Include the required skills prominently\n• Use bullet points for achievements\n• Quantify your results where possible"

def format_ai_feedback(text):
    """Ensure consistent formatting for AI feedback."""
    # Split into lines and process
    lines = text.strip().split('\n')
    formatted_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Skip lines that are just headers or numbers
        if line.isdigit() or line.lower().startswith(('feedback', 'suggestions', 'recommendations')):
            continue
            
        # Ensure each line starts with a bullet point
        if not line.startswith('•'):
            # Check if line starts with a different bullet format or number
            if line.startswith('-') or line.startswith('*') or (line[0].isdigit() and line[1:3] in ['. ', ') ']):
                line = '• ' + line[line.find(' ')+1:]
            else:
                line = '• ' + line
                
        formatted_lines.append(line)
    
    # If no valid lines, provide default feedback
    if not formatted_lines:
        return "• Ensure your resume includes the required skills explicitly\n• Use industry-standard section headings for better ATS parsing\n• Quantify achievements with numbers and percentages\n• Remove tables, images, and complex formatting\n• Match keywords from the job description exactly\n• Use both acronyms and full terms (e.g., 'AI' and 'Artificial Intelligence')"
    
    return '\n'.join(formatted_lines)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5001)))
