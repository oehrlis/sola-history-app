# Local Development

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
docker compose -f docker-compose.dev.yml up --build
```
