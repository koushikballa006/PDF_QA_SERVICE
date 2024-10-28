# PDF_QA_SERVICE

# 1. Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows use: .\venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start PostgreSQL using Docker
docker-compose up -d postgres

# 4. Initialize Alembic and create first migration
alembic init alembic
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head

# 5. Create necessary directories
mkdir -p storage/pdfs storage/extracted_text storage/vectorstore

# 6. Run the application
uvicorn app.main:app --reload
