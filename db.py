import mysql.connector

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="smritisinha@mysql719",
    database="bloodbank"
)

cursor = conn.cursor(dictionary=True)