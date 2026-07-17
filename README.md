# 🛍️ PricePulse

PricePulse is an intelligent price tracking application built with Python. It automatically monitors product prices from e-commerce websites, stores historical price data, and notifies users when the price drops.

## ✨ Features

- 🔍 Real-time product price scraping
- 💾 SQLite database for storing price history
- 📊 Detects price increases and decreases
- 📱 Telegram notifications for price drops
- ⏰ Automated price monitoring
- 📈 Interactive Streamlit dashboard
- 📝 Price history logging

---

## 🛠️ Tech Stack

- Python
- BeautifulSoup
- Requests
- SQLite
- APScheduler
- Telegram Bot API
- Streamlit
- Plotly
- Pandas

---

## 📂 Project Structure

```
PricePulse/
│
├── main.py
├── scraper.py
├── database.py
├── notifier.py
├── scheduler.py
├── requirements.txt
├── README.md
└── screenshots/
```

---

## ⚙️ How It Works

1. User enters a product URL.
2. The scraper extracts the latest product price.
3. The latest price is compared with the previously stored price.
4. The new price is saved in the SQLite database.
5. If the price drops, a Telegram notification is sent instantly.
6. The Streamlit dashboard displays price history and trends.

---

## 🚀 Installation

Clone the repository

```bash
git clone https://github.com/priyanka052/PricePulse.git
```

Go to the project folder

```bash
cd PricePulse
```

Install dependencies

```bash
pip install -r requirements.txt
```

Run the application

```bash
python main.py
```

Launch the dashboard

```bash
streamlit run app.py
```

---

## 📸 Screenshots

> <img width="1900" height="855" alt="image" src="https://github.com/user-attachments/assets/24a54674-6c81-49fc-b7ce-065b8a782db0" />
<img width="1864" height="807" alt="image" src="https://github.com/user-attachments/assets/e9e8e0f0-e362-48cf-a75a-4ec60abf904a" />
<img width="1882" height="754" alt="image" src="https://github.com/user-attachments/assets/1ff11455-f375-452b-9585-534958edaceb" />
<img width="1824" height="774" alt="image" src="https://github.com/user-attachments/assets/e51304c4-f5dd-4f9d-9328-4445fbf276e5" />


---

## 🔮 Future Improvements

- Track multiple products simultaneously
- Email notifications
- AI-based price trend prediction
- Product comparison
- Cloud deployment
- User authentication

---

## 👩‍💻 Author

**Priyanka**

Artificial Intelligence & Machine Learning Engineering Student

Built as a portfolio project to learn Python, Web Scraping, Automation, Databases, and Data Visualization.
