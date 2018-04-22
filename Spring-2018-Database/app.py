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
            session['ID'] = ID
            session['userType'] = userType
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

    if userType == 'customer':
        return render_template('customer_home.html', ID=ID, userType=userType)
    elif userType == 'booking_agent':
        return render_template('agent_home.html', ID=ID, userType=userType)
    elif userType == 'airline_staff':
        return render_template('staff_home.html', ID=ID, userType=userType)
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
    session.pop('userType')
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


		
app.secret_key = 'some key that you will never guess'
#Run the app on localhost port 5000
#debug = True -> you don't have to restart flask
#for changes to go through, TURN OFF FOR PRODUCTION
if __name__ == "__main__":
	app.run('127.0.0.1', 5000, debug = True)