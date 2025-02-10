from flask import Flask, render_template, render_template_string, request, jsonify, redirect, url_for
from flask_mysqldb import MySQL
from joblib import load

import numpy as np

app = Flask(__name__)

app.config['MYSQL_USER'] = 'wanas'
app.config['MYSQL_PASSWORD'] = '123'
app.config['MYSQL_HOST'] = '127.0.0.1'
app.config['MYSQL_DB'] = 'bloodseeker_db'

mysql = MySQL(app)

otherModel = load('otherRFmodel.joblib')
otherScaler = load('otherScaler.joblib')
model = load('RFmodel.joblib')
scaler = load('scaler.joblib')

@app.route('/')
def home():
    return render_template('page/index.html')

@app.route('/otherModel')
def otherhome():
    return render_template('page/otherModel.html')

@app.route('/aboutAnemia')
def about_anemia():
    return render_template('page/aboutAnemia.html')

@app.route('/productPage')
def products():
    return render_template('page/productPage.html')

@app.route('/adminLogin')
def adminLogin():
    return render_template('page/adminInterface/adminLogin.html')

@app.route('/prediction', methods=['POST'])
def predict():
    gender = request.form['Gender']
    hb = request.form['Hb']
    mch = request.form['MCH']
    mchc = request.form['MCHC']
    mcv = request.form['MCV']
    age = request.form['Age']
    country = request.form['Country']
    income = request.form['Income']
    race = request.form['Race']
    profession = request.form['Profession']

    #Model Use Data
    array = np.array([[gender, hb, mch, mchc, mcv]])

    array_scaled = scaler.transform(array)
    
    pred = model.predict(array_scaled)

    result = str(pred[0])

    #Storing the data to the database
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO blood_data (gender, hb, mch, mchc, mcv, age, country, income, race, profession, result) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                , (gender, hb, mch, mchc, mcv, age, country, income, race, profession, result))
    mysql.connection.commit()

    #if 0 = no anemia, if 1 = have anemia
    if pred[0] == 0:
        something = "No anemia"
    elif pred[0] == 1:
        something = "Have anemia"
    else:
        something = "Unknown prediction"

    print("Prediction result:", pred)
    print("Input Data:", array)

    html_template = '''
            <html>
                <head>
                    <script src="https://cdn.jsdelivr.net/npm/sweetalert2@11"></script>
                </head>
                <body>
                    <script type="text/javascript">
                        Swal.fire({
                            title: 'Prediction Result',
                            text: {{ something | tojson }},
                            icon: 'info',
                            confirmButtonText: 'OK',
                        }).then(() => {
                            window.location.href = "/";
                        });
                    </script>
                </body>
            </html>
        '''

    return render_template_string(html_template, something = something)

# Route to add user
@app.route('/login', methods=['POST'])
def logiAuth():
    name = request.form['name']
    password = request.form['password']

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM users WHERE name = %s", [name])
    user = cur.fetchone()  # Fetch the user by name

    if user:
        DBpassword = user[3]

        if DBpassword == password:
            return render_template('page/adminInterface/adminMenu.html')
        else:
            # Password is incorrect
            return render_template_string('''
            <html>
                <head>
                    <script type="text/javascript">
                        alert("Error");
                        window.location.href = "/adminLogin";
                    </script>
                </head>
            </html>
            ''')
    else:
        return render_template_string('''
        <html>
            <head>
                <script type="text/javascript">
                    alert("Error");
                    window.location.href = "/adminLogin";
                </script>
            </head>
        </html>
    ''')

@app.route('/data')
def get_data():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM blood_data")
    rows = cur.fetchall()

    # Get column names
    column_names = [desc[0] for desc in cur.description]

    # Convert rows to a list of dictionaries
    data = [dict(zip(column_names, row)) for row in rows]

    return jsonify(data)

if __name__ == "__main__":
    app.run(debug=True)