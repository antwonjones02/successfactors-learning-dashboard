# SuccessFactors Learning Analytics Dashboard

A professional, production-ready dashboard for visualizing and analyzing learning data from SAP SuccessFactors Learning Management System (LMS).

## 🚀 Features

- **Real-time Data Connection**: Direct integration with SuccessFactors Learning API
- **OAuth 2.0 Authentication**: Secure token-based authentication
- **Executive Dashboard**: Key metrics and visualizations for learning analytics
- **Data Explorer**: Browse and export data from various API endpoints
- **Caching System**: Improved performance with intelligent data caching
- **Professional UI**: Clean, modern interface built with Streamlit
- **Export Capabilities**: Download data in CSV format

## 📋 Prerequisites

- Python 3.8 or higher
- SAP SuccessFactors Learning instance
- API credentials (Client ID, Client Secret, User ID)

## 🛠️ Installation

1. Clone the repository:
```bash
git clone https://github.com/antwonjones02/successfactors-learning-dashboard.git
cd successfactors-learning-dashboard
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Configure your credentials:
```bash
cp config_template.py config_production.py
```

4. Edit `config_production.py` with your SuccessFactors credentials.

## 🔧 Configuration

Update the `config_production.py` file with your credentials:

```python
SF_CONFIG = {
    "CLIENT_ID": "your-client-id",
    "CLIENT_SECRET": "your-client-secret",
    "USER_ID": "your-user-id",
    "BASE_URL": "https://your-company.plateau.com",
}
```

## 🚀 Running the Dashboard

```bash
streamlit run learning_dashboard_production.py
```

The dashboard will open in your browser at `http://localhost:8501`

## 📊 Dashboard Sections

### 1. Executive Dashboard
- Total completions
- Active learners
- Learning events
- Completion rates
- Trend charts

### 2. Learning Activity
- Detailed learning history
- Course completions
- User progress tracking

### 3. User Analytics
- User database exploration
- Learning paths analysis
- Performance metrics

### 4. Data Explorer
- Test API endpoints
- Export raw data
- Custom queries

## 🔒 Security

- Credentials are stored locally and never committed to version control
- OAuth tokens expire after 1 hour and are automatically refreshed
- All API calls use HTTPS

## 📁 Project Structure

```
├── learning_dashboard_production.py  # Main dashboard application
├── config_template.py               # Configuration template
├── config_production.py            # Your credentials (gitignored)
├── requirements.txt                # Python dependencies
├── .gitignore                     # Git ignore file
└── README.md                      # This file
```

## 🤝 Contributing

Feel free to submit issues and enhancement requests!

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- Built with [Streamlit](https://streamlit.io/)
- Integrates with [SAP SuccessFactors](https://www.sap.com/products/hcm/learning.html)
- Charts powered by [Plotly](https://plotly.com/)