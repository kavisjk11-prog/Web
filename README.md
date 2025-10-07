Invoicing ROI Simulator
A lightweight ROI calculator that helps businesses visualize savings, ROI, and payback when switching from manual to automated invoicing.
Built with Flask (backend), Streamlit (frontend), and SQLite (database)

🚀 Features
💰 Quick Simulation – Enter invoice metrics and instantly see savings, ROI & payback.
💾 Scenario Management (CRUD) – Save, load, and delete named scenarios using SQLite.
⚙️ Favorable Output Logic – Built-in bias ensures automation always shows positive ROI.
📧 Email-Gated Report – Generate PDF/HTML reports only after entering an email.
🧩 Self-Contained Prototype – Works locally with no authentication required.
🧱 Tech Stack
Layer	Technology
Frontend	Streamlit
Backend	Flask
Database	SQLite
Report Engine	WeasyPrint / xhtml2pdf
Language	Python 3.10+
⚙️ Setup & Run Locally
1️⃣ Clone the repository
git clone https://github.com/<your-username>/invoicing-roi-simulator.git
cd invoicing-roi-simulator
2️⃣ Install dependencies
pip install -r requirements.txt
