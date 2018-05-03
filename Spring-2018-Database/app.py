#Import Flask Library
from flask import Flask, render_template, request, session, url_for, redirect
import pymysql.cursors
from passlib.hash import md5_crypt
from util import *


#Initialize the app from Flask
app = Flask(__name__)

#Configure MySQL
conn = pymysql.connect(host='localhost',
                       user='root',
                       password='',
                       db='reservation',
                       charset='utf8mb4',
                       cursorclass=pymysql.cursors.DictCursor)


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
	return render_template('login.html')


#User selection for register
@app.route('/userselect', methods=['GET', 'POST'])
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
            print(exist)
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
        return render_template('guest_home.html')

		
@app.route('/post', methods=['GET', 'POST'])
def post():
	username = session['username']
	cursor = conn.cursor()
	blog = request.form['blog']
	query = 'INSERT INTO blog (blog_post, username) VALUES(%s, %s)'
	cursor.execute(query, (blog, username))
	conn.commit()
	cursor.close()
	return redirect(url_for('home'))


@app.route('/logout')
def logout():
    session.pop('ID')
    userType = session.pop('userType')
    if userType == 'airline_staff':
        session.pop('airline_name')
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
        data = showFlightsOfAirlineCo(cursor, airline_name, in_n_days = 30)
        cursor.close()
        return render_template('staff_home.html', ID=session['ID'], userType=session['userType'], result=data, airline_name=airline_name, message=msg)
    else:
        return render_template('add_airplane.html', airline_name=session['airline_name'])


		
app.secret_key = 'some key that you will never guess'
#Run the app on localhost port 5000
#debug = True -> you don't have to restart flask
#for changes to go through, TURN OFF FOR PRODUCTION
if __name__ == "__main__":
	app.run('127.0.0.1', 5000, debug = True)