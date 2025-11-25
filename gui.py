# frontend/gui.py
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
from backend import services
from PIL import Image
import uuid


PRIMARY = "#4C6EF5"
ACCENT = "#22C55E"
BG = "#F4F6FB"
CARD = "#FFFFFF"
TEXT = "#0F172A"
SIDEBAR_BG = "#0F172A"
SIDEBAR_FG = "#FFFFFF"

def setup_styles():
    style = ttk.Style()
    style.theme_use("default")

    style.configure("TFrame", background=BG)
    style.configure("Topbar.TFrame", background=PRIMARY)
    style.configure("Sidebar.TFrame", background=SIDEBAR_BG)
    style.configure("Card.TFrame", background=CARD, relief="flat", borderwidth=0)
    style.configure("TLabel", background=BG, foreground=TEXT, font=("Inter", 11))
    style.configure("Header.TLabel", background=PRIMARY, foreground="white", font=("Inter", 14, "bold"))
    style.configure("Sidebar.TLabel", background=SIDEBAR_BG, foreground=SIDEBAR_FG, font=("Inter", 11))
    style.configure("TButton", font=("Inter", 10))
    style.map("Accent.TButton", background=[("active", "#1B9C4A"), ("!disabled", ACCENT)])



def gen_account_no():
    return "AC" + uuid.uuid4().hex[:8].upper()

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Bank System")
        self.geometry("1000x650")
        self.style = ttk.Style(self)
        self.style.theme_use("clam")
        self.logged_admin = None
        self.logged_user = None
        self.create_login_view()
        
    

    def create_login_view(self):
        for w in self.winfo_children(): w.destroy()
        frame = ttk.Frame(self, style="TFrame", padding=20)
        frame.pack(expand=True, fill="both")
        left = ttk.Frame(frame,style="TFrame", width=320); left.pack(side="left", fill="y", padx=10)
        right = ttk.Frame(frame,style="TFrame"); right.pack(side="left", fill="both", expand=True)

        ttk.Label(left, text="BANKO", font=("Segoe UI", 20, "bold")).pack(pady=10)
        ttk.Label(left, text="Admin login").pack(pady=6)
        self.admin_user = ttk.Entry(left); self.admin_user.pack(pady=2)
        ttk.Label(left, text="Password").pack(pady=2)
        self.admin_pw = ttk.Entry(left, show="*"); self.admin_pw.pack(pady=2)
        ttk.Button(left, text="Admin Login", command=self.handle_admin_login).pack(pady=8)

        ttk.Separator(right, orient="horizontal").pack(fill="x", pady=8)
        ttk.Label(right, text="User Login or Create Account", font=("Segoe UI", 12)).pack(pady=8)
        ttk.Label(right, text="Account #:").pack()
        self.user_acc = ttk.Entry(right); self.user_acc.pack()
        ttk.Label(right, text="Password:").pack()
        self.user_pw = ttk.Entry(right, show="*"); self.user_pw.pack()
        ttk.Button(right, text="User Login", command=self.handle_user_login).pack(pady=6)
        ttk.Button(right, text="Create Account", command=self.open_create_account).pack(pady=6)

    # ---- admin login
    def handle_admin_login(self):
        u = self.admin_user.get().strip()
        p = self.admin_pw.get().strip()
        if not u or not p:
            messagebox.showerror("Error","Enter credentials")
            return
        if services.validate_admin(u, p):
            self.logged_admin = u
            services.audit(u, "login", "admin login")
            self.open_admin_dashboard()
        else:
            messagebox.showerror("Error","Invalid admin")

    # ---- user login
    def handle_user_login(self):
        acc = self.user_acc.get().strip()
        pw = self.user_pw.get().strip()
        if services.authenticate_user(acc, pw):
            self.logged_user = acc
            services.audit(acc, "user_login", "")
            self.open_user_dashboard(acc)
        else:
            messagebox.showerror("Error","Invalid account or password")

    # ---- create account dialog
    def open_create_account(self):
        dlg = tk.Toplevel(self)
        dlg.title("Create Account")
        ttk.Label(dlg, text="Name").pack(pady=6)
        name_e = ttk.Entry(dlg); name_e.pack()
        ttk.Label(dlg, text="Password").pack(pady=6)
        pw_e = ttk.Entry(dlg, show="*"); pw_e.pack()
        ttk.Label(dlg, text="Initial deposit").pack(pady=6)
        dep_e = ttk.Entry(dlg); dep_e.pack()
        def submit():
            name = name_e.get().strip(); pw = pw_e.get().strip()
            try:
                dep = float(dep_e.get().strip() or 0.0)
            except:
                messagebox.showerror("Error","Invalid deposit")
                return
            acc_no = gen_account_no()
            try:
                services.create_account(acc_no, name, pw, dep)
                messagebox.showinfo("Created", f"Account created: {acc_no}")
                dlg.destroy()
            except Exception as e:
                messagebox.showerror("Error", str(e))
        ttk.Button(dlg, text="Create", command=submit).pack(pady=10)

    # ---- admin dashboard
    def open_admin_dashboard(self):
        for w in self.winfo_children(): w.destroy()
        sidebar = ttk.Frame(self, width=220); sidebar.pack(side="left", fill="y")
        main = ttk.Frame(self); main.pack(side="left", fill="both", expand=True, padx=8, pady=8)
        ttk.Label(sidebar, text=f"Admin: {self.logged_admin}", font=("Segoe UI", 12)).pack(pady=8)
        ttk.Button(sidebar, text="Accounts", command=lambda: self.show_accounts(main)).pack(fill="x", padx=8, pady=6)
        ttk.Button(sidebar, text="Transactions", command=lambda: self.show_transactions(main)).pack(fill="x", padx=8, pady=6)
        ttk.Button(sidebar, text="Loans", command=lambda: self.show_loans(main)).pack(fill="x", padx=8, pady=6)
        ttk.Button(sidebar, text="Export CSV", command=self.export_csv).pack(fill="x", padx=8, pady=6)
        ttk.Button(sidebar, text="Export TX (PDF)", command=self.export_tx_pdf).pack(fill="x", padx=8, pady=6)
        ttk.Button(sidebar, text="Audit", command=lambda: self.show_audit(main)).pack(fill="x", padx=8, pady=6)
        ttk.Button(sidebar, text="Logout", command=self.logout).pack(side="bottom", padx=8, pady=12)
        self.show_accounts(main)

    def logout(self):
        if self.logged_admin:
            services.audit(self.logged_admin, "logout", "")
            self.logged_admin = None
        self.create_login_view()

    # ---- admin views
    def show_accounts(self, container):
        for w in container.winfo_children(): w.destroy()
        ttk.Label(container, text="Accounts", font=("Segoe UI", 14, "bold")).pack(anchor="w")
        cols = ("account_no", "name", "balance", "status", "kyc", "created_at")
        tree = ttk.Treeview(container, columns=cols, show="headings")
        for c in cols:
            tree.heading(c, text=c.title().replace("_"," "))
        tree.pack(fill="both", expand=True, pady=6)
        for a in services.list_accounts():
            tree.insert("", "end", values=(a["account_no"], a["name"], f"₱{a['balance']:.2f}", a["status"], a.get("kyc",0), a.get("created_at","")))
        # actions
        btns = ttk.Frame(container); btns.pack(fill="x")
        ttk.Button(btns, text="Refresh", command=lambda: self.show_accounts(container)).pack(side="left", padx=4)
        ttk.Button(btns, text="Deposit", command=lambda: self.admin_deposit(tree, container)).pack(side="left", padx=4)
        ttk.Button(btns, text="Withdraw", command=lambda: self.admin_withdraw(tree, container)).pack(side="left", padx=4)
        ttk.Button(btns, text="Transfer", command=lambda: self.admin_transfer()).pack(side="left", padx=4)
        ttk.Button(btns, text="Delete", command=lambda: self.admin_delete(tree, container)).pack(side="left", padx=4)
        ttk.Button(btns, text="KYC Verify", command=lambda: self.admin_kyc(tree, container)).pack(side="left", padx=4)

    def admin_deposit(self, tree, container):
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Select", "Select an account first")
            return
        acc = tree.item(sel[0])["values"][0]
        amt = simpledialog.askfloat("Amount", "Amount to deposit:")
        if amt is None: return
        try:
            services.deposit(acc, amt, performed_by=self.logged_admin)
            messagebox.showinfo("Success", f"Deposited ₱{amt:.2f}")
            self.show_accounts(container)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def admin_withdraw(self, tree, container):
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Select", "Select an account first")
            return
        acc = tree.item(sel[0])["values"][0]
        amt = simpledialog.askfloat("Amount", "Amount to withdraw:")
        if amt is None: return
        try:
            services.withdraw(acc, amt, performed_by=self.logged_admin)
            messagebox.showinfo("Success", f"Withdrew ₱{amt:.2f}")
            self.show_accounts(container)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def admin_transfer(self):
        src = simpledialog.askstring("From", "Source account no:")
        dst = simpledialog.askstring("To", "Destination account no:")
        amt = simpledialog.askfloat("Amount", "Amount to transfer:")
        if not src or not dst or amt is None:
            return
        try:
            services.transfer(src, dst, amt, performed_by=self.logged_admin)
            messagebox.showinfo("Success", f"Transferred ₱{amt:.2f}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def admin_delete(self, tree, container):
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Select", "Select an account first")
            return
        acc = tree.item(sel[0])["values"][0]
        if messagebox.askyesno("Confirm", f"Delete account {acc}?"):
            conn = services.connect()
            cur = conn.cursor()
            cur.execute("DELETE FROM accounts WHERE account_no=?", (acc,))
            conn.commit(); conn.close()
            services.audit(self.logged_admin, "delete_account", acc)
            self.show_accounts(container)

    def admin_kyc(self, tree, container):
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Select", "Select an account first")
            return
        acc = tree.item(sel[0])["values"][0]
        conn = services.connect()
        cur = conn.cursor()
        cur.execute("UPDATE accounts SET kyc=1 WHERE account_no=?", (acc,))
        conn.commit(); conn.close()
        services.audit(self.logged_admin, "kyc_verify", acc)
        self.show_accounts(container)

    def show_transactions(self, container):
        for w in container.winfo_children(): w.destroy()
        ttk.Label(container, text="Transactions", font=("Segoe UI", 14)).pack(anchor="w")
        cols = ("id","tx_type","from_acc","to_acc","amount","performed_by","timestamp")
        tree = ttk.Treeview(container, columns=cols, show="headings")
        for c in cols: tree.heading(c, text=c.title().replace("_"," "))
        tree.pack(fill="both", expand=True)
        for t in services.get_transactions():
            tree.insert("", "end", values=(t["id"], t["tx_type"], t.get("from_acc"), t.get("to_acc"), f"₱{t['amount']}", t.get("performed_by"), t["timestamp"]))
        ttk.Button(container, text="Refresh", command=lambda: self.show_transactions(container)).pack(pady=6)

    def show_loans(self, container):
        for w in container.winfo_children(): w.destroy()
        ttk.Label(container, text="Loans", font=("Segoe UI", 14)).pack(anchor="w")
        tree = ttk.Treeview(container, columns=("id","account_no","amount","term_months","status","created_at"), show="headings")
        for c in ("id","account_no","amount","term_months","status","created_at"):
            tree.heading(c, text=c.title())
        tree.pack(fill="both", expand=True)
        for l in services.list_loans():
            tree.insert("", "end", values=(l["id"],l["account_no"],f"₱{l['amount']:.2f}", l["term_months"], l["status"], l["created_at"]))
        ttk.Button(container, text="Refresh", command=lambda: self.show_loans(container)).pack(pady=6)
        # actions: approve/reject/disburse
        btnf = ttk.Frame(container); btnf.pack(pady=6)
        ttk.Button(btnf, text="Approve", command=lambda: self.loan_action(tree,"approved")).pack(side="left", padx=4)
        ttk.Button(btnf, text="Reject", command=lambda: self.loan_action(tree,"rejected")).pack(side="left", padx=4)
        ttk.Button(btnf, text="Disburse", command=lambda: self.loan_action(tree,"disbursed")).pack(side="left", padx=4)

    def loan_action(self, tree, action):
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Select", "Select a loan")
            return
        loan_id = tree.item(sel[0])["values"][0]
        services.update_loan_status(loan_id, action)
        messagebox.showinfo("Loan", f"Loan {action}")
        self.show_loans(tree.master)

    def show_audit(self, container):
        for w in container.winfo_children(): w.destroy()
        ttk.Label(container, text="Audit Log", font=("Segoe UI", 14)).pack(anchor="w")
        cols = ("id","actor","action","details","timestamp")
        tree = ttk.Treeview(container, columns=cols, show="headings")
        for c in cols: tree.heading(c, text=c.title())
        tree.pack(fill="both", expand=True)
        for a in services.list_audit():
            tree.insert("", "end", values=(a["id"], a["actor"], a["action"], a["details"], a["timestamp"]))
        ttk.Button(container, text="Refresh", command=lambda: self.show_audit(container)).pack(pady=6)

    def export_csv(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv")
        if not path: return
        try:
            services.export_accounts_csv(path)
            messagebox.showinfo("Exported", f"Saved to {path}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def export_tx_pdf(self):
        # may raise if reportlab not installed
        try:
            path = filedialog.asksaveasfilename(defaultextension=".pdf")
            if not path: return
            services.export_transactions_pdf(path)
            messagebox.showinfo("Exported", f"Saved to {path}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ---- user dashboard
    def open_user_dashboard(self, acc_no):
        for w in self.winfo_children(): w.destroy()
        self.logged_user = acc_no
        topbar = ttk.Frame(self); topbar.pack(fill="x")
        ttk.Label(topbar, text=f"User: {acc_no}", font=("Segoe UI", 12)).pack(side="left", padx=8)
        ttk.Button(topbar, text="Logout", command=self.create_login_view).pack(side="right", padx=8)
        main = ttk.Frame(self); main.pack(fill="both", expand=True, padx=8, pady=8)
        ttk.Label(main, text=f"Balance: ₱{services.get_account(acc_no)['balance']:.2f}", font=("Segoe UI", 14)).pack(anchor="w")
        frame = ttk.Frame(main); frame.pack(anchor="w", pady=6)
        ttk.Button(frame, text="Deposit", command=lambda: self.user_deposit(acc_no)).pack(side="left", padx=6)
        ttk.Button(frame, text="Withdraw", command=lambda: self.user_withdraw(acc_no)).pack(side="left", padx=6)
        ttk.Button(frame, text="History", command=lambda: self.show_transactions(main, acc_no)).pack(side="left", padx=6)

    def user_deposit(self, acc_no):
        amt = simpledialog.askfloat("Deposit","Amount:")
        if amt is None: return
        try:
            services.deposit(acc_no, amt, performed_by=acc_no)
            messagebox.showinfo("Success", "Deposit complete")
            self.open_user_dashboard(acc_no)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def user_withdraw(self, acc_no):
        amt = simpledialog.askfloat("Withdraw","Amount:")
        if amt is None: return
        try:
            services.withdraw(acc_no, amt, performed_by=acc_no)
            messagebox.showinfo("Success", "Withdraw complete")
            self.open_user_dashboard(acc_no)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def show_transactions(self, container, acc_no=None):
        for w in container.winfo_children(): w.destroy()
        ttk.Label(container, text="Transactions", font=("Segoe UI", 14)).pack(anchor="w")
        cols = ("id","tx_type","from_acc","to_acc","amount","performed_by","timestamp")
        tree = ttk.Treeview(container, columns=cols, show="headings")
        for c in cols: tree.heading(c, text=c.title().replace("_"," "))
        tree.pack(fill="both", expand=True)
        for t in services.get_transactions(acc_no):
            tree.insert("", "end", values=(t["id"], t["tx_type"], t.get("from_acc"), t.get("to_acc"), f"₱{t['amount']:.2f}", t.get("performed_by"), t["timestamp"]))
        ttk.Button(container, text="Back", command=lambda: self.open_user_dashboard(acc_no)).pack(pady=6)

