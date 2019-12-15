from flask import Flask, render_template, request, redirect, url_for, current_app, session, jsonify
from datetime import datetime
from werkzeug.utils import secure_filename


from database import Database, Instructor
from models.student import Student
from models.room import Room
from models.classroom import Classroom
from models.people import People
from models.lesson import Lesson


import hashlib
import os

UPLOAD_FOLDER = '/static/img'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

app = Flask(__name__, static_url_path='/static')
app.config['SECRET_KEY'] = 'betterthanoriginalsis'
app.config['BASE_DIR'] = os.path.dirname(__file__)
app.config['UPLOAD_FOLDER'] = app.config['BASE_DIR'] + UPLOAD_FOLDER


@app.route("/")
def home_page():
    """
    This is the first page users get. We will have a login form here.

    :return:
    """
    return render_template("home.html", 
        authenticated = session.get("logged_in"),
        username = "anon" if not session.get("logged_in") else session["person"]["name"],
        person = session.get("person")
        )


@app.route("/add_course")
def add_course():
    """
    This is for professors to add a new course and relevant information about it e.g. date, TA's etc.
    :return:
    """
    return render_template("add_course.html")


@app.route("/grades")
def grades():
    """
    This webpage is intended for all users.
    Students -> Will be able to see their grades
    Assistants -> Will be able to see their grades(for grad level courses) and enter grades for courses they are TA'ing
    Professors -> Will be able to enter grades (choose a course, get a list of students)
    :return:
    """
    return render_template("grades.html")


@app.route("/courses")
def courses():
    """
    This page is common for users.

    If user is student, she will see the courses she is registered to.
    If user is an assistant, she will see the courses she is registered to and she is TA'ing.
    If user is a professor, she will see the courses she is giving.

    :return:
    """
    return render_template("courses.html")


@app.route("/settings")
def user_settings():
    """
    Users will be able to update their profile pictures, phone number etc.

    :return:
    """
    return render_template("settings.html")


@app.route("/schedule")
def schedule():
    """
    This is a common page. Users will be able to see their schedules according to courses
    they are registered to/they are giving.

    :return:
    """
    return render_template("schedule.html")


@app.route("/exams")
def exams():
    """
    In this page we will show the exam dates for students.
    Same for assistants.

    Professors will see exam dates of their courses and they will be able to update the exam date if it is not
    colliding with another exam date.

    :return:
    """
    return render_template("exams.html")

@app.route("/su", methods = ["GET", "POST"])
def admin_page():
    """
    God mode.
    :return:
    """
    db = Database()

    if request.method == "GET":
        #print(session.get("person").get("admin"), "asdadsd")
        if session.get("person")["admin"]:
            return render_template("admin_page.html", 
                faculty_list=db.get_faculties(),
                prof_list=db.get_instructors(),
                student_list=db.get_students(), 
                datetime=datetime.now(),
                clubs=db.get_clubs_info_astext(),
                faculties=db.get_all_faculties(),
                departments=db.get_departments_text(),
                buildings = db.get_buildings(),
                rooms=db.get_rooms(),
                instructors=db.get_instructors(),
                classrooms=db.get_classrooms(),
                assistants=db.get_assistant_info(),
                labs = db.get_lab_info(),
                papers = db.get_paper_by_author(57)
                )
        else:
            return redirect(url_for("home_page"))
    return render_template("admin_page.html")

@app.route("/rooms_list", methods = ["GET", "POST"])
def rooms_page():
    '''
    In this page we will show the rooms
    :return:
    '''
    db = Database()
    rooms = db.get_rooms()
    return render_template("rooms_list.html", rooms = rooms)

@app.route("/assistants", methods=["POST", "GET"])
def as_page():
    db = Database()
    assistants = db.get_assistant_info()
    return render_template("assistants.html", assistants=assistants)

@app.route("/buildings", methods=["POST", "GET"])
def bu_page():
    db = Database()
    buildings = db.get_buildings()
    return render_template("buildings.html", buildings=buildings)

@app.route("/room_create", methods= ["POST", "GET"])
def room_create():
    db = Database()
    data = request.form
    is_class = 'FALSE'
    is_room = 'FALSE'
    is_lab = 'FALSE'
    if data["type"] == "class":
        is_class = 'TRUE'
    elif data["type"] == "room":
        is_room = 'TRUE'
    elif data["type"] == "lab":
        is_lab = 'TRUE'
    room = Room(data["building"], data["name"], data["availability"], is_class, is_room, is_lab)
    db.add_room(room)
    return redirect(url_for("admin_page"))

