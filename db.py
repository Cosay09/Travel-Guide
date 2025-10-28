import customtkinter as ctk
import tkinter as tk
import sqlite3
import hashlib
import os


DB_PATH = "users.db"


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Travel Explorer")
        self.geometry("1000x600")
        self.resizable(False, False)

        init_db()

        self.build_welcome_page()
    

    def build_welcome_page(self):
        for widget in self.winfo_children():
            widget.destroy()

        title = ctk.CTkLabel(self, text="Welcome to Travel Explorer", font=("Arial", 26, "bold"))
        title.pack(pady=40)

        subtitle = ctk.CTkLabel(self, text="Continue as:", font=("Arial", 20))
        subtitle.pack(pady=20)

        # Buttons for roles
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=10)

        manager_btn = ctk.CTkButton(btn_frame, text="Manager", width=200, command=self.manager_login_page)
        manager_btn.pack(pady=10)

        employee_btn = ctk.CTkButton(btn_frame, text="Employee", width=200, command=self.employee_login_page)
        employee_btn.pack(pady=10)

        customer_btn = ctk.CTkButton(btn_frame, text="Customer", width=200, command=self.customer_welcome_page)
        customer_btn.pack(pady=10)

        
    def manager_login_page(self):
        for widget in self.winfo_children():
            widget.destroy()

        label = ctk.CTkLabel(self, text="Welcome, Manager!", font=("Arial", 24, "bold"))
        label.pack(pady=30)

        username_label = ctk.CTkLabel(self, text="Username:", font=("Arial", 16))
        username_label.pack()
        username_entry = ctk.CTkEntry(self, width=250)
        username_entry.pack(pady=5)

        password_label = ctk.CTkLabel(self, text="Password:", font=("Arial", 16))
        password_label.pack()
        password_entry = ctk.CTkEntry(self, width=250, show="*")
        password_entry.pack(pady=5)

        message = ctk.CTkLabel(self, text="", font=("Arial", 14), text_color="red")
        message.pack(pady=5)

        def login():
            username = username_entry.get().strip()
            password = password_entry.get().strip()

            if not username or not password:
                message.configure(text="Please enter both username and password.")
                return
            
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            cur.execute("SELECT password FROM users WHERE username=? AND role='manager'", (username,))
            result = cur.fetchone()
            conn.close()

            if result and result[0] == hash_password(password):
                message.configure(text="Login successful!", text_color="green")
                # Proceed to manager dashboard (not implemented)
            else:
                message.configure(text="Invalid username/password. Please try again.", text_color="red")
        
        login_btn = ctk.CTkButton(self, text="Login", width=120, command=login)
        login_btn.pack(pady=15)

        back_btn = ctk.CTkButton(self, text="← Back", width=100, command=self.build_welcome_page)
        back_btn.pack(pady=10)

        self.bind("<Return>", lambda event: login_btn.invoke())
            


    def employee_login_page(self):
        for widget in self.winfo_children():
            widget.destroy()

        label = ctk.CTkLabel(self, text="Welcome, Employee!", font=("Arial", 24, "bold"))
        label.pack(pady=30)

        username_label = ctk.CTkLabel(self, text="Username:", font=("Arial", 16))
        username_label.pack()
        username_entry = ctk.CTkEntry(self, width=250)
        username_entry.pack(pady=5)

        password_label = ctk.CTkLabel(self, text="Password:", font=("Arial", 16))
        password_label.pack()
        password_entry = ctk.CTkEntry(self, width=250, show="*")
        password_entry.pack(pady=5)

        message = ctk.CTkLabel(self, text="", font=("Arial", 14), text_color="red")
        message.pack(pady=5)

        def login():
            username = username_entry.get().strip()
            password = password_entry.get().strip()

            if not username or not password:
                message.configure(text="Please enter both username and password.")
                return
            
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            cur.execute("SELECT password FROM users WHERE username=? AND role='employee'", (username,))
            result = cur.fetchone()
            conn.close()

            if result and result[0] == hash_password(password):
                message.configure(text="Login successful!", text_color="green")
                # Proceed to employee dashboard (not implemented yet)
            else:
                message.configure(text="Invalid username/password. Please try again.", text_color="red")

        def register():
            username = username_entry.get().strip()
            password = password_entry.get().strip()

            if not username or not password:
                message.configure(text="Please enter both username and password.")
                return
                
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()

            try:
                cur.execute("INSERT INTO users VALUES (?, ?, ?)", (username, hash_password(password), "employee"))
                conn.commit()
                message.configure(text="Registration successful! You can now log in.", text_color="green")
            except sqlite3.IntegrityError:
                message.configure(text="Username already exists. Please choose another.", text_color="red")
                
            conn.close()

        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(pady=15)

        login_btn = ctk.CTkButton(button_frame, text="Login", width=120, command=login)
        login_btn.grid(row=0, column=0, padx=10)

        register_btn = ctk.CTkButton(button_frame, text="Register", width=120, command=register)
        register_btn.grid(row=0, column=1, padx=10)

        back_btn = ctk.CTkButton(self, text="← Back", width=100, command=self.build_welcome_page)
        back_btn.pack(pady=10)

        # Bind Enter key to trigger login
        self.bind("<Return>", lambda event: login_btn.invoke())

    
    def customer_welcome_page(self):
        for widget in self.winfo_children():
            widget.destroy()

        label = ctk.CTkLabel(self, text="Welcome, Customer!", font=("Arial", 26, "bold"))
        label.pack(pady=80)

        sublabel = ctk.CTkLabel(self, text="Enjoy exploring the app!", font=("Arial", 18))
        sublabel.pack(pady=10)

        back_btn = ctk.CTkButton(self, text="← Back", width=120, command=self.build_welcome_page)
        back_btn.pack(pady=30)
        

def init_db():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT,
            role TEXT
        )
    """)
    # Hardcode manager
    try:
        cur.execute("INSERT INTO users VALUES (?, ?, ?)", ("manager", hashlib.sha256("manager123".encode()).hexdigest(), "manager"))
    except sqlite3.IntegrityError:
        pass  # manager already exists
    conn.commit()
    conn.close()


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

if __name__ == "__main__":
    app = App()
    app.mainloop()

    

'''
import sqlite3

conn = sqlite3.connect("users.db")
cur = conn.cursor()

cur.execute("SELECT * FROM users")
rows = cur.fetchall()

for row in rows:
    print(row)

conn.close()
'''