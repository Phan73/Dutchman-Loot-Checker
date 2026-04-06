# 🛡️ Flying Dutchman Guild Loot Auditor

A specialized Streamlit application designed for **I The Flying Dutchman I** guild members to audit loot logs and verify chest deposits. This tool automates the process of matching loot event logs against chest history to identify missing items and facilitate trade verification.

## ✨ Features
* **Strict Guild Filtering:** Automatically filters logs to show only items looted by guild members.
* **Cross-Language Support:** Matches item names between Korean and English game clients.
* **Smart Sorting:** Accounted-for items stay at the top; missing items flow to the bottom for review.
* **Trade Verification:** Compare missing loot against Officer/Caller chest logs to verify hand-offs.
* **Deduplication:** Uses a custom "Sync Window" to prevent double-counting caused by laggy logs.

---

## 🚀 Getting Started

Follow these steps to set up the environment and run the app on your local machine.

### 1. Prerequisites
Ensure you have **Python 3.9 or higher** installed. You can check your version by running:
`python --version`

### 2. Clone the Repository
Download the code to your machine:

git clone [https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git](https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git)
cd YOUR_REPO_NAME

###3. Set Up a Virtual Environment (Recommended)
This keeps your project dependencies isolated from your main system:

# Windows
python -m venv venv
.\venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate

4. Install Dependencies
Install all required libraries using the provided requirements file:
pip install -r requirements.txt

5. Run the Application
Start the Streamlit server:
streamlit run app.py
📖 Usage Guide
Loot Logs: Upload your .txt files exported from the Albion Loot Logger.

Chest Logs: Upload your .csv or copy-pasted .txt logs from the in-game chest history.

Audit: - Use the Full Report for a guild-wide overview.

Use Player Audit to check a specific member. Select "Officer Names" to see if the missing items were traded to a lead.

Export: Hover over any table to download the results as a CSV for guild records.
