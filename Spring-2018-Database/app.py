#Import Flask Library
from flask import Flask, render_template, request, session, url_for, redirect
import pymysql.cursors
from passlib.hash import md5_crypt
from util import *
from functools import wraps


#Initialize the app from Flask
app = Flask(__name__)

#Configure MySQL
conn = pymysql.connect(host='localhost',
                       user='root',
                       password='',
                       db='reservation',
                       charset='utf8mb4',
                       cursorclass=pymysql.cursors.DictCursor)


# Define login check (decorator)
def login_required(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if not session:
            return redirect(url_for('login'))
        return func(*args, **kwargs)
    return decorated_function

# staff check
def is_staff(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if session['userType'] != 'airline_staff':
            return redirect(url_for('login'))
        return func(*args, **kwargs)
    return decorated_function


#Define a route to index function
@app.route('/')
def index():
	return render_template('index.html')


#Define a route for guest
@app.route('/guest')
def guest():
    return render_template('guest.html')


#Define route for login
@app.route('/login')
def login():
    # clear session each time request a login
    session.clear()
    return render_template('login.html')


#User selection for register
@app.route('/userselect', methods=['GET', 'POST'])
@login_required
def userSelect():
    if request.method == 'POST':
        userType = request.form.get('userType')
        if userType == 'customer':
            customer = True
            agent = False
            staff = False
        elif userType == 'agent':
            agent = True
            customer = False
            staff = False
        elif userType == 'staff':
            staff = True
            customer = False
            agent = False
        return render_template('register.html', customer=customer, agent=agent, staff=staff)
    else:
        return render_template('userSelect.html')


#Define route for register
@app.route('/register')
def register():
	return render_template('register.html')


#Authenticates the login
@app.route('/loginAuth', methods=['GET', 'POST'])
def loginAuth():
    #grabs information from the forms
    ID = request.form['ID']
    rawpwd = request.form['password']
    userType = request.form['userType']

    #cursor used to send queries
    cursor = conn.cursor()
    #executes query
    attribute = 'username' if userType == 'airline_staff' else 'email'
    query = 'SELECT * FROM ' + userType + ' WHERE ' + attribute + ' = %s'
    cursor.execute(query, (ID))
    exist = cursor.fetchone()
    cursor.close()
    error = None
    if exist:
        # check password
        if md5_crypt.verify(rawpwd, exist['password']):
            #creates a session for the the user
            #session is a built in
            session['ID'] = ID
            session['userType'] = userType
            session['airline_name'] = exist['airline_name'] if 'airline_name' in exist else None
            return redirect(url_for('home'))
        else:
            error = 'Invalid password'
            return render_template('login.html', error=error)
    else:
        error = 'Wrong email address or username or user type'
        return render_template('login.html', error=error)



#Authenticates the register
@app.route('/registerAuth', methods=['GET', 'POST'])
def registerAuth():
    # determine user type
    userType = request.form['userType']
    # email/username and raw password from the form
    attribute, ID = ('username', request.form['username']) if userType == 'airline_staff' else ('email', request.form['email'])
    raw_pwd = request.form['password']

    #cursor used to send queries
    cursor = conn.cursor()
    #executes query
    query = 'SELECT * FROM ' + userType + ' WHERE ' + attribute + ' = %s'
    cursor.execute(query, (ID))
    #stores the results in a variable
    data = cursor.fetchone()
    #use fetchall() if you are expecting more than 1 data row
    error = None
    # return error message if user exists
    if(data):
        #If the previous query returns data, then user exists
        error = "This user already exists"
        return render_template('register.html', error = error)
    else:
        # hash password here
        password = md5_crypt.encrypt(raw_pwd)

        if userType == 'customer':
            email = ID
            name = request.form['name']
            building_number = request.form['building_number']
            street = request.form['street']
            city = request.form['city']
            state = request.form['state']
            phone_number = request.form['phone_number']
            passport_number = request.form['passport_number']
            passport_expiration = request.form['passport_expiration']
            passport_country = request.form['passport_country']
            date_of_birth = request.form['date_of_birth']

            insert = 'INSERT INTO customer VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'
            cursor.execute(insert, (email, name, password, building_number, street, city, state, phone_number, passport_number, passport_expiration, passport_country, date_of_birth))
        elif userType == 'booking_agent':
            "what"
            email = ID
            booking_agent_id = request.form['booking_agent_id']

            insert = 'INSERT INTO booking_agent VALUES(%s, %s, %s)'
            cursor.execute(insert, (email, password, booking_agent_id))
        elif userType == 'airline_staff':
            username = ID
            first_name = request.form['first_name']
            last_name = request.form['last_name']
            date_of_birth = request.form['date_of_birth']
            airline_name = request.form['airline_name']

            insert = 'INSERT INTO airline_staff VALUES(%s, %s, %s, %s, %s, %s)'
            cursor.execute(insert, (username, password, first_name, last_name, date_of_birth, airline_name))
        conn.commit()
        cursor.close()
        return render_template('index.html')



@app.route('/home')
@login_required
def home():
    ID = session['ID'] if 'ID' in session else None
    userType = session['userType'] if 'userType' in session else None
    airline_name = session['airline_name'] if 'airline_name' in session else None

    if userType == 'customer':
        return render_template('customer_home.html', ID=ID, userType=userType)
    elif userType == 'booking_agent':
        return render_template('agent_home.html', ID=ID, userType=userType)
    elif userType == 'airline_staff':
        return redirect(url_for('staff_home', ID=ID, userType=userType, airline_name=airline_name))
    else:
        return redirect(url_for('guest_home'))

		
@app.route('/logout')
@login_required
def logout():
    # session.pop('ID')
    # userType = session.pop('userType')
    # if userType == 'airline_staff':
    #     session.pop('airline_name')
    session.clear()
    return redirect('/')


@app.route('/guest_home', methods=['GET', 'POST'])
def guest_home():
    if request.method == 'POST':
        if flightSearchValidation(request):
            query, args = flightSearchQuery(request)
            cursor = conn.cursor()
            cursor.execute(query, args)
            data = cursor.fetchall()
            return render_template('guest_home.html', result=data)
        else:
            return render_template('guest_home.html', error="Please enter departure city/airport, arrival city/airport and travel date")
    else:
        return render_template('guest_home.html')


@app.route('/staff_home', methods=['GET', 'POST'])
@login_required
@is_staff
def staff_home():
    if request.method == 'POST':
        airline_name = request.form['airline_name']
        flight_num = request.form['flight_num']
        cursor = conn.cursor()
        # if status update
        if 'update_status' in request.form:
            new_status = request.form['update_status']
            query = "UPDATE flight SET status = %s WHERE airline_name = %s and flight_num = %s"
            cursor.execute(query, (new_status, airline_name, flight_num))
            conn.commit()
            msg = "Flight %s state updated as %s" % (flight_num, new_status)
            data = showFlightsOfAirlineCo(cursor, airline_name, in_n_days = 30)
            cursor.close()
            return render_template('staff_home.html', ID=session['ID'], userType=session['userType'], result=data, airline_name=airline_name, message=msg)
        # show passengers of a specific flight
        query = '''SELECT DISTINCT name, email FROM purchases, ticket, customer 
                   WHERE ticket.ticket_id = purchases.ticket_id and customer_email = email and airline_name = %s and flight_num = %s'''
        cursor.execute(query, (airline_name, flight_num))
        passengers = cursor.fetchall()
        cursor.close()
        return render_template('staff_home.html', airline_name=airline_name, flight_num=flight_num, passengers=passengers)
    else:
        # read ID, userType, airline_name from args if login
        # else read from session (back from check passenger)
        ID = request.args.get('ID') if request.args.get('ID') else session['ID']
        userType = request.args.get('userType') if request.args.get('userType') else session['userType']
        airline_name = request.args.get('airline_name') if request.args.get('airline_name') else session['airline_name']
        query = 'SELECT * FROM flight WHERE departure_time >= NOW() and departure_time < NOW() + INTERVAL 1 MONTH and airline_name = %s'
        cursor = conn.cursor()
        cursor.execute(query, airline_name)
        data = cursor.fetchall()
        return render_template('staff_home.html', ID=ID, userType=userType, result=data, airline_name=airline_name)


@app.route('/create_flight', methods=['GET', 'POST'])
@login_required
@is_staff
def create_flight():
    if request.method == 'POST':
        airline_name = request.form['airline_name']
        flight_num = request.form['flight_num']
        departure_airport = request.form['departure_airport']
        departure_time = request.form['departure_time']
        arrival_airport = request.form['arrival_airport']
        arrival_time = request.form['arrival_time']
        price = request.form['price']
        status = request.form['status']
        airplane_id = request.form['airplane_id']
        query = 'INSERT INTO flight VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s)'
        cursor = conn.cursor()
        cursor.execute(query, (airline_name, flight_num, departure_airport, departure_time, arrival_airport, arrival_time, price, status, airplane_id))
        conn.commit()
        msg = "Flight %s Added" % flight_num
        data = showFlightsOfAirlineCo(cursor, airline_name, in_n_days = 30)
        cursor.close()
        return render_template('staff_home.html', ID=session['ID'], userType=session['userType'], result=data, airline_name=airline_name, message=msg)
    else:
        return render_template('create_flight.html', airline_name=session['airline_name'])


@app.route('/add_airplane', methods=['GET', 'POST'])
@login_required
@is_staff
def add_airplane():
    if request.method =='POST':
        airline_name = request.form['airline_name']
        airplane_id = request.form['airplane_id']
        seats = request.form['seats']
        query = 'INSERT INTO airplane VALUES(%s, %s, %s)'
        cursor = conn.cursor()
        cursor.execute(query, (airline_name, airplane_id, seats))
        conn.commit()
        msg = 'Airplane %s Added' % airplane_id
        data = showAirplanesOfAirlineCo(cursor, airline_name)
        cursor.close()
        return render_template('add_airplane.html', ID=session['ID'], userType=session['userType'], result=data, airline_name=airline_name, message=msg)
    else:
        airline_name = session['airline_name']
        cursor = conn.cursor()
        data = showAirplanesOfAirlineCo(cursor, airline_name)
        cursor.close()
        return render_template('add_airplane.html', ID=session['ID'], userType=session['userType'], result=data, airline_name=airline_name)


@app.route('/add_airport', methods=['GET', 'POST'])
@login_required
@is_staff
def add_airport():
    if request.method =='POST':
        airline_name = request.form['airline_name']
        airport_name = request.form['airport_name']
        airport_city = request.form['airport_city']
        query = 'INSERT INTO airport VALUES(%s, %s)'
        cursor = conn.cursor()
        cursor.execute(query, (airport_name, airport_city))
        conn.commit()
        msg = 'Airport %s in %s Added' % (airport_name, airport_city)
        data = showFlightsOfAirlineCo(cursor, airline_name, in_n_days = 30)
        cursor.close()
        return render_template('staff_home.html', ID=session['ID'], userType=session['userType'], result=data, airline_name=airline_name, message=msg)
    else:
        return render_template('add_airport.html', airline_name=session['airline_name'])


@app.route('/top_destinations')
@login_required
@is_staff
def top_destinations():
    # show last 3 month and last year top destinations repectively
    query3month = queryForTopDestinations('MONTH')
    queryLastYear = queryForTopDestinations('YEAR')
    cursor = conn.cursor()
    cursor.execute(query3month, session['airline_name'])
    data3month = cursor.fetchall()
    cursor.execute(queryLastYear, session['airline_name'])
    dataLastYear = cursor.fetchall()
    cursor.close()
    return render_template('top_destinations.html', airline_name=session['airline_name'], result3month=data3month, resultLastYear=dataLastYear)


@app.route('/report', methods=['GET', 'POST'])
@login_required
@is_staff
def report():
    if request.method == 'POST':
        cursor = conn.cursor()
        # if search by start and end date
        # if no end_date then set end_date to NOW
        if 'start_date' in request.form:
            start_date = request.form['start_date']
            end_date = request.form['end_date'] if 'end_date' in request.form else 'NOW()'
            queryStartEnd = 'SELECT * FROM ticket NATURAL JOIN purchases WHERE airline_name = %s AND purchase_date >= %s AND purchase_date <= %s'
            cursor.execute(queryStartEnd, (session['airline_name'], start_date, end_date))
            ticketNum = len(cursor.fetchall())
            cursor.close()
            msg = 'From %s to %s number of tickets sold: ' % (start_date, end_date)
            return render_template('report.html', airline_name=session['airline_name'], result=ticketNum, message=msg)
        # if search last month
        elif request.form['interval'] == 'MONTH':
            queryLastMonth = 'SELECT * FROM ticket NATURAL JOIN purchases WHERE airline_name = %s AND purchase_date <= NOW() and purchase_date > NOW() - INTERVAL %s MONTH'
            cursor.execute(queryLastMonth, (session['airline_name'], request.form['period']))
            ticketNum = len(cursor.fetchall())
            cursor.close()
            msg = 'Number of tickets sold for last %s month: ' % request.form['period']
            return render_template('report.html', airline_name=session['airline_name'], result=ticketNum, message=msg)
        # if search last year
        elif request.form['interval'] == 'YEAR':
            count = []
            numOfYears = int(request.form['period'])
            for i in range(12*numOfYears, 0, -1):
                query = 'SELECT * FROM ticket NATURAL JOIN purchases WHERE airline_name = %s AND purchase_date < NOW() - INTERVAL %s MONTH and purchase_date >= NOW() - INTERVAL %s MONTH'
                cursor.execute(query, (session['airline_name'], i-1, i))
                count.append(len(cursor.fetchall()))
            cursor.close()
            totSellNum = sum(count)
            msg = 'Number of tickets sold for last %s year: ' % numOfYears
            return render_template('report.html', airline_name=session['airline_name'], sellStats=count, totSellNum=totSellNum, message=msg)

    return render_template('report.html', airline_name=session['airline_name'])


@app.route('/show_revenue')
@login_required
@is_staff
def revenue():
    # total direct revenue of an airline company
    queryDirect = ('SELECT SUM(price) AS revenue_direct '
                   'FROM (SELECT * '
                         'FROM ticket NATURAL JOIN flight NATURAL JOIN purchases '
                         'WHERE airline_name = %s AND booking_agent_id IS NULL) AS T')

    # total indirect revenue of an airline company (10% commision)
    queryIndirect = ('SELECT 0.9 * SUM(price) AS revenue_indirect '
                     'FROM (SELECT * '
                           'FROM ticket NATURAL JOIN flight NATURAL JOIN purchases '
                           'WHERE airline_name = %s AND booking_agent_id IS NOT NULL) AS T')

    cursor = conn.cursor()
    cursor.execute(queryDirect, session['airline_name'])
    dataDirect = cursor.fetchone()
    cursor.execute(queryIndirect, session['airline_name'])
    dataIndirect = cursor.fetchone()
    cursor.close()
    data = []
    # using float() to convert Decimal
    # if no direct or indirect revenue set to 0
    data.append(float(dataDirect['revenue_direct']) if dataDirect['revenue_direct'] else 0)
    data.append(float(dataIndirect['revenue_indirect']) if dataIndirect['revenue_indirect'] else 0)

    return render_template('revenue.html', airline_name=session['airline_name'], result=data)


@app.route('/view_customers', methods=['GET', 'POST'])
@login_required
@is_staff
def view_customers():
    if request.method == 'POST':
        customer_email = request.form['customer_email']
        return redirect(url_for('show_trips', airline_name=session['airline_name'], customer_email=customer_email))
    # all customers(cust_email, name and number of trips) of an airline company
    query = ('SELECT customer_email, name, COUNT(*) AS travels '
             'FROM (SELECT ticket_id, customer_email, name, airline_name, flight_num '
                   'FROM purchases NATURAL JOIN ticket, customer '
                   'WHERE customer_email = email AND airline_name = %s) AS records '
             'GROUP BY customer_email '
             'ORDER BY travels DESC')
    cursor = conn.cursor()
    cursor.execute(query, session['airline_name'])
    data = cursor.fetchall()

    return render_template('view_customers.html', airline_name=session['airline_name'], result=data)


@app.route('/show_trips')
@login_required
@is_staff
def show_trips():
    customer_email = request.args.get('customer_email')
    airline_name = session['airline_name']
    # query all trips of a customer of an airline company
    query = ('SELECT ticket_id, booking_agent_id, purchase_date, flight_num '
             'FROM purchases NATURAL JOIN ticket, customer '
             'WHERE customer_email = email AND airline_name = %s AND customer_email = %s')
    cursor = conn.cursor()
    cursor.execute(query, (airline_name, customer_email))
    data = cursor.fetchall()

    return render_template('show_trips.html', airline_name=airline_name, result=data, customer_email=customer_email)

		
app.secret_key = 'some key that you will never guess'
#Run the app on localhost port 5000
#debug = True -> you don't have to restart flask
#for changes to go through, TURN OFF FOR PRODUCTION
if __name__ == "__main__":
    app.run('127.0.0.1', 5000, debug = True)