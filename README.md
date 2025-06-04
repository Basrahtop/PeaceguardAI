# 🕊️ PeaceGuard AI: Advancing Global Information Integrity for Peace

**PeaceGuard AI is an intelligent framework designed to detect, analyze, and counteract misinformation, hate speech, and other harmful narratives that fuel conflict and undermine peace across diverse global contexts.**

---

**Quick Links:**

* **🚀 Live Demo Application:** [https://peaceguard-ui.onrender.com/](https://peaceguard-ui.onrender.com/)
* **🌐 Project Landing Page:** `[https://peaceguard-visual-guardian.lovable.app/]`
* **🎬 Video Demo:** `[https://drive.google.com/file/d/14cziBYIz2buwhMdl1tENV7aCA0SdDQnH/view?usp=sharing]`
* **📊 Pitch Deck:** `[https://drive.google.com/drive/folders/1HKxDM_LKvk_7xNUx43fsxeLDmfkSZ9u_]`
* **🎤 Video Presentation:** `[https://drive.google.com/file/d/1cOtbuvxPCV6FMJbhpXwUYAJh7wMaRBCb/view?usp=sharing]`

---

## Table of Contents

* [The Challenge: Information as a Catalyst in Conflict](#the-challenge-information-as-a-catalyst-in-conflict)
* [Our Solution: The PeaceGuard AI Framework](#our-solution-the-peaceguard-ai-framework)
* [Key Features & Services](#key-features--services)
    * [Advanced Text Analysis & Risk Assessment](#1-advanced-text-analysis--risk-assessment)
    * [Comprehensive Audio Analysis](#2-comprehensive-audio-analysis)
    * [Proactive Early Warning System (EWS)](#3-proactive-early-warning-system-ews)
    * [Future Services](#future-services)
* [How PeaceGuard AI Works](#how-peaceguard-ai-works)
    * [The Journey of Content](#the-journey-of-content)
    * [Calculating the PeaceGuard AI Risk Score](#calculating-the-peaceguard-ai-risk-score)
    * [The Early Warning System in Action](#the-early-warning-system-in-action)
* [Why PeaceGuard AI is Unique](#why-peaceguard-ai-is-unique)
* [Use Cases](#use-cases)
* [Technology Stack](#technology-stack)
* [Getting Started (Local Setup & Running)](#getting-started-local-setup--running)
    * [Prerequisites](#prerequisites)
    * [Cloning the Repository](#cloning-the-repository)
    * [Backend Setup](#backend-setup)
    * [Frontend Setup](#frontend-setup)
* [Project Status & Vision](#project-status--vision)
* [Contributing](#contributing)
* [License](#license)

## The Challenge: Information as a Catalyst in Conflict

In an era of rapid digital communication, the deliberate spread of misinformation and hate speech has become a critical global concern. These harmful narratives can:

* Erode trust within and between communities worldwide.
* Exacerbate existing societal, ethnic, and political divisions.
* Incite violence and disrupt peacebuilding efforts on a global scale.
* Overwhelm local information ecosystems, especially in areas with limited digital literacy or during times of crisis.

Vulnerable regions globally face unique challenges due to linguistic diversity, complex socio-political dynamics, and the rapid adoption of communication technologies that can be exploited for malicious purposes. Timely identification and contextual understanding of such threats are paramount for effective intervention.

## Our Solution: The PeaceGuard AI Framework

PeaceGuard AI offers an integrated suite of AI-powered services designed to provide actionable intelligence for monitoring the information environment, identifying potential threats, and supporting peace-oriented responses. Our framework aims to empower journalists, fact-checkers, peacebuilders, CSOs, and communities worldwide with tools to navigate and mitigate the impact of harmful information.

## Key Features & Services

PeaceGuard AI is being developed with the following core services:

### 1. Advanced Text Analysis & Risk Assessment
This service performs in-depth analysis of textual content (from articles, social media, or transcribed audio) to:
* Detect and flag specific **keywords** (dangerous, sensitive, and dynamically identified contextual concern terms relevant to evolving local situations globally).
* Analyze **sentiment** to understand the emotional tone and intensity.
* Identify **manipulative framing techniques** such as "Us vs. Them" narratives and "Alarmist Claims."
* Leverage cloud-based AI for **content categorization** to identify potentially sensitive topics.
* Calculate a custom **PeaceGuard AI Risk Score** and qualitative label (Low, Medium, High, Critical) based on a weighted combination of these factors, providing clear, human-readable explanations and contributing factors.
* **Automatic EWS Trigger:** If the assessed risk is high, this service automatically flags the content for evaluation by the Early Warning System.

### 2. Comprehensive Audio Analysis
This service processes audio files to:
* Transcribe speech to text using robust Speech-to-Text (STT) technology.
* Automatically feed the transcribed text into the **Advanced Text Analysis & Risk Assessment pipeline** (described above), including the automatic EWS trigger, to provide a full risk profile for spoken content.

### 3. Proactive Early Warning System (EWS)
A proactive system designed to:
* Evaluate high-risk content (flagged by Text/Audio Analysis) against a knowledge base of **predefined historical conflict precursor patterns** drawn from diverse global events.
* Generate **EWS alerts** if current activities mirror these dangerous historical patterns, indicating a potential escalation.
* Includes a conceptual framework for disseminating these alerts through accessible channels, with an initial focus on **SMS** for broad reach (currently mocked, with a testable interface).

### Future Services
We envision expanding PeaceGuard AI with:
* **Specialized Speech-to-Text (STT) for Challenging Environments:** To improve transcription accuracy for audio with diverse global accents, local dialects, or poor recording quality.
* **AI-Assisted Contextual Verification Support:** A service to help human verifiers by providing rich contextual information for claims or media.

## How PeaceGuard AI Works (Simplified Explanation)

Imagine PeaceGuard AI as a highly observant assistant, carefully reading texts and listening to audio to flag potentially harmful content.

### The Journey of Content
1.  **Input:** You provide text directly, upload an audio file, or (in a future iteration of our live analysis feature) speak into a microphone.
2.  **Transcription (for Audio):** If it's audio, PeaceGuard AI first transcribes the speech into text.
3.  **Core Analysis:** The text is then deeply analyzed for multiple risk indicators.

### Calculating the PeaceGuard AI Risk Score
This is where PeaceGuard AI's intelligence shines. It's not just about one factor; it's a combination:
* **"Danger Words" & "Warning Signs":** It looks for specific keywords known to be problematic or sensitive, including terms highly relevant to current local contexts.
* **"Emotional Temperature":** It assesses if the message is very angry, hateful, or fearful.
* **"Tricky Language":** It identifies manipulative framing like "Us vs. Them" narratives or "Alarmist Claims."
* **Topic Flags:** It considers general content categories flagged by Google Cloud's AI.

All these clues are weighted and combined. For example, a sensitive keyword in a very angry, alarmist message using divisive language will result in a much higher risk score than the same keyword in a neutral text. This score is then given a clear label: **Low, Medium, High, or Critical Risk**, along with an explanation.

### The Early Warning System in Action
If the initial analysis flags content as "Medium" risk or higher, our **Early Warning System (EWS)** automatically steps in. It compares the problematic content's characteristics against patterns known from *historical conflicts* – how dangerous narratives spread and escalated in the past. If a strong match is found, a specific EWS alert is generated, complete with a suggested SMS message for rapid, accessible dissemination to those who can help mitigate the threat.

## Why PeaceGuard AI is Unique

* **Context-Driven & Localized Insights:** Adapts to understand regional specifics and evolving threats.
* **Focus on Manipulative Tactics:** Identifies *how* messages are framed to deceive, not just keywords.
* **Historically-Informed Early Warnings:** Aims to learn from past conflict drivers for proactive alerts.
* **Integrated & Automated Pipeline:** From audio/text input to risk score and potential EWS alert in one flow.
* **Accessible Alerting Concept:** Designed with SMS in mind for broad EWS reach.

## Technology Stack

* **Backend:** Python, FastAPI
* **Frontend:** Gradio
* **AI/ML & Core Services:** Google Cloud AI (Natural Language API, Speech-to-Text, Translation API), custom Python-based rule engines and NLP techniques.
* **Deployment:** Docker, Render (for backend and frontend), Gunicorn.

## Getting Started (Local Setup & Running)

Follow these steps to set up and run PeaceGuard AI on your local machine.

### Prerequisites
* Python 3.10+
* Git
* Access to Google Cloud Platform with:
    * A project created.
    * The "Cloud Natural Language API," "Cloud Translation API," and "Cloud Speech-to-Text API" enabled.
    * A Service Account created with appropriate permissions (`Cloud Natural Language API User`, `Cloud Translation API User`, `Cloud Speech API User`) and its JSON key file downloaded.

### Cloning the Repository
```bash
git clone [https://github.com/Basrahtop/PeaceguardAI.git](https://github.com/Basrahtop/PeaceguardAI.git) 
cd PeaceguardAI

1. Backend Setup
All backend commands should be run from the project root directory (e.g., PeaceGuardAI/).

a. Create and Activate Virtual Environment:
It's highly recommended to use a virtual environment.

Bash

python -m venv venv
Activate it:

On Windows (Git Bash / MINGW64):
Bash

source venv/Scripts/activate
On Windows (Command Prompt / PowerShell):
Bash

venv\Scripts\activate
On macOS / Linux:
Bash

source venv/bin/activate
Your terminal prompt should now indicate the (venv) is active.

b. Install Dependencies:

Bash

pip install -r requirements.txt
c. Set Google Cloud Credentials:
You need to tell the application where to find your Google Cloud service account key. Set the GOOGLE_APPLICATION_CREDENTIALS environment variable in your current terminal session before starting the backend.

On Windows (Git Bash / MINGW64) or macOS / Linux:

Bash

export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/service-account-key.json"
(Replace /path/to/your/service-account-key.json with the actual absolute path to your downloaded JSON key file. For MINGW64 on Windows, a path might look like /c/Users/YourUser/Downloads/my-key.json)

On Windows Command Prompt:

Bash

set GOOGLE_APPLICATION_CREDENTIALS="C:\path\to\your\service-account-key.json"
d. Run the FastAPI Backend Server:

Bash

uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
The backend server will start, and you should see logs indicating it's running on http://0.0.0.0:8000.
Look for confirmation messages like "Google Cloud clients initialized successfully."
Keep this terminal window open and running.

2. Frontend Setup (Gradio UI)
a. Ensure Backend is Running: The FastAPI backend (from step 2d) must be running in its own terminal.

b. Open a New Terminal: Do not use the same terminal where the backend is running.

c. Navigate to Project Root and Activate Virtual Environment:

Bash

cd path/to/your/PeaceGuardAI 
# (If not already there)

# Activate venv in this new terminal:
# On Windows (Git Bash / MINGW64):
source venv/Scripts/activate
# On Windows (Command Prompt / PowerShell):
# venv\Scripts\activate
# On macOS / Linux:
# source venv/bin/activate
d. Check Backend URL Configuration (for local testing):

The frontend_gradio.py script is configured to connect to http://localhost:8000/api/v1 by default if the PEACEGUARD_BACKEND_URL environment variable is not set. This is suitable for local testing against your locally running backend.
e. Run the Gradio Frontend Application:

Bash

python frontend_gradio.py
f. Access the PeaceGuard AI UI:

The terminal will output a local URL, typically: Running on local URL: http://127.0.0.1:7860
Open this URL in your web browser to interact with the application.