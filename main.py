import random
from sqlalchemy import desc
import smtplib
from werkzeug.utils import secure_filename
import datetime
from datetime import timedelta
import os
from sqlalchemy.sql.expression import func
from flask_login import login_user, LoginManager, login_required, current_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
import bleach
from models import User,Blog,Collabration,LikedBlog,Follower,Message,Interest,Userscomment,app,db
from datetime import timedelta
from flask import abort, jsonify
from flask import render_template, request, redirect, url_for, flash
current_year = datetime.datetime.now().year

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = '/login'
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
PERMANENT_SESSION_LIFETIME = timedelta(seconds=28800)


@app.route("/addoremovelike/<int:id>", methods=["POST"])
@login_required
def addoremovelike(id):
    #get the current user
    user_id = current_user.id
    try:
        #query all the specifblog to liked or remove like
        blog = Blog.query.filter_by(id=id).first()
        #check if the current user have already liked that blog
        liked_blog = LikedBlog.query.filter_by(user_id=current_user.id, blog_id=id).first()
        #check if the blogs exist
        if blog:
            #check if the current user is not the owner of the blog
            if blog.user_id != user_id:
                    #check if not the user has already liked that post
                if liked_blog:
                    db.session.delete(liked_blog)
                    # subtract the like of the user
                    blog.like -= 1
                    # commit changes to the database
                    db.session.commit()
                    response = {"message": "Like Removed"}
                    return jsonify(response), 201

                else:
                    #if the user has already liked tha post remove the user from the liked_blogs
                    # add like
                    blog.like += 1
                    # add the user to user who have already liked that post
                    blog.liking_users.append(current_user)
                    # commit the changes to the database
                    db.session.commit()
                    response = {"message": "like added"}
                    return jsonify(response), 200


            else:
                #if the owner of the blogs is the same as the user who is trying to like the post return a 403 response to js
                response = {"message": "You can't like your own blog"}
                return jsonify(response), 403
        else:
            #if the blog doesn;t exit return a 404 response
            response = {"message": "Blog is not found"}
            return jsonify(response), 404
    except Exception as e:
        response = {"message": f"Internal server error: {str(e)}"}
        print(e)  # Print the exception for debugging purposes
        return jsonify(response), 500


@app.route("/topblogs", methods=["GET"])
def TopBlogs():
    #query the current user
    user = User.query.filter_by(id=current_user.id).first()
    #adding pagination
    page = request.args.get("page", default=1, type=int)
    per_page = 10
    offset = (page - 1) * per_page
    #query 30 top liked blogs
    blogs = Blog.query.filter(Blog.user_id != current_user.id).order_by(Blog.like.desc()).offset(offset).limit(per_page).all()


    total_pages = 3

    return render_template("topblogs.html", blogs=blogs, page=page, user=user, total_pages=total_pages)



@app.route("/accept/<int:id>/<int:userid>", methods=["POST"])
@login_required
def accept(id, userid):
    #query the project
    project = Collabration.query.get(id)
    #if the project exist
    if project:
        if current_user.id == project.user_id:
            user = User.query.get(userid)
            if user:
                #add th user to the team
                project.members.append(user)
                #query the interest of that user
                interest = Interest.query.filter_by(user_id=userid).first()
                #remove the user since they are on the team
                db.session.delete(interest)
                #comomit the changes to the database
                db.session.commit()
                response = {"message": "User added to the team successfully"}
                return jsonify(response), 200
            else:
                response = {"message": "User not found"}
                return jsonify(response), 404
        else:
            response = {"message": "Current user is not the project owner"}
            return jsonify(response), 403
    else:
        response = {"message": "Project not found"}
        return jsonify(response), 404


@app.route("/follow/<int:id>", methods=["POST"])
@login_required
def addorremoverfollowing(id):
    try:
        #query the current user
        user_id = current_user.id
        #check if they are trying to follow themselve
        if id == user_id:
            # return a 400 error with a message to js fetch function
            response = {"message": "You can't follow yourself"}
            return jsonify(response), 400

        # Check if the follow relationship already exists
        existing_follow = Follower.query.filter_by(user_id=id, follower_id=user_id).first()
        if existing_follow:

            db.session.delete(existing_follow)
            db.session.commit()
            response = {"message": "You are already following this user"}
            return jsonify(response), 201

        # Add new follow relationship
        new_follower = Follower(user_id=id, follower_id=user_id)
        #add the new follower to the databse
        db.session.add(new_follower)
        #commit the changes to the datbase
        db.session.commit()

        response = {"message": "Follower added successfully."}
        return jsonify(response), 200

    except Exception as e:
        # Log the error and return an error response
        app.logger.error(f"An error occurred: {str(e)}")
        response = {"message": "An error occurred"}
        return jsonify(response), 500


@app.route("/interestinmyproject/<int:id>", methods=["GET"])
@login_required
def specficinterestinmyproject(id):
    #query all the project
    project = Collabration.query.filter_by(id=id).first()
    #query the current user
    user = User.query.filter_by(id=current_user.id).first()
    #query the team of the project
    Team = Collabration.query.filter_by(id=id).first()

    team = Team.members
    if project:
        if project.user_id == current_user.id:
            all_interest = project.interests
            return render_template("interestinmyproject.html", interests=all_interest, project=project, user=user, team=team)
    else:
         return jsonify("NO project was found!!")


