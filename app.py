from flask import Flask, render_template, request, session, redirect, flash, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail , Message
from datetime import datetime
from random import randrange
from itsdangerous import URLSafeTimedSerializer, SignatureExpired
import werkzeug
import sqlite3
#from werkzeug import secure_filename
import json
import math
import os
with open("package.json","r") as c:
    params=json.load(c)["params"]

db_path=os.path.join(os.path.dirname(__file__))
db_uri='sqlite:///'+ os.path.join(db_path, 'blogdbfile.sqlite')

app=Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] =db_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False
db=SQLAlchemy(app)
app.secret_key = 'super-secret-key'


''' yeh mail send krny wala content hain '''
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT='465',
    MAIL_USE_SSL=True,
    MAIL_USE_TLS=False,
    MAIL_USERNAME=params['username'],
    MAIL_PASSWORD=params['mailpass']
)
mail=Mail(app)
s = URLSafeTimedSerializer('Thisisasecret!')
class Contacts(db.Model):
    '''sno, name,email, phone_num, msg,date '''
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255),  nullable=False)
    email = db.Column(db.String(255),  nullable=False)
    phone_num = db.Column(db.String(255),  nullable=False)
    msg = db.Column(db.String(255),  nullable=False)
    date = db.Column(db.String(12),   nullable=True )
class Posts(db.Model):
    '''sno, name,email, phone_num, msg,date '''
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255),  nullable=False)
    tagline = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String(255),  nullable=False)
    content  = db.Column(db.String(255),  nullable=False)
    img_file = db.Column(db.String(255), nullable=True)
    date = db.Column(db.String(12),   nullable=True )
class Signup(db.Model):
    '''sno, name,email, username, password, repeat-password'''
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255),  nullable=False)
    email = db.Column(db.String(255),  nullable=False)
    username = db.Column(db.String(255),  nullable=False)
    password = db.Column(db.String(255),  nullable=False)
    repeat_password = db.Column(db.String(12),   nullable=True )
    code = db.Column(db.Integer,   nullable=True )
db.create_all()

@app.route('/')
def home():
    posts=Posts.query.filter_by().all()
    last= math.ceil(len(posts)/int(params['no_of_posts']))
    page= request.args.get('page')
    if(not str(page).isnumeric()):
        page=1
    page=int(page)
    posts=posts[(page-1)*int(params['no_of_posts']): (page-1)*int(params['no_of_posts'])+ int(params['no_of_posts'])]
    if(page==1):
        prev="#"
        next="/?page="+str(page+1)
    elif(page==last):
        prev="/?page="+str(page-1)
        next="#"
    else:
        prev = "/?page=" + str(page - 1)
        next = "/?page=" + str(page + 1)
    return render_template("index.html", params=params, posts=posts, prev=prev, next=next)

@app.route('/about')
def about():
    return render_template("about.html", params=params)

@app.route('/dashboard' , methods=["GET", "POST"])
def dashboard():
    if 'adm' in session and session['adm'] == params['admin_user']:
        posts=Posts.query.all()
        return render_template("dashboard.html", params=params, posts=posts)
    if(request.method=='POST'):
        username=request.form.get('username')
        password = request.form.get('password')
        if(username== params['admin_user'] and password==params['admin_password']):
            session['adm']=username
            posts = Posts.query.all()
            return render_template("dashboard.html", params=params, posts=posts)

    return render_template("adminlogin.html", params=params)

@app.route("/edit/<string:sno>", methods = ['GET', 'POST'])
def edit(sno):
    if ('adm' in session and session['adm'] == params['admin_user']):
        if request.method == 'POST':
            box_title = request.form.get('title')
            tline = request.form.get('tagline')
            slug = request.form.get('slug')
            content = request.form.get('content')
            img_file = request.form.get('img_file')
            date = datetime.now()

            if sno=='0':
                post = Posts(title=box_title, slug=slug, content=content, tagline=tline, img_file=img_file, date=date)
                db.session.add(post)
                db.session.commit()
            else:
                post = Posts.query.filter_by(sno=sno).first()
                post.title = box_title
                post.slug = slug
                post.content = content
                post.tagline = tline
                post.img_file = img_file
                post.date = date
                db.session.commit()
                return redirect('/edit/'+sno)
        post = Posts.query.filter_by(sno=sno).first()
        return render_template('edit.html', params=params, post=post, sno=sno)

@app.route('/delete/<string:sno>', methods=["GET", "POST"])
def delete(sno):
    if 'adm' in session and session['adm'] == params['admin_user']:
        post=Posts.query.filter_by(sno=sno).first()
        db.session.delete(post)
        db.session.commit()
    return redirect('/dashboard')

