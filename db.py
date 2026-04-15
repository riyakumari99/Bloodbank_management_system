import mysql.connector

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="riya@99",
    database="bloodbank"
)

cursor = conn.cursor(dictionary=True)