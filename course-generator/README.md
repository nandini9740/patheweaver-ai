# Pathweaver AI — Personalized Learning Roadmaps

Pathweaver AI is a premium, goal-driven learning roadmap generator. It uses the Gemini 2.0 Flash model to create structured, personalized curricula tailored to your skill level, available time, and learning style.

## 🚀 Features
- **AI-Powered Personalization**: Tailored content based on your specific goals.
- **Visual Guides**: Interactive flowcharts for every module.
- **Smart Fallback**: Expert-curated roadmaps available even when AI quotas are reached.
- **Export Options**: Download your roadmap as PDF or JSON.
- **Premium Design**: Modern, responsive UI with glassmorphism aesthetics.

## 🛠️ Tech Stack
- **Frontend**: Vanilla JS, HTML5, CSS3 (Custom Design System).
- **Backend**: FastAPI (Python), SQLAlchemy, SQLite.
- **AI**: Google Gemini 2.0 Flash (google-genai SDK).

## 📦 Setup & Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/pathweaver-ai.git
   cd pathweaver-ai
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment**:
   Create a `.env` file in the `backend` folder and add your Gemini API Key:
   ```env
   GEMINI_API_KEY=your_api_key_here
   ```

4. **Run the application**:
   ```bash
   python -m uvicorn backend.app.main:app --reload
   ```

5. **Access the webapp**:
   Open `http://localhost:8000` in your browser.

## 📄 License
This project is licensed under the MIT License.
