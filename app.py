
from flask import Flask, render_template, request, redirect, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from datetime import date

app = Flask(__name__)
app.secret_key = 'supersecret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your_email@gmail.com'
app.config['MAIL_PASSWORD'] = 'your_password'
mail = Mail(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    subject = db.Column(db.String(50))
    date = db.Column(db.String(20))
    status = db.Column(db.String(10))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['POST','GET'])
def register():
    if request.method == 'POST':
        new_user = User(
            name=request.form['name'],
            email=request.form['email'],
            password=request.form['password']
        )
        db.session.add(new_user)
        db.session.commit()
        return redirect('/login')
    return render_template('register.html')

@app.route('/login', methods=['POST','GET'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form['email'], password=request.form['password']).first()
        if user:
            session['user_id'] = user.id
            return redirect('/dashboard')
        else:
            flash("Invalid Credentials")
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' in session:
        return render_template('dashboard.html')
    return redirect('/login')

@app.route('/add_attendance', methods=['POST','GET'])
def add_attendance():
    if 'user_id' not in session:
        return redirect('/login')
    if request.method == 'POST':
        new_att = Attendance(
            user_id=session['user_id'],
            subject=request.form['subject'],
            date=str(date.today()),
            status=request.form['status']
        )
        db.session.add(new_att)
        db.session.commit()
        check_attendance_percentage(session['user_id'])
        return redirect('/dashboard')
    return render_template('add_attendance.html')

@app.route('/report')
def report():
    if 'user_id' not in session:
        return redirect('/login')
    records = Attendance.query.filter_by(user_id=session['user_id']).all()
    present = sum(1 for r in records if r.status == 'Present')
    total = len(records)
    percent = (present/total)*100 if total else 0
    return render_template('report.html', records=records, percent=percent)

def check_attendance_percentage(user_id):
    records = Attendance.query.filter_by(user_id=user_id).all()
    present = sum(1 for r in records if r.status == 'Present')
    total = len(records)
    if total > 0:
        percent = (present/total)*100
        if percent < 75:
            user = User.query.get(user_id)
            send_email_alert(user.email, percent)

def send_email_alert(email, percent):
    msg = Message('⚠️ Attendance Alert!',
                  sender='your_email@gmail.com',
                  recipients=[email])
    msg.body = f'Your attendance is {percent:.2f}%, which is below the required 75%. Please attend classes regularly!'
    mail.send(msg)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)

