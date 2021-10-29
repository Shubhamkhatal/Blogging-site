from datetime import datetime
from flask import Flask,render_template,request,session,redirect
from flask_mail import Mail, Message
from itsdangerous import URLSafeSerializer as serializer
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
mail=Mail(app)
app.config['SQLALCHEMY_DATABASE_URI']='postgresql://postgres:'password_of_database'@localhost/website'
app.secret_key='super-secret-key'
db = SQLAlchemy(app)
app.config['SESSION_SQLALCHEMY_TABLE'] = 'sessions'
app.config['UPLOAD_FOLDER'] = "..//static//img//post//"
s = serializer('secret')

class Registration(db.Model):
    id = db.Column(db.Integer,primary_key=True,autoincrement=True)
    first_name = db.Column(db.String(75),nullable=False)
    middle_name = db.Column(db.String(75),nullable=False)
    last_name = db.Column(db.String(75),nullable=False)
    email = db.Column(db.String(75),nullable=False)
    phone_number = db.Column(db.Integer,nullable=False)
    password = db.Column(db.String(75),nullable=False)
    isactive = db.Column(db.Boolean, default=False, nullable=False)

class Posts(db.Model):
    id = db.Column(db.Integer,primary_key=True,autoincrement=True)
    title = db.Column(db.String(80),nullable = False)
    tagline = db.Column(db.String(1000), nullable=False)
    slug = db.Column(db.String(80), nullable=False)
    content = db.Column(db.String(10000), nullable=False)
    creator = db.Column(db.ForeignKey('registration.id'),nullable=False)
    createtime = db.Column(db.DateTime())
    updatetime = db.Column(db.DateTime())
    isactive = db.Column(db.Boolean, default=False, nullable=False)

db.create_all()

def mail(receiver,message1):
    app.config['MAIL_SERVER']='smtp.gmail.com'
    app.config['MAIL_PORT'] = 465
    app.config['MAIL_USERNAME'] = 'yourmailid@gmail.com'
    app.config['MAIL_PASSWORD'] = 'Password'
    app.config['MAIL_USE_TLS'] = False
    app.config['MAIL_USE_SSL'] = True
    mail = Mail(app)
    msg = Message('Hello', sender =  'yourmailid@gmail.com', recipients = [receiver])
    msg.body = message1
    mail.send(msg)
    return redirect("/signin")


@app.route('/search')
def signin():
    query = request.args.get('query')
    query = "".join(query.split())

    no_post  = None
    try :
        posts = Posts.query.filter(Posts.title.match(f"{query}%")).all()
        print(len(posts))
        if len(posts) == 0:
            no_post = True
    except Exception as e:
        no_post = True
    return render_template('home.html',posts=posts,no_post=no_post)



@app.route('/')
def home():
    posts = Posts.query.order_by(Posts.updatetime.desc()).all()
    posted_by = Registration.query.filter_by().all()
    no_post = None
    no_of_posts = 3
    last = len(posts)/no_of_posts
    print(last)
    if last%no_of_posts >= 3:
        last = int(last)
    else :
        last = int(last)+1
    page = request.args.get('page')
    if(not str(page).isnumeric()):
        page = 1
    page = int(page)
    posts = posts[(page-1)*no_of_posts : (page-1)*no_of_posts+no_of_posts]
    if (page == 1):
        prev = "#"
        next = "/?page="+str(page+1)
    elif (page==last):
        prev = "/?page="+str(page-1)
        next = "#"
    else:
        prev = "/?page="+str(page-1)
        next = "/?page="+str(page+1)
    return render_template('home.html',posts=posts,prev=prev,next=next,page=page,last=last,no_post=no_post)


@app.route('/dashboard/<data>/')
def test(data):
    user = s.loads(data)
    if "user" in session:
            mail = session["user"]
            post = Posts.query.filter_by(creator = user['id']).all()
            return render_template('dashboard.html',user=user,post=post)
    else :
        return redirect('/')