@app.route("/room_edit", methods= ["POST", "GET"])
def room_edit():
    db = Database()
    data = request.form
    if data["button"] == "delete":
        room_keys = request.form.getlist("room_keys")
        for room_key in room_keys:
            db.delete_classroom(int(room_key))
    elif data["button"] == "update":
        room = db.get_room(request.form.getlist("room_keys")[0])
        return render_template("room_update.html", room=room)
    else:
        pass
    return redirect(url_for("rooms_page"))

@app.route("/room_update", methods= ["POST", "GET"])
def room_update():
    db = Database()
    data = request.form
    attrs = ["room_name","building","class", "lab" ,"room" ,"available"]
    classFlag = labFlag = roomFlag = "FALSE"
    if data["type"] == "class":
        classFlag = "TRUE" 
    elif data["type"] == "lab":
        labFlag = "TRUE" 
    elif data["type"] == "room":
        roomFlag = "TRUE" 
    values = [data["name"], data["building"], classFlag, labFlag, roomFlag, data["availability"]]
    db.update_room(data["id"], attrs, values)
    return redirect(url_for("rooms_page"))

@app.route("/classrooms_list", methods = ["GET", "POST"])
def classrooms_page():
    '''
    In this page we will show the classrooms
    :return:
    '''
    db = Database()
    classrooms = db.get_classrooms()
    return render_template("classrooms_list.html", classrooms = classrooms)

@app.route("/classroom_create", methods= ["POST", "GET"])
def classroom_create():
    db = Database()
    data = request.form
    newroom = Room(data["building"], data["name"], data["availability"], classroom="TRUE",lab="FALSE",room="FALSE")
    room = db.add_room(newroom)

    classroom = Classroom(room.id, room.name, room.building, data["type"], data["restoration_date"], data["capacity"], data["conditioner"], data["board_type"])
    db.add_classroom(classroom)
    return redirect(url_for("admin_page"))

@app.route("/classroom_edit", methods= ["POST", "GET"])
def classroom_edit():
    db = Database()
    data = request.form
    if data["button"] == "delete":
        classroom_keys = request.form.getlist("classroom_keys")
        for classroom_key in classroom_keys:
            db.delete_classroom(int(classroom_key))
    elif data["button"] == "update":
        classroom = db.get_classroom(request.form.getlist("classroom_keys")[0])
        return render_template("classroom_update.html", classroom=classroom, datetime=datetime.now())
    else:
        pass
    return redirect(url_for("classrooms_page"))

@app.route("/classroom_update", methods= ["POST", "GET"])
def classroom_update():
    db = Database()
    data = request.form
    attrs = ["type","air_conditioner","last_restoration" ,"board_type" ,"cap"]
    values = [data["type"], data["conditioner"], data["restoration_date"], data["board_type"], data["capacity"]]
    db.update_classroom(data["id"], attrs, values)
    return redirect(url_for("classrooms_page"))

@app.route("/instructors", methods = ["GET", "POST"])
def instructors_page():
    '''
    In this page we will show the instructors
    :return:
    '''
    db = Database()
    instructors = db.get_instructors()

    return render_template("instructors.html", instructors = instructors)

@app.route("/instructor_create", methods= ["POST", "GET"])
def instructor_create():
    db = Database()
    data = request.form
    password = hashlib.md5(data["password"].encode())
    person = People(name=data["name"], password=password.hexdigest(), mail=data["mail"])
    db.add_person(person) 
    instructor = Instructor(person.id, data["name"], data["bachelors"], data["masters"], data["doctorates"], data["department"], data["room"], data["lab"])
    db.add_instructor(instructor)
    return redirect(url_for("admin_page"))

@app.route("/instructor_edit", methods= ["POST", "GET"])
def instructor_edit():
    db = Database()
    data = request.form
    if data["button"] == "delete":
        instructor_keys = request.form.getlist("instructor_keys")
        for ins_key in instructor_keys:
            db.delete_instructor(int(ins_key))
    elif data["button"] == "update":
        instructor = db.get_instructor(request.form.getlist("instructor_keys")[0])
        return render_template("instructor_update.html", instructor=instructor)
    else:
        pass
    return redirect(url_for("instructors_page"))

@app.route("/instructor_update", methods= ["POST", "GET"])
def instructor_update():
    db = Database()
    data = request.form
    attrs = ["department", "room", "lab", "bachelors", "masters", "doctorates"]
    values = [data["department"], data["room"], data["lab"], data["bachelors"], data["masters"], data["doctorates"]]
    db.update_instructor(data["id"], attrs, values)
    return redirect(url_for("instructors_page"))

