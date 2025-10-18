import sqlite3
from datetime import datetime
import hashlib

# ---------- DATABASE SETUP ----------
DB = "bank.db"
conn = sqlite3.connect(DB)
cur = conn.cursor()

# Create tables if not exists
cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT UNIQUE,
    hashed_password TEXT,
    balance REAL
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    type TEXT,
    amount REAL,
    date TEXT,
    FOREIGN KEY(user_id) REFERENCES users(id)
)
""")
conn.commit()
conn.close()


# ---------- HELPER FUNCTIONS ----------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def register_user():
    name = input("Enter Name: ")
    email = input("Enter Email: ")
    password = input("Enter Password: ")
    balance = float(input("Enter Initial Deposit: "))

    hashed = hash_password(password)

    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO users (name, email, hashed_password, balance) VALUES (?, ?, ?, ?)",
                    (name, email, hashed, balance))
        conn.commit()
        print("✅ Registration Successful!")
        return email
    except sqlite3.IntegrityError:
        print("⚠️ Email already exists!")
        return None
    finally:
        conn.close()


def login_user():
    email = input("Enter Email: ")
    password = input("Enter Password: ")
    hashed = hash_password(password)

    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE email=? AND hashed_password=?", (email, hashed))
    user = cur.fetchone()
    conn.close()

    if user:
        print(f"✅ Login Successful! Welcome {user[1]}")
        return email
    else:
        print("❌ Invalid Email or Password!")
        return None


def get_user_id(email):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE email=?", (email,))
    user = cur.fetchone()
    conn.close()
    return user[0] if user else None


def check_balance(email):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT balance FROM users WHERE email=?", (email,))
    bal = cur.fetchone()
    conn.close()
    if bal:
        print(f"💰 Current Balance: ₹{bal[0]}")
    else:
        print("❌ User not found!")


def deposit_money(email, amount):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT id, balance FROM users WHERE email=?", (email,))
    user = cur.fetchone()
    if user:
        new_balance = user[1] + amount
        cur.execute("UPDATE users SET balance=? WHERE id=?", (new_balance, user[0]))
        cur.execute("INSERT INTO transactions (user_id, type, amount, date) VALUES (?, ?, ?, ?)",
                    (user[0], "Deposit", amount, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        print(f"✅ Deposited ₹{amount}. New Balance: ₹{new_balance}")
    else:
        print("❌ User not found!")
    conn.close()


def withdraw_money(email, amount):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT id, balance FROM users WHERE email=?", (email,))
    user = cur.fetchone()
    if user:
        if user[1] >= amount:
            new_balance = user[1] - amount
            cur.execute("UPDATE users SET balance=? WHERE id=?", (new_balance, user[0]))
            cur.execute("INSERT INTO transactions (user_id, type, amount, date) VALUES (?, ?, ?, ?)",
                        (user[0], "Withdraw", amount, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            conn.commit()
            print(f"✅ Withdrawn ₹{amount}. New Balance: ₹{new_balance}")
        else:
            print("⚠️ Insufficient Balance!")
    else:
        print("❌ User not found!")
    conn.close()


def show_transactions(email):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    user_id = get_user_id(email)
    if user_id:
        cur.execute("SELECT type, amount, date FROM transactions WHERE user_id=? ORDER BY date", (user_id,))
        rows = cur.fetchall()
        print("\n--- Transaction History ---")
        if rows:
            for row in rows:
                print(f"{row[2]} | {row[0]} | ₹{row[1]}")
        else:
            print("No transactions yet.")
    else:
        print("❌ User not found!")
    conn.close()


def transfer_funds(sender_email, receiver_email, amount):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    # Check sender
    cur.execute("SELECT id, balance FROM users WHERE email=?", (sender_email,))
    sender = cur.fetchone()
    if not sender:
        print("❌ Sender not found!")
        conn.close()
        return

    # Check receiver
    cur.execute("SELECT id, balance FROM users WHERE email=?", (receiver_email,))
    receiver = cur.fetchone()
    if not receiver:
        print("❌ Receiver not found!")
        conn.close()
        return

    if sender[1] < amount:
        print("⚠️ Insufficient Balance!")
        conn.close()
        return

    # Update balances
    cur.execute("UPDATE users SET balance=? WHERE id=?", (sender[1] - amount, sender[0]))
    cur.execute("UPDATE users SET balance=? WHERE id=?", (receiver[1] + amount, receiver[0]))

    # Record transactions
    cur.execute("INSERT INTO transactions (user_id, type, amount, date) VALUES (?, ?, ?, ?)",
                (sender[0], f"Transfer to {receiver_email}", amount, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    cur.execute("INSERT INTO transactions (user_id, type, amount, date) VALUES (?, ?, ?, ?)",
                (receiver[0], f"Received from {sender_email}", amount, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

    conn.commit()
    conn.close()
    print(f"✅ ₹{amount} transferred from {sender_email} to {receiver_email}.")


# ---------- MAIN PROGRAM ----------
user_email = None

while True:
    print("\n=== Welcome to Online Banking System ===")
    print("1. Register")
    print("2. Login")
    print("3. Exit")
    choice = input("Choose: ")

    if choice == "1":
        user_email = register_user()
    elif choice == "2":
        user_email = login_user()
    elif choice == "3":
        print("Exiting... Thank you!")
        break
    else:
        print("Invalid choice!")

    # If logged in, show banking menu
    while user_email:
        print("\n--- Banking Menu ---")
        print("1. Check Balance")
        print("2. Deposit Money")
        print("3. Withdraw Money")
        print("4. Transaction History")
        print("5. Fund Transfer")
        print("6. Logout")
        option = input("Choose: ")

        if option == "1":
            check_balance(user_email)
        elif option == "2":
            try:
                amt = float(input("Enter amount to deposit: "))
                deposit_money(user_email, amt)
            except ValueError:
                print("⚠️ Please enter a valid number!")
        elif option == "3":
            try:
                amt = float(input("Enter amount to withdraw: "))
                withdraw_money(user_email, amt)
            except ValueError:
                print("⚠️ Please enter a valid number!")
        elif option == "4":
            show_transactions(user_email)
        elif option == "5":
            receiver = input("Enter receiver email: ")
            try:
                amt = float(input("Enter amount to transfer: "))
                transfer_funds(user_email, receiver, amt)
            except ValueError:
                print("⚠️ Please enter a valid number!")
        elif option == "6":
            print("Logging out...")
            user_email = None
        else:
            print("Invalid option!")