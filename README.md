# Microsoft Practice Exams

A Streamlit-hosted practice-exam template with eight Microsoft certification banks:

- PL-900, AZ-500, AB-730, AB-900
- AI-901, PL-300, PL-200, AB-731

Each new attempt creates a randomized, pillar-balanced 40–65 question exam. The application supports single-answer, multiple-select, True/False, matching, and ordering questions, answer review, weighted practice scoring, a 700/1000 practice pass line, a timed session, and results review.

## Run locally

1. Install Python 3.10 or later.
2. From this project folder, install the dependency:

   ```powershell
   python -m pip install -r requirements.txt
   ```

3. Start the app:

   ```powershell
   streamlit run app.py
   ```

## Publish with GitHub and Streamlit Community Cloud

1. Create a new empty GitHub repository, for example `microsoft-practice-exams`.
2. In this project folder, run:

   ```powershell
   git init
   git add .
   git commit -m "Initial Streamlit practice exam app"
   git branch -M main
   git remote add origin https://github.com/YOUR-ACCOUNT/microsoft-practice-exams.git
   git push -u origin main
   ```

3. In [Streamlit Community Cloud](https://share.streamlit.io/), select **Create app**, choose the GitHub repository and branch, and set the entry point to `app.py`.
4. Deploy. Streamlit installs the dependency declared in `requirements.txt` automatically.

## Project layout

```text
app.py                         Streamlit application
PracticeExamQuestionBanks/     Version-controlled JSON question banks
requirements.txt               Hosting dependency declaration
.streamlit/config.toml         Theme configuration
```

Question banks are local JSON assets and do not require a database, secret, or API key.

> The 700/1000 result is a practice estimate. Microsoft uses a proprietary scaled-score methodology, so this app does not claim to reproduce an official score.
