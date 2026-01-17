import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

try:
    with psycopg2.connect(
        host=os.getenv("POSTGRES_HOST"),
        database=os.getenv("POSTGRES_NAME"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        port=os.getenv("POSTGRES_PORT"),
    ) as conn:
        with conn.cursor() as cur:
            pass
except psycopg2.Error as e:
    print(f"Error connecting to the database: {e}")