@app.route("/student_create", methods= ["POST", "GET"])
def student_create():
    db = Database()
    data = request.form

    password = hashlib.md5(data["password"].encode())

    student = Student(data["name"], data["number"], data["mail"], data["cred"], data["depart"], data["facu"], data["club"], data["lab"], password)
    db.add_student(student)
    return redirect(url_for("admin_page"))

@app.route("/student_list", methods = ["GET", ])
def students_list():
    #db = current_app.config["db"]
    #students = db.get_students().values()
    db = Database()
    students = db.get_students()

    return render_template("students_list.html", students = students)


@app.route("/login", methods = ["GET", ])
def login_page():
    return render_template("login_page.html")

@app.route("/login_action", methods = ["POST", ])
def login_action():
    data = request.form
    
    db = Database()
    person = db.get_person_by_mail(data["mail"])

    attempted_hashed_passw = hashlib.md5(data["password"].encode()).hexdigest()

    if not person or person.password != attempted_hashed_passw:
        return redirect(url_for("login_page"))

    session["logged_in"] = 1
    session["person"] = vars(person)
    return redirect(url_for("home_page"))

@app.route("/signup", methods = ["GET", ])
def signup_page():
    return render_template("signup_page.html")

@app.route("/signup_action", methods = ["POST", ])
def signup_action():
    data = request.form 
    print(data)

    if not data.get("type"):
        return redirect(url_for("home_page"))
    
    password = hashlib.md5(data["password"].encode())

    if "pic" not in request.files:
            flash('No file part')
            return redirect(request.url)

    file = request.files["pic"]
    # if user does not select file, browser also
    # submits an empty part without filename
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)

    if file and file.filename[-3:] in ALLOWED_EXTENSIONS:
        basedir = os.path.abspath(os.path.dirname(__file__))
        filename = secure_filename(file.filename[:-4] + data["mail"][:-4] + file.filename[-4:])
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    
    person = People(name=data["name"], password=password.hexdigest(), mail=data["mail"], type=data["type"], photo=filename)
    db = Database()

    if db.person_exists(person):
        return redirect(url_for("login_page"))

    db.add_person(person)

    session["logged_in"] = 1
    session["person"] = vars(person)

    return redirect(url_for("home_page"))   


@app.route("/logout", methods = ["GET", ])
def logout():
    if session["logged_in"]:
        session["logged_in"] = 0
        session["person"] = None

    return redirect(url_for("home_page"))

@app.route("/lesson_create", methods = ["POST", ])
def lesson_create():
    data = request.form
    print(data)
    lesson = Lesson(data["crn"], data["date"], data["code"], data["instructor"], data["location"], data["assistant"], data["credit"])
    db = Database()
    db.create_lesson(lesson)

    return redirect(url_for("admin_page"))

@app.route("/enroll", methods = ["GET", "POST"])
def enroll_page():
    db = Database()
    enrolled_list = db.get_enrolled(session.get("person")["id"])
    enrolled = []
    for enr in enrolled_list:
        enrolled.append(enr[2])

    if request.method == "GET":
        if not session["logged_in"]:
            return redirect(url_for("login_page"))

        return render_template("enroll_page.html",
            authenticated = session.get("logged_in"),
            username = "anon" if not session.get("logged_in") else session["person"]["name"],
            person = session.get("person"),
            enrolled = enrolled
            )

    else:
        data = request.form
        if data["type"] == "1": # searched by CRN
            result = db.search_lesson_by_crn(data["value"])
        else:
            result = db.search_lesson_by_instructor(data["value"])

        return render_template("enroll_page.html",
            authenticated = session.get("logged_in"),
            username = "anon" if not session.get("logged_in") else session["person"]["name"],
            person = session.get("person"),
            result = result,
            enrolled = enrolled
            )


@app.route("/enroll_action", methods = ["GET", ])
def enroll_action():
    lesson_id = request.args.get("lesson_id")
    if not lesson_id or not session["logged_in"]:
        return redirect(url_for("home_page"))

    db = Database()
    enrollments = db.get_enrolled(session["person"]["id"])
    for enr in enrollments:
        if enr[2] == lesson_id:
            return redirect(url_for("enroll_page"))

    if db.enroll_for_student(student_id = session["person"]["id"], lesson_id = lesson_id):
        return jsonify({"Success": True})

    return jsonify({"Success": False})

@app.route("/leave_action", methods = ["GET", ])
def leave_action():
    lesson_id = request.args.get("lesson_id")
    if not lesson_id or not session["logged_in"]:
        return redirect(url_for("home_page"))

    db = Database()
    if db.leave_for_student(student_id = session["person"]["id"], lesson_id = lesson_id):
        return jsonify({"Success": True})

    return jsonify({"Success": False})


if __name__ == "__main__":
    app.run(debug=True)
