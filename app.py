from flask import Flask, request, jsonify
from flask_cors import CORS
import PyPDF2
import io
import re

app = Flask(__name__)
CORS(app)  # Allows frontend to talk to backend

# -----------------------------------------------
# HOME ROUTE - just to test if server is running
# -----------------------------------------------
@app.route('/')
def home():
    return jsonify({"message": "AI Resume Screener API is running!"})


# -----------------------------------------------
# MAIN ROUTE - analyze the resume
# -----------------------------------------------
@app.route('/analyze', methods=['POST'])
def analyze():
    # Get the uploaded file and job description
    if 'resume' not in request.files:
        return jsonify({"error": "No resume file uploaded"}), 400

    file = request.files['resume']
    job_description = request.form.get('job_description', '')

    if not job_description:
        return jsonify({"error": "No job description provided"}), 400

    # Extract text from the resume
    resume_text = extract_text(file)

    if not resume_text:
        return jsonify({"error": "Could not read resume. Use a TXT or PDF file."}), 400

    # Score the resume
    result = score_resume(resume_text, job_description)

    return jsonify(result)


# -----------------------------------------------
# FUNCTION - Extract text from PDF or TXT file
# -----------------------------------------------
def extract_text(file):
    filename = file.filename.lower()
    text = ""

    try:
        if filename.endswith('.pdf'):
            # Read PDF
            reader = PyPDF2.PdfReader(io.BytesIO(file.read()))
            for page in reader.pages:
                text += page.extract_text() or ""

        elif filename.endswith('.txt'):
            # Read plain text
            text = file.read().decode('utf-8')

        else:
            # Try reading as text anyway
            text = file.read().decode('utf-8', errors='ignore')

    except Exception as e:
        print("Error reading file:", e)
        return ""

    return text.lower()


# -----------------------------------------------
# FUNCTION - Score resume against job description
# -----------------------------------------------
def score_resume(resume_text, job_description):
    # Words to ignore (not useful as keywords)
    stopwords = set([
        'the','a','an','and','or','but','in','on','at','to','for',
        'of','with','by','from','is','are','be','was','were','have',
        'has','will','we','our','you','your','their','this','that',
        'it','as','not','they','than','more','also','can','which',
        'all','about','up','out','if','into','through','during',
        'including','using','based','experience','looking','work',
        'working','team','ability','strong','knowledge','skills',
        'required','preferred','must','should','good','excellent',
        'great','understanding','able','help','position','role',
        'candidate','years','year','minimum','plus','highly'
    ])

    # Extract keywords from job description
    words = re.findall(r'\b[a-z][a-z0-9+#.]*\b', job_description.lower())
    freq = {}
    for word in words:
        if word not in stopwords and len(word) > 2:
            freq[word] = freq.get(word, 0) + 1

    # Get top 20 most important keywords
    keywords = sorted(freq, key=freq.get, reverse=True)[:20]

    # Check which keywords are in the resume
    matched = [k for k in keywords if k in resume_text]
    missing = [k for k in keywords if k not in resume_text]

    # Calculate score out of 100
    score = round((len(matched) / max(len(keywords), 1)) * 100)

    # Generate verdict and suggestion
    if score >= 70:
        verdict = "Strong Match - Recommended for Interview"
        suggestion = (
            f"Excellent! This resume matches {len(matched)} out of {len(keywords)} "
            f"key requirements. Strongly recommend for interview."
        )
    elif score >= 40:
        verdict = "Partial Match - Review Recommended"
        suggestion = (
            f"Moderate match. Missing keywords: {', '.join(missing[:5])}. "
            f"Candidate may need upskilling in some areas."
        )
    else:
        verdict = "Weak Match - Not Recommended"
        suggestion = (
            f"Low match score. Resume is missing critical skills like: "
            f"{', '.join(missing[:5])}. Not suitable for this role."
        )

    return {
        "score": score,
        "verdict": verdict,
        "suggestion": suggestion,
        "matched_keywords": matched,
        "missing_keywords": missing,
        "total_keywords": len(keywords)
    }


# -----------------------------------------------
# RUN THE SERVER
# -----------------------------------------------
if __name__ == '__main__':
    print("Server starting at http://localhost:5000")
    app.run(debug=True, port=5000)