@app.route("/myfollowers", methods=["GET", "POST"])
@login_required
def myfollowers():
    page = request.args.get("page", default=1, type=int)
    per_page = 10
    offset = (page - 1) * per_page
    #query all the user that are followers of the current user
    followers = Follower.query.filter_by(user_id=current_user.id).offset(offset).limit(per_page).all()
    followers = [follower.follower for follower in followers]
    #query the curent user
    user = User.query.filter_by(id=current_user.id).first()

    total_records = User.query.count()

    total_pages = (total_records // per_page) + (1 if total_records % per_page > 0 else 0)

    return render_template("myfollowers.html", user=user, page=page, total_pages=total_pages, followers=followers)



@app.route("/myfollowing", methods=["GET", "POST"])
@login_required
def myfollowing():
    page = request.args.get("page", default=1, type=int)
    per_page = 10
    offset = (page - 1) * per_page
    user = User.query.get(current_user.id)
    #query all the user the current user follows
    following = Follower.query.filter_by(follower_id=current_user.id).offset(offset).limit(per_page).all()

    #fget the count of the query
    total_records = User.query.count()

    total_pages = (total_records // per_page) + (1 if total_records % per_page > 0 else 0)


    return render_template("myfollowing.html", allfollowing=following, user=user, page=page, total_pages=total_pages)




@app.route("/", methods=["GET", "POST"])
def home():
    #query all the projects
    allcollaboration = Collabration.query.all()
    #call the checkdue date function to see if proijects have passed their deadline
    # checkdue_date(allcollaboration)
    #check if th user is authenticated
    if current_user.is_authenticated:
        #query 5 random users
        random_users = User.query.filter(User.id != current_user.id).order_by(func.random()).limit(5).all()
        #query the current user
        user = User.query.filter_by(id=current_user.id).first()
        #query all the projects with exception of all the project that are made by the current user and order by decreasing project id
        collabs = Collabration.query.filter(Collabration.user_id != current_user.id).order_by(Collabration.id.desc()).limit(5)
        #query 5 blogs that are order baded on their blog id decreasingly
        blog = Blog.query.filter(Blog.user_id != current_user.id).order_by(Blog.id.desc()).limit(5)

        is_logged_in = current_user.is_authenticated
        return render_template("index.html", is_logged_in=is_logged_in, user=user, collabs=collabs, blogs=blog, random_users=random_users)
    else:
        return render_template("index.html")




@app.route("/deleteinterest/<int:id>", methods=["POST"])
def deleteinterest(id):
    #query the project
    project = Collabration.query.filter_by(id=id).first()
    #get all the interest in that project
    interests = project.interests
    #check if the project exist
    if not project:
        return jsonify({"message": "Project not found"}), 404
    #iterate through all the interest in that project
    for interest in interests:

        if interest.user_id == current_user.id:
            db.session.delete(interest)
            db.session.commit()
            response = {"message": "Interest has been deleted successfully."}
            return jsonify(response), 200

        else:
            response = {"message": "Interest has not been deleted try again!"}
            return jsonify(response), 400

    response = {"message": "Interest has not been deleted try again!"}
    return jsonify(response), 400

@app.route("/forgotpasswordloggedin", methods=["GET", "POST"])
@login_required
def forgetpassword():
    user = User.query.filter_by(id=current_user.id).first()
    user_email = user.email
    if request.method == "POST":
        mailuser = 'zgetnet24@gmail.com'
        mailpasswd = 'Scooponset1'
        fromaddr = 'zgetnet24@gmail.com'
        toaddrs = "zelalem328@gmail.com"
        msg = 'Subject: Test Email\n\nThis is a test email from Python.'
        if user:
            try:
                server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
                server.login(mailuser, mailpasswd)
                server.sendmail(fromaddr, toaddrs, msg)
                print("Email sent successfully!")
            except Exception as e:
                print(f"An error occurred: {e}")
            finally:
                server.quit()
        return redirect(url_for('home'))
    else:
        return render_template("forgetpassword.html", email=user_email, user=user)





@app.route("/forgotpasswordloggedout", methods=["GET", "POST"])
def forgetpasswordloggedout():
    user = []
    if request.method == "POST":
        email = request.form["email"]
        user = User.query.filter_by(email=email).first()
        mailuser = 'zgetnet24@gmail.com'
        mailpasswd = 'Scooponset1'
        fromaddr = 'zgetnet24@gmail.com'
        toaddrs = "zelalem328@gmail.com"
        msg = 'Subject: Test Email\n\nThis is a test email from Python.'
        if user:
            try:
                server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
                server.login(mailuser, mailpasswd)
                server.sendmail(fromaddr, toaddrs, msg)
                print("Email sent successfully!")
            except Exception as e:
                print(f"An error occurred: {e}")
            finally:
                server.quit()
        return redirect(url_for('home'))
    else:
        return render_template("forgetpasswordloggedout.html",  user=user)


@app.route("/emailsent", methods=["GET"])
def emailsent():
    return render_template("emailsent.html")


@app.route("/followingblogs", methods=["POST", "GET"])
@login_required
def followingblogs():
    page = request.args.get("page", default=1, type=int)
    per_page = 10
    offset = (page - 1) * per_page
    user = User.query.filter_by(id=current_user.id).first()
    # Get the current user
    user = db.session.get(User, int(current_user.id))

    # Get the IDs of the users the current user follows
    following_users = [follower.followed_user for follower in user.following]

    # Get the blogs of the following users
    following_blogs = (
        Blog.query.filter(Blog.user_id.in_([following_user.id for following_user in following_users]))
        .order_by(desc(Blog.date))
        .offset(offset)
        .limit(per_page)
        .all()
    )
    total_pages = 0
    for blog in following_blogs:

        total_records = Blog.query.filter(
        Blog.user_id.in_([following_user.id for following_user in following_users])).count()
        total_pages = (total_records // per_page) + (1 if total_records % per_page > 0 else 0)

    return render_template(
        "following_blogs.html", blogs=following_blogs, page=page, total_pages=total_pages, user=user
    )



@app.route("/allcollabration", methods=["GET", "POST"])
@login_required
def allcollbration():
    user = User.query.filter_by(id=current_user.id).first()
    page = request.args.get("page", default=1, type=int)
    per_page = 10
    offset = (page - 1) * per_page
    #query all the results excluding all the projects which the owner is the current user
    collabrations = Collabration.query.filter(Collabration.user_id != current_user.id).offset(offset).limit(per_page).all()

    #Get the number of pages
    total_records = Collabration.query.count()

    total_pages = (total_records // per_page) + (1 if total_records % per_page > 0 else 0)

    return render_template("collabration.html", collabrations=collabrations, page=page, total_pages=total_pages,
                          user=user)











@app.route("/otherfollowing/<int:id>", methods=["GET","POST"])
def otherfollowing(id):
    page = request.args.get("page", default=1, type=int)
    per_page = 10
    offset = (page - 1) * per_page
    user = User.query.get(current_user.id)
    following = Follower.query.filter_by(follower_id=id).offset(offset).limit(per_page).all()
    total_records = User.query.count()

    total_pages = (total_records // per_page) + (1 if total_records % per_page > 0 else 0)

    return render_template("otherfollowing.html", allfollowing=following, user=user, page=page, total_pages=total_pages)




@app.route("/otherfollowers/<int:id>", methods=["GET", "POST"])
def otherfollowers(id):
    #query the user
    user = User.query.filter_by(id=id).first()
    #query from from the follower table
    followers = Follower.query.filter_by(user_id=id).all()
    #query all the followers of that user
    followers = [follower.follower for follower in followers]
    #render the page
    return render_template("otherfollowers.html", allfollowers=followers, user=user)


@app.route("/changepassword", methods=["GET", "POST"])
@login_required
def changepassword():
    #query the current user
    user = User.query.filter_by(id=current_user.id).first()
    if request.method == "POST":
        user = User.query.filter_by(id=current_user.id).first()
        print(user.password)
        #Get the current password from form
        current_password = request.form["password"]
        #check if it is correct
        password = user.password
        if not check_password_hash(password, current_password):
            flash('Incorrect password, please try again.')
            return redirect(url_for('changepassword'))
        #get the new password from the form
        new_password = request.form["newpassword"]
        #get the confirmation passsword from the form
        confirm_password = request.form["confirm-password"]
        #check if new_password and confirm_password are not the same
        if new_password != confirm_password:
            flash("Confirmation password is not the same as the password you entered.")
            return redirect(url_for('changepassword'))
        #hash the new password
        hash_and_salted_password = generate_password_hash(
            new_password,
            method='pbkdf2:sha256',
            salt_length=8
        )
        #change the old password with the new one
        user.password = hash_and_salted_password
        #commit the changes to the database
        db.session.commit()

        return redirect(url_for('home'))

    return render_template("changepassword.html", user=user)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))







@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":
        email = bleach.clean(request.form['email'])
        password = bleach.clean(request.form['password'])
        user = User.query.filter_by(email=email).first()

        if not user:
            flash("That email does not exist, please try again.")

            return redirect(url_for('login'))

        if not check_password_hash(user.password, password):
            flash('Incorrect password, please try again.')

            return redirect(url_for('login'))
        login_user(user)


        return redirect(url_for('home'))

    return render_template("login.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    # Check if the user is already logged in
    is_logged_in = current_user.is_authenticated

    # If the request method is POST (form submission)
    if request.method == "POST":
        # Clean the form data using bleach
        email = bleach.clean(request.form['email'])
        password = bleach.clean(request.form['password'])
        confirm_password = bleach.clean(request.form['confirm-password'])
        first_name = bleach.clean(request.form['first_name'])
        last_name = bleach.clean(request.form['last_name'])
        twitter = bleach.clean(request.form['twitter'])
        github = bleach.clean(request.form['github'])
        country = bleach.clean(request.form['country'])
        city = bleach.clean(request.form['City'])
        usersage = bleach.clean(request.form['age'])
        skills = bleach.clean(request.form['skills'])
        status = bleach.clean(request.form['about_me'])
        phone_number = bleach.clean(request.form['phone_number'])
        about_me = bleach.clean(request.form["about_me"])
        portfolio = bleach.clean(request.form["previous"])
        username = bleach.clean(request.form["username"])
        employment_status = request.form['employment-status']
        education_level = request.form['education-level']

        # Set the default profile image path
        image_path = "static/images/noprofile.jpg"

        # If the user has uploaded an image
        if 'image' in request.files:
            image = request.files['image']
            ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
            # Check if the image file extension is allowed
            if image.filename.split('.')[-1].lower() in ALLOWED_EXTENSIONS:
                destination_folder = os.path.join('static', 'images')
                image_path = os.path.join('static', 'images', secure_filename(image.filename))
                image.save(image_path)

        # Check if the confirmation password matches the password
        if confirm_password != password:
            flash("Your confirmation password does not match the password")
            return redirect(url_for('signup'))

        # Check if the email is already registered
        if User.query.filter_by(email=request.form.get('email')).first() is not None:
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for('login'))

        # Check if all required fields are filled
        if not email or not password or not first_name or not last_name or not phone_number:
            flash("Please fill in all the required fields.")
            return redirect(url_for('signup'))

        # Check if the password is at least 5 characters long
        if len(password) < 5:
            flash("Password should be at least 5 characters long.")
            return redirect(url_for('signup'))

        # Hash and salt the password
        hash_and_salted_password = generate_password_hash(
            password,
            method='pbkdf2:sha256',
            salt_length=8
        )

        # Create a new user
        new_user = User(
            fname=first_name,
            lname=last_name,
            phone_number=phone_number,
            email=email,
            twitter=twitter,
            github=github,
            status=status,
            skills=skills,
            age=usersage,
            country=country,
            City=city,
            about_me=about_me,
            profile_photo=image_path,
            portfolio=portfolio,
            username=username,
            employment_status=employment_status,
            education_status=education_level,
            password=hash_and_salted_password,
        )

        # Add the new user to the database and commit the changes
        db.session.add(new_user)
        db.session.commit()

        # Log in the new user
        login_user(new_user)

        # Redirect the user to the home page
        return redirect(url_for("home"))

    # Render the signup template, passing the is_logged_in variable
    return render_template("signup.html", is_logged_in=is_logged_in)

@app.route("/contact", methods=["GET", "POST"])
def contact():
    # Get the current user
    user = User.query.filter_by(id=current_user.id).first()

    # If the request method is POST (form submission)
    if request.method == "POST":
        # Clean the form data using bleach
        name = bleach.clean(request.form["name"])
        email = bleach.clean(request.form["email"])
        phone = bleach.clean(request.form["phone"])
        message = bleach.clean(request.form["message"])

        # Create a new message
        new_message = Message(
            name=name,
            phone=phone,
            email=email,
            message=message,
        )

        # Add the new message to the database and commit the changes
        db.session.add(new_message)
        db.session.commit()
        flash("Your message has been received")
        return redirect(url_for('contact'))

    # Render the contact template, passing the is_logged_in and user variables
    else:
        is_logged_in = current_user.is_authenticated
        return render_template("contact.html", is_logged_in=is_logged_in, user=user)

@app.route("/about", methods=["GET", "POST"])
def about():
    # Check if the user is logged in
    is_logged_in = current_user.is_authenticated

    # Get the current user
    user = User.query.filter_by(id=current_user.id).first()

    # Render the about template, passing the is_logged_in, year, and user variables
    return render_template("about.html", is_logged_in=is_logged_in, year=current_year, user=user)

@app.route("/logout", methods=["GET", "POST"])
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))
@app.route("/removefollower/<int:id>", methods=["POST"])
def removefollower(id):
    follower = Follower.query.filter_by(user_id=current_user.id, follower_id=id).first()
    if follower:
        db.session.delete(follower)
        db.session.commit()
        response = {"follower removed succesfully"}
        return response, 200
    else:
        response={"There is no follower with that id"}
        return response, 404


@app.route("/allblogs")
@login_required
def allblogs():

    user = User.query.filter_by(id=current_user.id).first()
    page = request.args.get("page", default=1, type=int)
    per_page = 10
    offset = (page - 1) * per_page

    blogs = Blog.query.filter(Blog.user_id != current_user.id).order_by(Blog.date.desc(), Blog.like.desc()).offset(offset).limit(per_page).all()

    total_records = Blog.query.count()

    total_pages = (total_records // per_page) + (1 if total_records % per_page > 0 else 0)

    return render_template("allblog.html", blogs=blogs, page=page, user=user,total_pages=total_pages)

@app.route("/blogs/<id>", methods=["GET"])
@login_required
def Specficblog(id):
    """
    Renders the template for a specific blog post.

    Args:
        id (str): The unique identifier of the blog post.

    Returns:
        The rendered template for the specific blog post.
    """
    blog = Blog.query.filter_by(id=id).first()
    user = User.query.filter_by(id=blog.user_id).first()
    liked = LikedBlog.query.filter_by(user_id=current_user.id, blog_id=blog.id).first()

    return render_template("specficblog.html", blog=blog, user=user, liked=liked)


@app.route("/myblogs", methods=["GET", "POST"])
@login_required
def myblogs():
    """
    Renders the template for the user's blog posts.

    Returns:
        The rendered template for the user's blog posts.
    """
    page = request.args.get("page", default=1, type=int)
    per_page = 10
    offset = (page - 1) * per_page
    blogs = Blog.query.filter_by(user_id=current_user.id).offset(offset).limit(per_page).all()
    user = User.query.filter_by(id=current_user.id).first()

    total_records = Blog.query.count()

    total_pages = (total_records // per_page) + (1 if total_records % per_page > 0 else 0)

    return render_template("myblogs.html", user=user, page=page, total_pages=total_pages, blogs=blogs)




#
@app.route("/editblog/<id>", methods=["GET", "POST"])
@login_required
def editblog(id):
    """
    Handles the editing of a blog post.

    Args:
        id (str): The unique identifier of the blog post.

    Returns:
        The rendered template for the edit blog page or a redirect to the user's blog page.
    """
    user = User.query.filter_by(id=current_user.id).first()
    if request.method == "POST":
        title = bleach.clean(request.form['title'])
        subititle = bleach.clean(request.form['subtitle'])
        content = bleach.clean(request.form["content"])
        blog = Blog.query.filter_by(id=id)
        blog.title = title
        blog.subtitle = subititle
        blog.content = content
        db.session.commit()
        return redirect(url_for('myblogs'))
    else:
        blog = Blog.query.filter_by(id=id).first()
        return render_template("editblog.html", blog=blog, user=user)


@app.route("/myblogs/delete/<int:id>", methods=["POST"])
@login_required
def deleteblog(id):
    """
    Handles the deletion of a blog post.

    Args:
        id (int): The unique identifier of the blog post.

    Returns:
        A redirect to the user's blog page.
    """
    user = User.query.filter_by(id=current_user.id).first()
    blogs = Blog.query.filter_by(user_id=current_user.id).all()
    if blogs:
        for blog in blogs:
            if blog.id == id:
                db.session.delete(blog)
                db.session.commit()
        return redirect(url_for('myblogs'))

    else:
        return render_template("myblogs.html", user=user)
@app.route('/editprofile', methods=['GET', 'POST'])
@login_required
def editprofile():
    user = current_user
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        phone_number = request.form.get('phone_number')
        age = request.form.get('age')
        country = request.form.get('country')
        city = request.form.get('city')
        twitter = request.form.get('twitter')
        github = request.form.get('github')
        skills = request.form.get('skills')
        employment_status = request.form.get('employment_status', user.employment_status)
        education_status = request.form.get('education_level', user.education_status)

        previous = request.form.get('previous')
        about_me = request.form.get('about_me')

        # Handle profile photo upload
        if 'image' in request.files and request.files['image'].filename != '':
            image = request.files['image']
            if image and allowed_file(image.filename):
                filename = secure_filename(image.filename)
                image.save(os.path.join(app.root_path, 'static/images', filename))
                user.profile_photo = f'/static/images/{filename}'
        elif 'image2' in request.files and request.files['image2'].filename != '':
            image = request.files['image2']
            if image and allowed_file(image.filename):
                filename = secure_filename(image.filename)
                image.save(os.path.join(app.root_path, 'static/images', filename))
                user.profile_photo = f'/static/images/{filename}'
        else:
            if request.form.get('delete_photo') == 'true':
                user.profile_photo = 'static/images/noprofile.jpg'

        user.fname = first_name
        user.lname = last_name
        user.email = email
        user.phone_number = phone_number
        user.age = age
        user.country = country
        user.City = city
        user.twitter = twitter
        user.github = github
        user.skills = skills
        user.employment_status = employment_status
        user.education_status = education_status
        user.previous = previous
        user.about_me = about_me

        db.session.commit()
        flash('Your profile has been updated.', 'success')
        return redirect(url_for('myprofile'))

    return render_template('editprofile.html', user=user)

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS





@app.route("/myprofile", methods=['GET' , "POST"])
@login_required
def myprofile():
    """
    Renders the template for the user's profile page.

    Returns:
        The rendered template for the user's profile page.
    """
    userid = current_user.id
    user = User.query.filter_by(id=userid).first()
    return render_template("myprofile.html", user=user)



# This route handles the creation of a new blog post
@app.route("/newblog", methods=['GET', "POST"])
@login_required
def newblog():
    # Get the current user
    user = User.query.filter_by(id=current_user.id).first()

    # Check if the request method is POST
    if request.method == "POST":
        # Get the user's ID
        user_id = current_user.id
        # Initialize the image path to None
        image_path = None

        # Check if an image was uploaded
        if 'image' in request.files and request.files['image'].filename != '':
            image = request.files['image']
            # Define the allowed file extensions
            ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
            # Check if the file extension is allowed
            if image.filename.split('.')[-1].lower() in ALLOWED_EXTENSIONS:
                # Create the destination folder for the image
                destination_folder = os.path.join('static', 'images')
                # Set the image path
                image_path = os.path.join('static', 'images', secure_filename(image.filename))
                # Save the image to the destination folder
                image.save(image_path)

        # Create a new blog post
        new_blog = Blog(
            title=request.form.get("title"),
            content=request.form.get("content"),
            subtitle=request.form.get("subtitle"),
            user_id=user_id,
            blog_image=image_path
        )
        # Add the new blog post to the database and commit the changes
        db.session.add(new_blog)
        db.session.commit()
        # Redirect the user to the "myblogs" route
        return redirect(url_for('myblogs'))
    else:
        # Render the "newblog.html" template and pass the user object
        return render_template("newblog.html", user=user)

# This route handles the header section of the website
@app.route("/header", methods=['GET', "POST"])
def header():
    # Check if the current user is authenticated
    is_logged_in = current_user.is_authenticated
    # Render the "header.html" template and pass the is_logged_in variable
    return render_template("header.html", is_logged_in=is_logged_in)

# This route handles the interest/follow functionality
@app.route("/interest/<int:id>", methods=["POST"])
@login_required
def interest(id):
    interest = Interest.query.filter_by(user_id=current_user.id, project_id=id).first()
    if interest:
        response = {"message": "Follower added successfully."}
        return jsonify(response), 400

    # Create a new Interest object
    new_interest = Interest(
        user_id=current_user.id,
        project_id=id
    )
    # Add the new Interest to the database and commit the changes
    db.session.add(new_interest)
    db.session.commit()
    # Return a JSON response with a success message
    response = {"message": "Follower added successfully."}
    return jsonify(response), 200

# This route handles the display of a specific collaboration
@app.route("/collab/<int:id>", methods={"GET"})
@login_required
def specficcollabration(id):
    # Get the current user
    user = User.query.filter_by(id=current_user.id).first()
    # Get the Collabration object with the specified ID
    collab = Collabration.query.filter_by(id=id).first()
    # Render the "specficcollab.html" template and pass the collab and user objects
    return render_template("specficcollab.html", collab=collab, user=user)

# This route handles the creation of a new collaboration
@app.route("/addcollabration", methods=["GET", "POST"])
@login_required
def addcollab():
    # Get the current user
    user = User.query.filter_by(id=current_user.id).first()

    # Check if the request method is POST
    if request.method == "POST":
        # Get the current date
        current_date = datetime.date.today().isoformat()
        # Clean the form input data using Bleach
        name = bleach.clean(request.form["name"])
        requirments = bleach.clean(request.form["requirment"])
        description = bleach.clean(request.form["description"])
        looking_for = bleach.clean(request.form["lookingfor"])
        user_id = current_user.id
        due_date = bleach.clean(request.form["Date"])

        # Check if the due date is valid (not in the past)
        if due_date <= current_date:
            # If the due date is invalid, flash a message and redirect to the "addcollab" route
            flash("You did not enter a valid date.")
            return redirect(url_for('addcollab'))

        # Create a new Collabration object
        new_collabration = Collabration(
            user_id=user_id,
            name=name,
            description=description,
            requirment=requirments,
            Looking_for=looking_for,
            due_date=due_date
        )
        # Add the new Collabration to the database and commit the changes
        db.session.add(new_collabration)
        db.session.commit()
        # Redirect the user to the "myprojects" route
        return redirect(url_for('myprojects'))
    else:
        # Render the "addcollabration.html" template and pass the user object
        return render_template("addcollabration.html", user=user)

# This route handles the display of the user's projects
@app.route("/myproject", methods=["GET", "POST"])
@login_required
def myprojects():
    # Get the current page from the query parameters (default is 1)
    page = request.args.get("page", default=1, type=int)
    # Set the number of projects to display per page
    per_page = 10
    # Calculate the offset for pagination
    offset = (page - 1) * per_page
    # Get the current user
    user = User.query.filter_by(id=current_user.id).first()
    # Get the user's ID
    user_id = current_user.id

    # Get the projects for the current user, with pagination
    projects = Collabration.query.filter_by(user_id=user_id).offset(offset).limit(per_page).all()
    # Get the total number of projects
    total_records = Collabration.query.count()
    # Calculate the total number of pages
    total_pages = (total_records // per_page) + (1 if total_records % per_page > 0 else 0)

    # Render the "myproject.html" template and pass the necessary variables
    return render_template("myproject.html", user=user, page=page, total_pages=total_pages, projects=projects)

# This route handles the display of other users' projects
@app.route("/otherprojects/<int:id>", methods=["GET"])
@login_required
def otherprojects(id):
    page = request.args.get("page", default=1, type=int)
    # Set the number of projects to display per page
    per_page = 10
    # Calculate the offset for pagination
    offset = (page - 1) * per_page

    # Get the current user
    user = User.query.filter_by(id=current_user.id).first()
    # Get the projects for the user with the specified ID
    projects = Collabration.query.filter_by(user_id=id).offset(offset).limit(per_page).all()

    total_records = Collabration.query.count()
    # Calculate the total number of pages
    total_pages = (total_records // per_page) + (1 if total_records % per_page > 0 else 0)

    # Render the "otherprojects.html" template and pass the projects and user objects
    return render_template("otherprojects.html", projects=projects, user=user,page=page, total_pages=total_pages)
@app.route("/deleteproject/<id>", methods=["POST", "GET"])
@login_required
def deleteproject(id):
    if request.method == "POST":
        users_id = current_user.id
        project = Collabration.query.filter_by(id=id).first()
        if project:
            if project.user_id == users_id:
                db.session.delete(project)
                db.session.commit()
                return redirect(url_for('myprojects'))

        else:
            return abort(404)


@app.route("/searchproject/<namepattern>", methods=["GET", "POST"])
@login_required
def searchproject(namepattern):
    user = User.query.filter_by(id=current_user.id).first()
    results = Collabration.query.filter(Collabration.name.like(f'%{namepattern}%')).all()
    return render_template("searchproject.html", results=results, pattern=namepattern, user=user)




@app.route("/searchprofile/<namepattern>", methods=["GET", "POST"])
@login_required
def searchprofile(namepattern):
    user = User.query.filter_by(id=current_user.id).first()
    results = User.query.filter(User.fname.like(f'%{namepattern}%'), User.id != current_user.id).all()
    return render_template("searchprofile.html", results=results, pattern=namepattern, user=user)


@app.route("/searchblog/<titleofblog>", methods=['GET', "POST"])
@login_required
def searchblog(titleofblog):

    page = request.args.get("page", default=1, type=int)
    per_page = 10
    offset = (page - 1) * per_page
    user = User.query.filter_by(id=current_user.id).first()
    results = Blog.query.filter(Blog.title.like(f'%{titleofblog}%'),Blog.user_id != current_user.id).offset(offset).limit(per_page).all()

    total_records = Blog.query.count()

    total_pages = (total_records // per_page) + (1 if total_records % per_page > 0 else 0)

    return render_template("searchblog.html", results=results, titleofblog=titleofblog, page=page, total_pages=total_pages,user=user)





@app.route("/otherusers")
@login_required
def otherusers():
    user = User.query.filter_by(id=current_user.id).first()
    page = request.args.get("page", default=1, type=int)
    per_page = 10
    offset = (page - 1) * per_page

    users = User.query.filter(User.id != current_user.id).offset(offset).limit(per_page).all()
    random.shuffle(users)

    total_records = User.query.count()

    total_pages = (total_records // per_page) + (1 if total_records % per_page > 0 else 0)

    return render_template("otherusers.html", users=users, page=page, total_pages=total_pages,user=user)





@app.route("/allfollowers/<int:id>", methods=["GET", "POST"])
@login_required
def allfollowers(id):
    user = User.query.filter_by(id=current_user.id).first()
    followers = Follower.query.filter_by(user_id=id).all()
    followers = followers.followers
    return render_template("allfollowers.html", followers=followers, user=user)




@app.route("/allfollwing", methods=["GET", "POST"])
@login_required
def allfollowing():
    user = User.query.filter_by(id=current_user.id).first()
    followers = Follower.query.filter_by(user_id=current_user.id)
    page = request.args.get("page", default=1, type=int)
    per_page = 10
    offset = (page - 1) * per_page

    follwoing = followers.query.offset(offset).limit(per_page).all()

    users = random.shuffle(followers)

    total_records = User.query.count()

    total_pages = (total_records // per_page) + (1 if total_records % per_page > 0 else 0)

    return render_template("otherusers.html", users=users, page=page, total_pages=total_pages,
                           user=user)



@app.route("/deleteaccount", methods=["GET", "POST"])
@login_required
def deleteaccount():
    """
    This route handles the deletion of a user's account.

    If the request method is POST, the user's account is deleted, including their profile photo and any collaborations they were a part of. The user is then logged out and redirected to the home page.

    If the request method is GET, the 'deleteaccount.html' template is rendered, displaying the user's information.

    Returns:
        If the request method is POST, a redirect to the home page.
        If the request method is GET, the rendered 'deleteaccount.html' template.
    """
    user = User.query.filter_by(id=current_user.id).first()
    if request.method == "POST":
        user = User.query.filter_by(id=current_user.id).first()
        collabrations = Collabration.query.filter_by(user_id=current_user.id).all()
        current_dir = os.getcwd()

        if user.profile_photo is not None:
            full_path = os.path.join(current_dir, user.profile_photo)
            os.remove(full_path)
        logout_user()
        db.session.delete(user)
        db.session.commit()
        return redirect(url_for('home'))
    else:
        return render_template("deleteaccount.html", user=user)


@app.route("/unfollow/<int:follower_id>", methods=["POST"])
@login_required
def unfollow(follower_id):
    """
    This route handles the unfollowing of a user.

    Args:
        follower_id (int): The ID of the user to be unfollowed.

    Returns:
        A JSON response indicating the status of the unfollow operation.
    """
    user_id = current_user.id
    following = Follower.query.filter_by(follower_id=follower_id).first()

    if following:
        db.session.delete(following)
        db.session.commit()
        response = {"message": "Follower unfollowed successfully."}
        return jsonify(response), 200
    else:

        response = {"message": "No such follower found to unfollow."}
        return jsonify(response), 404


@app.route("/profile/<int:id>", methods=["GET", "POST"])
@login_required
def profile(id):
    """
    This route displays the profile of a specific user.

    Args:
        id (int): The ID of the user whose profile is to be displayed.

    Returns:
        The rendered 'otherprofile.html' template with the user's information.
    """
    user = User.query.filter_by(id=id).first()
    return render_template("otherprofile.html", user=user)


@app.route("/interestinmyproject", methods=["GET"])
@login_required
def interestinmyproject():
    """
    This route displays the projects that the current user is a part of.

    Returns:
        The rendered 'interestinmyproject.html' template with the user's projects.
    """
    user = User.query.filter_by(id=current_user.id).first()
    projects = Collabration.query.filter_by(user_id=current_user.id).all()
    if projects:
        return render_template("interestinmyproject.html", projects=projects, user=user)


@app.route("/explore", methods=["GET"])
def explore():
    """
    This route displays the explore page, which shows the list of users.

    Returns:
        The rendered 'explore.html' template with the user's information and login status.
    """
    is_logged_in = current_user.is_authenticated
    user = User.query.filter_by(id=current_user.id).first()
    return render_template("explore.html", user=user, is_logged_in=is_logged_in)


@app.route("/userblogs/<int:id>", methods=["GET", "POST"])
def userblogs(id):
    """
    This route handles the display of user's blogs.

    Args:
        id (int): The ID of the user whose blogs are to be displayed.

    Returns:
        The rendered template for the user's blog page, along with the user's blogs and the current user's information.
    """
    blogs = Blog.query.filter_by(user_id=id).all()
    user = User.query.filter_by(id=current_user.id).first()
    return render_template("userblog.html", blogs=blogs, user=user)


@app.route("/fetchusername/<username>", methods=["POST"])
def fetchusername(username):
    """
    This route checks if a given username is already taken.

    Args:
        username (str): The username to be checked.

    Returns:
        A JSON response indicating whether the username is available or already taken.
    """
    user = User.query.filter_by(username=username).first()
    if user is not None:
        response = {"message": "Username already taken"}
        return jsonify(response), 400
    else:
        response = {"message": "Username is available."}
        return jsonify(response), 200


@app.route("/deleteprofile", methods=["POST"])
def deleteprofile():
    """
    This route handles the deletion of a user's profile.

    Returns:
        A redirect to the user's profile edit page.
    """
    user = User.query.filter_by(id=current_user.id).first()
    profile_photo = user.profile_photo
    if user.profile_photo != "static/images/noprofile.jpg":


        if os.remove("../"+user.profile_photo):
            response = {"message": "profile deleted successfully"}
            return response,200
        else:
            response ={"message": "photo deletion did not work"}
            return response,400
    print("../"+user.profile_photo)

    return redirect(url_for('editprofile'))

@app.route("/removelike/<int:id>", methods=["POST"])
def removelike(id):
    """
    This route handles the removal of a like on a blog post.

    Args:
        id (int): The ID of the blog post.

    Returns:
        A JSON response indicating the status of the like removal operation.
    """
    blog = Blog.query.filter_by(id=id).first()
    user = User.query.filter_by(id=current_user.id)
    user = user.liked_blogs
    if blog:
        if blog.user_id != current_user.id:
            if user in blog.liking_users:
                response = {"message": "can't be unliked since you haven't liked it"}
                return jsonify(response), 500
        else:
            response = {"message": "You can't like your own blog"}
            return jsonify(response), 404
    else:
        response = {"message": "Blog is not found"}
        return jsonify(response), 404

#
# def checkdue_date(allcollaboration):
#     for collabration in allcollaboration:
#         due_date = datetime.strptime(collabration.due_date, "%B %d, %Y").date()
#         if due_date > datetime.date.today():
#             db.session.delete(collabration)
#     db.session.commit()

@app.route("/followingprojects", methods=["GET"])
def followingprojects():
    page = request.args.get("page", default=1, type=int)
    per_page = 10
    offset = (page - 1) * per_page
    user = User.query.get(current_user.id)

    following = Follower.query.filter_by(follower_id=current_user.id).offset(offset).limit(per_page).all()
    followed_user_id = [f.followed_user.id for f in following]
    # query all the user the current user follows
    following_projects = Collabration.query.filter(Collabration.user_id.in_([user_id for user_id in followed_user_id ])).offset(offset).limit(per_page).all()

    # get the count of the query
    total_records = User.query.count()

    total_pages = (total_records // per_page) + (1 if total_records % per_page > 0 else 0)

    return render_template("FollowingProjects.html", user=user, page=page, total_pages=total_pages, projects=following_projects)


@app.route("/checkfollowing/<int:id>", methods=["POST"])
def checkfollowing(id):
    following = Follower.query.filter_by(user_id=id,follower_id=current_user.id).first()


    if following:
            response = {"message": "follows that user"}
            return jsonify(response), 200

    else:
        response = {"message": "Blog is not found"}
        return jsonify(response), 400




if __name__ == '__main__':

    app.run(debug=True, port=5000)
