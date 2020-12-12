import settings
import os

from sqlalchemy import create_engine, text
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from sqlalchemy import create_engine, text, select
from sqlalchemy.orm import Session as alcSession
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

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
# app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

engine = create_engine("sqlite+pysqlite:///finance.db", echo=True, future=True)

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set. Set in terminal, or see readme for installing and using python-dotenv.")

@app.route("/")
#decorator defined in helpers.py
@login_required
def index():
    """Show portfolio of stocks"""
    # need to lookup each stock user owns. Group by stock name

    with engine.connect() as conn:

        rows = conn.execute(text('SELECT symbol, sum(shares_purchased)'
                        + ' FROM purchases WHERE username = :username'
                        + ' GROUP BY symbol'), [ { 'username': session['username'] } ] )
        rows = rows.all()
        # Keep a running total to sum up all stock holdings
        grand_total = 0
        # Create a new array to contain the SQL values, so that the values may be converted to a dictionary and keys added
        table_rows = []
        for row in rows:
            # Get the current quote for each stock.
            quote = lookup(row['symbol'])
            current_price = quote['price']
            row_dict = {}
            row_dict['symbol'] = row['symbol']
            row_dict['current_price'] = usd(current_price)
            row_dict['sum(shares_purchased)'] = row['sum(shares_purchased)']
            # Get the total current value of the holdings. Add to grand total
            total_value = current_price * row['sum(shares_purchased)']
            row_dict['total_value'] = usd(total_value)
            grand_total += total_value
            table_rows.append(row_dict)

        # Finally, get the user's current cash balance.
        current_cash = conn.execute(text("SELECT cash FROM users WHERE username = :username"), [ { 'username': session['username'] } ] )
        current_cash = current_cash.all()
        current_cash = usd(current_cash[0]['cash'])
        return render_template('index.html', rows=table_rows, grand_total = usd(grand_total), current_cash=current_cash)



