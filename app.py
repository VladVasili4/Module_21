from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from models import db, CustomUser, Photo, Comment
from forms import UserRegistrationForm, UserLoginForm
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_migrate import Migrate
import os


app = Flask(__name__)
app.config.from_object('config.Config')
db.init_app(app)

migrate = Migrate(app, db)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


@login_manager.user_loader
def load_user(user_id):
    return CustomUser.query.get(int(user_id))


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = UserRegistrationForm()

    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data, method='pbkdf2:sha256')
        new_user = CustomUser(
            username = form.username.data,
            first_name = form.first_name.data,
            last_name = form.last_name.data,
            email = form.email.data,
            phone_number = form.phone_number.data,
            birth_date = form.birth_date.data,
            password = hashed_password
        )
        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)   # После успешной регистрации сразу авторизуем пользователя
        return redirect(url_for('home'))

    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = UserLoginForm()

    if form.validate_on_submit():
        user = CustomUser.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for('home'))
        else:
            # Добавьте обработку ошибки входа
            flash('Неверный логин или пароль', 'danger')

    return render_template('login.html', form=form)


@app.route('/users_list')
@login_required  #Декоратор @login_required проверяет, авторизован ли пользователь. Если нет, он будет
# перенаправлен на маршрут, указанный в login_manager.login_view (в нашем случае, на страницу /login)
def users_list():
    users = CustomUser.query.all()
    return render_template('users_list.html', users=users)


@app.route('/logout')
def logout():
    logout_user()  # Ожидается, что этот вызов разорвет сессию
    return redirect(url_for('home'))  # Перенаправление на главную страницу


@app.route('/photos', methods=['GET', 'POST'])
@login_required
def photos():
    if request.method == 'POST':
        file = request.files.get('photo')
        description = request.form.get('description')
        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            new_photo = Photo(
                user_id=current_user.id,
                image_path=f"{app.config['UPLOAD_FOLDER']}/{filename}",
                description=description
            )
            db.session.add(new_photo)
            db.session.commit()
            flash('Фото успешно загружено', 'success')
    photos = Photo.query.order_by(Photo.timestamp.desc()).all()
    return render_template('photos.html', photos=photos)

@app.route('/photos/<int:photo_id>/comments', methods=['POST'])
@login_required
def add_comment(photo_id):
    content = request.form.get('comment')
    if content:
        new_comment = Comment(
            user_id=current_user.id,
            photo_id=photo_id,
            content=content
        )
        db.session.add(new_comment)
        db.session.commit()
        flash('Комментарий добавлен', 'success')
    return redirect(url_for('photos'))


if __name__ == '__main__':
    app.run(debug=True)
