import sqlite3, random, time, os
from getpass import getpass
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt
from rich.align import Align
from rich import box

console = Console()
conn = sqlite3.connect("slots.db")
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, balance INTEGER, luck_multiplier REAL)''')
c.execute('''CREATE TABLE IF NOT EXISTS codes (code TEXT PRIMARY KEY, reward_type TEXT, value REAL)''')
conn.commit()

symbols = ["🍒", "🍋", "🔔", "💎", "7️⃣"]
payouts = {"🍒": 2, "🍋": 3, "🔔": 5, "💎": 10, "7️⃣": 25}

def spinner_animation():
    for _ in range(3):
        spin = [random.choice(symbols) for _ in range(3)]
        console.print(Align.center(" | ".join(spin), vertical="middle", style="bold green"))
        time.sleep(0.2)
        console.clear()

def slot_spin(luck):
    reel = []
    for _ in range(3):
        reel.append(random.choices(symbols, weights=[1*luck if s=="7️⃣" else 1 for s in symbols])[0])
    return reel

def print_reel(reel):
    console.print(Panel(Align.center(" | ".join(reel)), title="🎰 Result 🎰", subtitle="Try your luck!", style="bold magenta"))

def win_amount(reel, bet):
    if reel[0] == reel[1] == reel[2]:
        return int(bet * payouts.get(reel[0], 0))
    return 0

def register():
    console.print(Panel("Register Account", style="bold blue"))
    username = input("Username: ")
    password = getpass("Password: ")
    c.execute("SELECT * FROM users WHERE username = ?", (username,))
    if c.fetchone():
        console.print("⚠️ User already exists.", style="bold red")
        return None
    c.execute("INSERT INTO users VALUES (?, ?, ?, ?)", (username, password, 100, 1.0))
    conn.commit()
    console.print("✅ Account created!", style="bold green")
    return username

def login():
    console.print(Panel("Login", style="bold cyan"))
    username = input("Username: ")
    password = getpass("Password: ")
    if username == "ADMIN" and password == "ADMIN":
        return "ADMIN"
    c.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
    if c.fetchone():
        return username
    console.print("❌ Invalid login.", style="bold red")
    return None

def get_balance(user):
    c.execute("SELECT balance FROM users WHERE username = ?", (user,))
    return c.fetchone()[0]

def get_luck(user):
    c.execute("SELECT luck_multiplier FROM users WHERE username = ?", (user,))
    return c.fetchone()[0]

def update_balance(user, new_balance):
    c.execute("UPDATE users SET balance = ? WHERE username = ?", (new_balance, user))
    conn.commit()

def update_luck(user, value):
    c.execute("UPDATE users SET luck_multiplier = ? WHERE username = ?", (value, user))
    conn.commit()

def redeem_code(user):
    code = input("Enter code: ").strip()
    c.execute("SELECT * FROM codes WHERE code = ?", (code,))
    row = c.fetchone()
    if not row:
        console.print("❌ Invalid code.", style="bold red")
        return
    if row[1] == "money":
        bal = get_balance(user)
        update_balance(user, bal + int(row[2]))
        console.print(f"✅ Code redeemed! +{int(row[2])}$ added.", style="bold green")
    elif row[1] == "luck":
        update_luck(user, float(row[2]))
        console.print(f"🍀 Double luck activated! x{row[2]}", style="bold yellow")
    c.execute("DELETE FROM codes WHERE code = ?", (code,))
    conn.commit()

def admin_panel():
    while True:
        console.clear()
        console.print(Panel("🛠️ ADMIN PANEL 🛠️", style="bold red"))
        choice = Prompt.ask("[1] Add Code  [2] Show Users  [3] Exit", choices=["1", "2", "3"])
        if choice == "1":
            code = input("Code: ").strip()
            type_ = Prompt.ask("Type", choices=["money", "luck"])
            value = input("Value: ")
            c.execute("INSERT INTO codes VALUES (?, ?, ?)", (code, type_, value))
            conn.commit()
            console.print("✅ Code created!", style="bold green")
            input("Press Enter...")
        elif choice == "2":
            table = Table(title="All Users", box=box.SIMPLE_HEAVY)
            table.add_column("Username", style="bold cyan")
            table.add_column("Balance", style="bold green")
            table.add_column("Luck", style="bold yellow")
            c.execute("SELECT username, balance, luck_multiplier FROM users")
            for row in c.fetchall():
                table.add_row(row[0], str(row[1]), str(row[2]))
            console.print(table)
            input("Press Enter...")
        elif choice == "3":
            break

def play(user):
    while True:
        os.system("cls" if os.name == "nt" else "clear")
        balance = get_balance(user)
        luck = get_luck(user)
        table = Table(title=f"🎰 Welcome, {user} 🎰", box=box.DOUBLE_EDGE, style="bold green")
        table.add_column("Balance", justify="center", style="bold blue")
        table.add_column("Luck", justify="center", style="bold yellow")
        table.add_row(f"${balance}", f"x{luck}")
        console.print(table)
        choice = Prompt.ask("[1] Spin  [2] Redeem Code  [3] Exit", choices=["1", "2", "3"])
        if choice == "1":
            try:
                bet = int(input("Bet amount: "))
                if bet <= 0 or bet > balance:
                    console.print("⚠️ Invalid bet.", style="bold red")
                    continue
            except:
                continue
            update_balance(user, balance - bet)
            spinner_animation()
            reel = slot_spin(luck)
            print_reel(reel)
            winnings = win_amount(reel, bet)
            if winnings > 0:
                console.print(f"🎉 You won ${winnings}!", style="bold green")
                update_balance(user, get_balance(user) + winnings)
            else:
                console.print("😢 No win this time.", style="bold red")
            input("Press Enter...")
        elif choice == "2":
            redeem_code(user)
            input("Press Enter...")
        elif choice == "3":
            break

def main():
    while True:
        os.system("cls" if os.name == "nt" else "clear")
        console.print(Panel("🎰 [bold cyan]Terminal Slot Machine[/bold cyan] 🎰", subtitle="By GhostGamer 😎", style="bold magenta"))
        choice = Prompt.ask("[1] Login  [2] Register  [3] Exit", choices=["1", "2", "3"])
        if choice == "1":
            user = login()
            if user == "ADMIN":
                admin_panel()
            elif user:
                play(user)
        elif choice == "2":
            register()
            input("Press Enter...")
        elif choice == "3":
            break

main()