@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "GET":
        return render_template("/buy.html")
    # for post, get form info.
    else:
        symbol = request.form.get('symbol')
        shares = request.form.get('shares')

        # First make sure shares are a positive integer
        try:
            shares = int(shares)
        except(ValueError):
            return apology("Only positive integer share numbers accepted.", 403)
        if not isinstance(int(shares), int) or int(shares) <= 0:
            return apology("Only positive integer share numbers may be entered.", 403)

        # Next, find price of stock
        quote = lookup(symbol)
        # if api call is invalid, will return None
        if quote == None:
            return apology('That symbol is invalid!', 403)

        price = quote['price']
        # Next look up how much cash the user has
        with engine.connect() as conn:
            id = session['user_id']
            statement = text("SELECT cash FROM users WHERE id = :id").bindparams(id=id)
            cash = conn.execute(statement)
            cash = cash.all()
            total_price = price * shares
            cash = cash[0]['cash']
            if cash < total_price:
                return apology(f'The total price is {usd(total_price)}. You only have {usd(cash)}!', 403)

            # if user can afford stock, add to purchases table. Get date of purchase as well.
            t1 = datetime.now()
            statement = text('INSERT INTO purchases (username, symbol, stock_price, shares_purchased, total_price, date)'
                    + ' values (:username, :symbol, :stock_price, :shares_purchased, :total_price, :date);').bindparams(username=session['username'], symbol=symbol.upper(), stock_price=usd(price), shares_purchased=shares, total_price=usd(total_price), date=t1)
            conn.execute(statement)
            conn.commit()
            # next subtract price from user's cash
            statement = text('UPDATE users SET cash = :new_cash WHERE username = :username').bindparams( new_cash=cash - total_price, username=session['username'])
            conn.execute(statement)
            conn.commit()
            # finally, redirect to index
            return redirect('/')


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    with engine.connect() as conn:
        statement = text('SELECT symbol, stock_price, shares_purchased, total_price, date FROM purchases WHERE username = :username').bindparams(username=session['username'])
        rows = conn.execute(statement)
        rows = rows.all()
        return render_template('history.html', rows=rows)


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
        with engine.connect() as conn:
            statement = text("SELECT * FROM users WHERE username = :username").bindparams(username=request.form.get("username"))
            rows = conn.execute(statement)
            rows = rows.all()

            # Ensure username exists and password is correct
            if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
                return apology("invalid username and/or password", 403)

            # Remember which user has logged in
            session["user_id"] = rows[0]["id"]
            session['username'] = rows[0]['username']

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
    """Get stock quote."""
    if request.method == "GET":
        return render_template('/quote.html')
    else:
        symbol = request.form.get('symbol')
        print(symbol)
        # use lookup and usd functions from helpers.py
        quote = lookup(symbol)
        # if api call is invalid, will return None
        if quote == None:
            return apology('That symbol is invalid!', 403)
        # print('the quote is', quote)
        quote['price'] = usd(quote['price'])
        return render_template("quoted.html", quote=quote)


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == 'GET':
        return render_template("register.html")
    else:
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)
        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)
        elif request.form.get('password-confirm') != request.form.get('password'):
            return apology("must confirm password", 403)
        else:
            username = request.form.get('username')
            password = generate_password_hash(request.form.get('password'))
            with engine.connect() as conn:
                rows = conn.execute(text("SELECT * FROM users"))
                rows = rows.all()
                #make sure username doesn't already exist
                for row in rows:
                    if username == row['username']:
                        return apology("that username already exists", 403)
        # finally, if no errors, insert new user into db. then go back to login.
        with engine.connect() as conn:
            statement = text("INSERT INTO users (username, hash) VALUES (:username, :hash)").bindparams(username=username, hash=password)
            conn.execute(statement)
            conn.commit()
            return render_template('/login.html')


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    if request.method == "GET":
        with engine.connect() as conn:
            symbols = conn.execute(text('SELECT symbol'
                        + ' FROM purchases WHERE username = :username'
                        + ' GROUP BY symbol'), [ { 'username': session['username'] } ])
            symbols = symbols.all()
            return render_template("/sell.html", symbols=symbols)
    # for post, get form info.
    else:
        symbol = request.form.get('symbol')
        shares = request.form.get('shares')

        # First make sure shares are a positive integer
        try:
            shares = int(shares)
        except(ValueError):
            return apology("Only positive integer share numbers accepted.", 403)
        if not isinstance(int(shares), int) or int(shares) <= 0:
            return apology("Only positive integer share numbers may be entered.", 403)

        # Next, find price of stock
        quote = lookup(symbol)
        # if api call is invalid, will return None
        if quote == None:
            return apology('That symbol is invalid!', 403)
        price = quote['price']

        # Next look up how many shares the user has
        with engine.connect() as conn:
            user_shares = conn.execute(text('SELECT sum(shares_purchased)'
                        + ' FROM purchases WHERE username = :username AND symbol = :symbol'
                        + ' GROUP BY symbol'), [ { 'username': session['username'], 'symbol': symbol } ] )
            user_shares = user_shares.all()
            if user_shares == []:
                return apology(f"You do not own shares of {symbol}!")
            user_shares = user_shares[0]['sum(shares_purchased)']
            # Check to see if the user has enough shares to sell
            if shares > user_shares:
                return apology(f"You may not sell that much, you only own {user_shares} shares of that stock!", 403)

            # if so, calculate the total selling price. insert negative numbers into table for shares sold.
            total_price = price * -shares

            # Get date of purchase as well.
            t1 = datetime.now()
            statement = text('INSERT INTO purchases (username, symbol, stock_price, shares_purchased, total_price, date)'
                    + ' values (:username, :symbol, :stock_price, :shares_purchased, :total_price, :date);').bindparams(username=session['username'], symbol=symbol.upper(), stock_price=usd(price), shares_purchased= -shares, total_price=usd(total_price), date=t1)
            conn.execute(statement)
            conn.commit()
            # next subtract price from user's cash. Since total_price is negative, this will add to cash.
            cash = conn.execute(text("SELECT cash FROM users WHERE id = :id"), [ { 'id': session["user_id"] } ] )
            cash = cash.all()
            cash = cash[0]['cash']
            statement = text('UPDATE users SET cash = :new_cash WHERE username = :username').bindparams(new_cash=cash - total_price, username=session['username'])
            conn.execute(statement)
            conn.commit()
            # finally, redirect to index
            return redirect('/')

@app.route("/add", methods=["GET", "POST"])
@login_required
def add():
    '''allows user to add cash to account.'''
    if request.method == 'GET':
        return render_template('add.html')
    else:
        new_cash = float(request.form.get('add'))
        print(new_cash)
        with engine.connect() as conn:
            cash = conn.execute(text("SELECT cash FROM users WHERE id = :id"), [ { 'id': session["user_id"] } ] )
            cash = cash.all()
            cash = float(cash[0]['cash'])

            statement = text('UPDATE users SET cash = :new_cash WHERE username = :username').bindparams(new_cash=cash + new_cash, username=session['username'])
            conn.execute(statement)
            conn.commit()
            return redirect('/')

def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
