# def flightSearchValidation(request):
#     return (request.form['departure_city'] or request.form['departure_airport']) and\
#         (request.form['destination_city'] or request.form['destination_airport']) and\
#         (request.form['date'])

def flightSearchValidation(request):
    return request.form['departure_airport'] and request.form['arrival_airport'] and\
        request.form['departure_date']

# def flightSearchQuery(form):
#     query = 'SELECT * FROM flight WHERE date = %s' % form['date']
#     for key, value in form.items():
#         if value and key != 'date':
#             query += ' and ' + key + ' = %s'
#             query = query % value
#     return query

def flightSearchQuery(request):
    return 'SELECT * FROM flight WHERE departure_time LIKE %s and departure_airport = %s and arrival_airport = %s',\
    (request.form['departure_date'] + '%', request.form['departure_airport'], request.form['arrival_airport'])
    