@app.route('/logout')
def logout():
    session.pop('adm')
    return redirect("/dashboard")

@app.route('/uploader' , methods=[ "GET", "POST"])
def uploader():
    if 'adm' in session and session['adm'] == params['admin_user']:
        if request.method=="POST":
            f=request.files['file1']
        #    f.save(os.path.join(app.config['UPLOAD_FOLDER'] , secure_filename(f.filename)))
            return "Uploaded Successfully"

@app.route('/post/<string:post_slug>', methods=["GET"])
def post_route(post_slug):
    post = Posts.query.filter_by(slug=post_slug).first()
    return render_template("post.html", params=params, post=post)

@app.route('/contact' , methods=[ "GET", "POST"])
def contact():
    if(request.method=='POST'):
        '''Add Entry to Daatbase'''
        name= request.form.get('name')
        email= request.form.get('email')
        phone= request.form.get('phone')
        massage= request.form.get('massage')
        entry= Contacts(name=name, email=email, phone_num=phone,msg=massage, date=datetime.now())
        db.session.add(entry)
        db.session.commit()
        ''' this content comment  yeh mail send krny wala '''
        mail.send_message('New massage from ' + name ,
                          sender=email,
                          #recipients=[email, params['username']],
                          recipients=[params['username']],
                          body=massage+ "\n"+ phone +"\n"+ email
                          )

    return render_template("contact.html",params=params)

@app.route('/signup' , methods=["GET","POST"])
def signup():
    if(request.method=='POST'):
        num=''
        fname=request.form.get('name')
        email=request.form.get('email')
        uname = request.form.get('username')
        password=request.form.get('pass')
        rpassword=request.form.get('repeat-pass')
        if(password==rpassword):
            mass="Click The Below Link For login and Activate Your Account "
            #mas=randrange(65656, 78678, 6)
            #num=str(mas)
            token = s.dumps(email, salt='email-confirm')
            link = url_for('confirm_email', token=num, _external=True)
            ''' this content comment  yeh mail send krny wala '''

            mail.send_message('New massage from ' + fname,
                              sender=params['username'],
                              recipients=[email],
                              body= mass + "\n" + link
                              )
            flash("Plz check your Email Activition code send osn your mail id ")
            entry = Signup(name=fname, email=email, username=uname, password=password, repeat_password=rpassword, code=token)
            db.session.add(entry)
            db.session.commit()
        else:
           flash("Passwords are not same!")
    return render_template("signup.html", params=params)

@app.route('/confirm_email/<string:token>')
def Verify(token):
    try:
        email = s.loads(token, salt='email-confirm', max_age=36000000000)
    except SignatureExpired:
        return '<h1>The token is expired!</h1>'
    return '<h1>The token works!</h1>'

@app.route('/login' , methods=["GET","POST"])
def login():
    buname = 0
    bemail = 0
    bpass = 0
    if request.method=="POST":
        name = request.form.get('name')
        pas = request.form.get('pass')
        signup = Signup.query.filter_by(password=pas).all()
        for s in signup:
            if (name == s.username):
                buname = 1
            if (name == s.email):
                bemail = 1
            if (pas == s.password):
                bpass = 1
                snum=s.sno
        if bpass == 1:
           if (buname == 1 or bemail == 1):
               session['loginuser']=snum
               #sn=session['loginuser']
               flash("Successfully Login!")
               return render_template("login.html", params=params,  snum=snum)
        else:
            flash("Your Username/Email or Password Incorrect!")
            return render_template("login.html", params=params)
    else:
        return render_template("login.html", params=params)

@app.route('/userdashboard' , methods=["GET","POST"])
def userdashboard():
    if ('loginuser' in session):
        snum=session['loginuser']
        if (request.method == 'POST'):
            fname = request.form.get('name')
            email = request.form.get('email')
            uname = request.form.get('username')
            cpassword = request.form.get('cpass')
            password = request.form.get('pass')
            rpassword = request.form.get('repeat-pass')
            signup= Signup.query.filter_by(sno=snum).first()
            if(cpassword==signup.password):
                signup.name=fname
                signup.email=email
                signup.username = uname
                signup.password=password
                signup.repeat_password=rpassword
                db.session.commit()
                return redirect('/userdashboard')
            else:
                return "Old Password is Incorrect!"
        else:
            signup = Signup.query.filter_by(sno=snum).first()
            return render_template('userdashboard.html', params=params, signup=signup, sn=snum)
    return login()

@app.route('/userlogout')
def userlogout():
    session.pop('loginuser')
    return login()

if __name__=="__main__":
 app.run(debug=True)
