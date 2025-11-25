# app.py
from backend import db
db.initialize()
from frontend.gui import App

if __name__ == "__main__":
    app = App()
    app.mainloop()