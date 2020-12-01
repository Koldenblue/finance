from flask import Flask, render_template, request, redirect
from sqlalchemy import create_engine, text
app = Flask(__name__)

engine = create_engine("sqlite+pysqlite:///finance.db", echo=True, future=True)

with engine.connect() as conn:
    conn.execute(text("DROP TABLE IF EXISTS registrants"))
    conn.execute(text("CREATE TABLE 'registrants' ('id' INTEGER PRIMARY KEY, 'name' VARCHAR(255),'email' VARCHAR(255))"))
    conn.execute(text("INSERT INTO registrants (name, email) VALUES ('alice', 'a@a.com')"))
    conn.execute(text("INSERT INTO registrants (name, email) VALUES ('b', 'b@b.com')"))
    conn.commit()