@app.route('/signin',methods=['GET','POST'])
def index():
    error = None
    if "user" in session:
            mail = session["user"]
            user = Registration.query.filter_by(email=mail).first()
            data = s.dumps({"id":user.id,"fn":user.first_name,"mn":user.middle_name,"ln":user.last_name})
            return redirect(f"/dashboard/{data}/")
    
    if (request.method=='POST'):
            mail = request.form.get('email').lower()
            password = request.form.get('password')
            try :
                user = Registration.query.filter_by(email=mail).first()
                if user.password == password:
                    session['user'] = mail
                    data = s.dumps({"id":user.id,"fn":user.first_name,"mn":user.middle_name,"ln":user.last_name})
                    return redirect(f"/dashboard/{data}/")
                else :
                    error ="Incorrect Email id or Password"
            except Exception as e:
                error ="Incorrect Email id or Password"
    return render_template('index.html',error=error)

    

@app.route('/register',methods=['GET','POST'])
def register():
    error =None
    msg =None
    if (request.method=='POST'):
        first_name = request.form.get('first-name')
        middle_name = request.form.get('middle-name')
        last_name = request.form.get('last-name')
        email = request.form.get('email-address').lower()
        phone_number = request.form.get('phone-number')
        password = request.form.get('password')

        user = Registration.query.filter_by(email=email).first()
        try :
            if user != None:
                error =  "Your are already Registered"
            else:
                a = Registration(first_name=first_name,last_name=last_name,middle_name=middle_name,email=email,phone_number=phone_number,password =password,isactive=True)
                db.session.add(a)
                db.session.commit()
                msg = "You are successfully registered"
                try:
                    mail(email,msg)
                except:
                    msg = "You are successfully registered"
        except Exception as e:
            error = "Sorry we are unable to register you at this moment"
    return render_template('register.html',error = error,msg=msg)


@app.route("/post/<string:sno>/", methods=['GET','POST'])
def edit(sno):
    if 'user' in session :
        user = session['user']
        if request.method == 'POST':
                title = request.form.get('title')
                tagline = request.form.get('tagline')
                content = request.form.get('content')
                date = datetime.now()
                user = Registration.query.filter_by(email=user).first()
                slug = str(user.id) +  str(title)
                if sno == '0':
                    slug = s.dumps(slug)
                    post = Posts(title=title,tagline=tagline,slug=slug,content=content,creator = user.id,createtime=date,updatetime=date,isactive=True)
                    db.session.add(post)
                    db.session.commit()
                    return redirect('/signin')
                else:
                    post =  Posts.query.filter_by(slug=sno).first()
                    post.title = title
                    post.tagline = tagline
                    post.content = content
                    post.updatetime = date
                    db.session.commit()
                    return redirect("/signin")
        post = Posts.query.filter_by(slug=sno).first()
        return render_template('posts.html',post=post,sno=sno)
    else :
        return redirect('/signin')

@app.route('/view/<string:slug>')
def view(slug):
    post = Posts.query.filter_by(slug=slug).first()
    creator = Registration.query.filter_by(id=post.creator).first()
    contact = s.dumps(creator.id)
    return render_template('view.html',post=post,creator=creator,contact=contact)

@app.route('/contact_with_author/<string:slug>',methods=['GET','POST'])
def contact_with_author(slug):
    if request.method == 'POST':
        slug = s.loads(slug)
        user = Registration.query.filter_by(id=slug).first()
        name = request.form.get('name')
        email = request.form.get('email')
        phno = request.form.get('phone_num')
        message = request.form.get('msg')
        message1= str("You Have message from the :-" +name +" Email :-"+email +" phone number :-"+phno+" message :-"+message)
        receiver = user.email
        mail(receiver,message1)
        return redirect("/")
    slug1 = slug
    slug = s.loads(slug)
    user = Registration.query.filter_by(id=slug).first()
    return render_template('contact_with_author.html',user=user,slug1 = slug1)
   

@app.route('/logout')
def logout():
    session.pop("user")
    return redirect('/')

@app.route('/delete/<string:slug>')
def delete(slug):
    post = Posts.query.filter_by(slug=slug).first()
    db.session.delete(post)
    db.session.commit()
    return redirect('/signin')

app.run(debug=True)
