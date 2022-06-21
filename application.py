import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    rows = db.execute("SELECT symbol, name, Shares, Price, TOTAL FROM data WHERE user_id = :id",
                          id=session["user_id"])
    rows1 = db.execute("SELECT cash FROM users WHERE id = :id1",
                          id1=session["user_id"])
    return render_template("index.html", rows=rows, rows1=rows1)
    return apology("TODO")


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        if not request.form.get("symbol"):
            return apology("Must provide a symbol", 403)
        Symb = request.form.get("symbol").upper()
        Lokp = lookup(Symb)
        if Lokp == None:
            return apology("invalid symbol", 403)
        if not request.form.get("shares"):
            return apology("Must enter number of shares", 403)
        if not request.form.get("shares").isdigit():
            return apology("Must enter positve number of shares", 403)
        shares = int(request.form.get("shares"))
        rows = db.execute("SELECT cash FROM users WHERE id = :iod",iod=session["user_id"])
        cash = rows[0]["cash"]
        cash_stock =  shares * Lokp["price"]
        if cash-cash_stock < 0:
            return apology("Sorry, you cannot afford the stock", 403)
        db.execute("UPDATE users SET cash = cash - :cost WHERE id = :iod",cost = cash_stock, iod=session["user_id"])
        db.execute("INSERT INTO transictions (user_id, symbol, name, Shares, Price, TOTAL) VALUES (:id, :symbol, :name, :share, :price, :total)", id=session["user_id"],symbol=Symb, name=Lokp['name'], share=shares, price =Lokp["price"]  , total= cash_stock)
        rows = db.execute("SELECT symbol FROM data WHERE user_id = :id", id=session["user_id"])
        for row in rows:
            if row["symbol"] == Symb:
                db.execute("UPDATE data SET Shares = Shares + :s,TOTAL = TOTAL + :t WHERE user_id = :io1d AND symbol = :sq",sq=Symb,s=shares,t = cash_stock, io1d=session["user_id"])
                return redirect("/")

        db.execute("INSERT INTO data (user_id, symbol, name, Shares, Price, TOTAL) VALUES (:id, :symbol, :name, :share, :price, :total)", id=session["user_id"],
        symbol=Symb, name=Lokp['name'], share=shares, price =Lokp["price"]  , total= cash_stock)
        return redirect("/")




    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    rows = db.execute("SELECT symbol, Shares, Price,time FROM transictions WHERE user_id = :id",
                          id=session["user_id"])
    return render_template("history.html", rows=rows)
    return apology("TODO")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    if request.method =="POST":
        if not request.form.get("symbol"):
            return apology("must provide a symbol", 403)
        Lookp = lookup(request.form.get("symbol"))
        if Lookp == None:
            return apology("invalid symbol", 403)
        Name = Lookp['name']
        Price = Lookp['price']
        Symbol = Lookp['symbol']

        return render_template("quoted.html", name = Name, p = Price, s = Symbol)
    else:
        return render_template("quote.html")







@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    if request.method == "GET":
        rows = db.execute("SELECT symbol FROM data WHERE user_id = :id", id=session["user_id"] )
        return render_template("sell.html", rows = rows)
    else:
        if not request.form.get("symbol"):
            return apology("Must select a symbol", 403)
        symbol = request.form.get("symbol")
        if not request.form.get("shares"):
            return apology("Must input shares", 403)
        shares = int(request.form.get("shares"))
        rows = db.execute("SELECT Shares FROM data WHERE symbol = :sy AND user_id = :id", sy=symbol,id=session["user_id"])
        for row in rows:
            x = row["Shares"]

        if int(x) == 0:
            return apology("No shares to sell", 403)
        if int(x) < shares:
            return apology("Not enough shares to sell", 403)
        if not request.form.get("shares").isdigit():
            return apology("Must enter positve number of shares", 403)
        rows = db.execute("SELECT cash FROM users WHERE id = :iod",iod=session["user_id"])
        Lop = lookup(symbol)
        cash1 = rows[0]["cash"]
        cash_stock1 =  shares * Lop["price"]
        db.execute("UPDATE users SET cash = cash + :cost WHERE id = :iod",cost = cash_stock1, iod=session["user_id"])
        rows = db.execute("SELECT symbol FROM data WHERE user_id = :id", id=session["user_id"])
        db.execute("INSERT INTO transictions (user_id, symbol, name, Shares, Price, TOTAL) VALUES (:id, :symbol, :name, :share, :price, :total)", id=session["user_id"],symbol=symbol, name=Lop['name'], share=shares, price =Lop["price"]  , total= cash_stock1)
        for row in rows:
            if row["symbol"] == symbol:
                db.execute("UPDATE data SET Shares = Shares - :s,TOTAL = TOTAL - :t WHERE user_id = :io1d AND symbol = :sq",sq=symbol,s=shares,t = cash_stock1, io1d=session["user_id"])
                return redirect("/history")
        return redirect("/history")


    return apology("TODO")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
