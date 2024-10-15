from flask import Flask, request, session, redirect, url_for, render_template, flash
import psycopg2
from psycopg2 import sql
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os


app = Flask(__name__)
app.secret_key = 'cairocoders-ednalan'

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
UPLOAD_FOLDER = 'static/uploads/videos'  # Make sure this folder exists
ALLOWED_EXTENSIONS = {'mp4', 'mkv', 'avi', 'mov'}  # Add allowed video extensions


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/upload_video', methods=['GET', 'POST'])
def upload_video():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            userid = session.get('user_id')
            filename = secure_filename(file.filename)
            file.save(os.path.join(UPLOAD_FOLDER, filename))

            title = request.form['title']
            description = request.form['description']
            category = request.form['category']  # Получаем выбранную категорию

            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Используйте один запрос для вставки с категорией
                    cur.execute(
                        "INSERT INTO videos (user_id, filename, title, description, category) VALUES (%s, %s, %s, %s, %s)",
                        (userid, filename, title, description, category))
                    conn.commit()

            flash('Видео успешно загружено')
            return redirect(url_for('my_channel'))
    return render_template('upload_video.html')


@app.route('/edit_video/<int:video_id>', methods=['GET', 'POST'])
def edit_video(video_id):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Fetch the existing video details
            cur.execute("SELECT filename, title, description, category, upload_date FROM videos WHERE id = %s", (video_id,))
            video = cur.fetchone()


            cur.execute("SELECT filename, user_id, title, description FROM videos")
            videos = cur.fetchall()
            if video is None:
                flash('Видео не найдено')
                return redirect(url_for('my_channel'))

            if request.method == 'POST':
                if 'delete' in request.form:
                    # Удаление комментариев к видео
                    cur.execute("DELETE FROM comments WHERE video_id = %s", (video_id,))
                    # Удаление лайков и дизлайков к видео
                    cur.execute("DELETE FROM video_ratings WHERE video_id = %s", (video_id,))
                    cur.execute("DELETE FROM favorites WHERE video_id = %s", (video_id,))
                    # Удаление самого видео из базы данных
                    cur.execute("DELETE FROM videos WHERE id = %s", (video_id,))
                    conn.commit()

                    flash('Видео успешно удалено')
                    return redirect(url_for('my_channel'))
                else:
                    title = request.form['title']
                    description = request.form['description']

                    # Update the video details in the database
                    cur.execute("UPDATE videos SET title = %s, description = %s WHERE id = %s",
                                (title, description, video_id))
                    conn.commit()
                    title = request.form['title']
                    description = request.form['description']
                    category = request.form['category']  # Get the selected category

                    cur.execute("UPDATE videos SET title = %s, description = %s, category = %s WHERE id = %s",
                                (title, description, category, video_id))  # Update category as well
                    flash('Видео успешно обновлено')
                    return redirect(url_for('my_channel'))

    return render_template('edit_video.html', video=video, videos=videos)


@app.route('/music')
def music_page():
    userid = session.get('user_id')
    videos = []
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Получение данных о видео
            cur.execute("""
                SELECT v.id, v.filename, v.user_id, v.title, v.description, u.username
                FROM videos v
                JOIN users u ON v.user_id = u.id
                WHERE v.category = %s
            """, ('music',))
            videos_data = cur.fetchall()

            # Получение лайков, дизлайков и комментариев для каждого видео
            for video in videos_data:
                video_id = video[0]

                # Лайки и дизлайки
                cur.execute("""
                    SELECT COUNT(*) FILTER (WHERE rating = 1) AS likes,
                           COUNT(*) FILTER (WHERE rating = -1) AS dislikes
                    FROM video_ratings WHERE video_id = %s;
                """, (video_id,))
                ratings = cur.fetchone()

                # Комментарии
                cur.execute(
                    "SELECT u.username, c.comment, c.created_at FROM comments c JOIN users u ON c.user_id = u.id WHERE c.video_id = %s;",
                    (video_id,))
                comments = cur.fetchall()

                videos.append({
                    'id': video[0],
                    'filename': video[1],
                    'user_id': video[2],
                    'title': video[3],
                    'description': video[4],
                    'username': video[5],
                    'likes': ratings[0] if ratings else 0,
                    'dislikes': ratings[1] if ratings else 0,
                    'comments': comments,
                })

            # Получение аватара пользователя
            if userid:
                cur.execute("SELECT avatar FROM users WHERE id = %s", (userid,))
                result = cur.fetchone()
                avatar = result[0] if result else None
            else:
                avatar = None

    return render_template('musicpage.html', videos=videos, avatar=avatar)


@app.route('/gaming')
def gaming_page():
    userid = session.get('user_id')
    videos = []
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT v.id, v.filename, v.user_id, v.title, v.description, u.username
                FROM videos v
                JOIN users u ON v.user_id = u.id
                WHERE v.category = %s
            """, ('gaming',))
            videos_data = cur.fetchall()

            for video in videos_data:
                video_id = video[0]
                cur.execute("""
                    SELECT COUNT(*) FILTER (WHERE rating = 1) AS likes,
                           COUNT(*) FILTER (WHERE rating = -1) AS dislikes
                    FROM video_ratings WHERE video_id = %s;
                """, (video_id,))
                ratings = cur.fetchone()

                cur.execute(
                    "SELECT u.username, c.comment, c.created_at FROM comments c JOIN users u ON c.user_id = u.id WHERE c.video_id = %s;",
                    (video_id,))
                comments = cur.fetchall()

                videos.append({
                    'id': video[0],
                    'filename': video[1],
                    'user_id': video[2],
                    'title': video[3],
                    'description': video[4],
                    'username': video[5],
                    'likes': ratings[0] if ratings else 0,
                    'dislikes': ratings[1] if ratings else 0,
                    'comments': comments,
                })

            if userid:
                cur.execute("SELECT avatar FROM users WHERE id = %s", (userid,))
                result = cur.fetchone()
                avatar = result[0] if result else None
            else:
                avatar = None

    return render_template('gamepage.html', videos=videos, avatar=avatar)


@app.route('/education')
def education_page():
    userid = session.get('user_id')
    videos = []
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT v.id, v.filename, v.user_id, v.title, v.description, u.username
                FROM videos v
                JOIN users u ON v.user_id = u.id
                WHERE v.category = %s
            """, ('education',))
            videos_data = cur.fetchall()

            for video in videos_data:
                video_id = video[0]
                cur.execute("""
                    SELECT COUNT(*) FILTER (WHERE rating = 1) AS likes,
                           COUNT(*) FILTER (WHERE rating = -1) AS dislikes
                    FROM video_ratings WHERE video_id = %s;
                """, (video_id,))
                ratings = cur.fetchone()

                cur.execute(
                    "SELECT u.username, c.comment, c.created_at FROM comments c JOIN users u ON c.user_id = u.id WHERE c.video_id = %s;",
                    (video_id,))
                comments = cur.fetchall()

                videos.append({
                    'id': video[0],
                    'filename': video[1],
                    'user_id': video[2],
                    'title': video[3],
                    'description': video[4],
                    'username': video[5],
                    'likes': ratings[0] if ratings else 0,
                    'dislikes': ratings[1] if ratings else 0,
                    'comments': comments,
                })

            if userid:
                cur.execute("SELECT avatar FROM users WHERE id = %s", (userid,))
                result = cur.fetchone()
                avatar = result[0] if result else None
            else:
                avatar = None

    return render_template('sciencepage.html', videos=videos, avatar=avatar)


@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    if 'user_id' not in session:
        flash('Пожалуйста, войдите в систему.')
        return redirect(url_for('login'))

    userid = session['user_id']
    username = session['username']

    # Получение текущего аватара
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT avatar FROM users WHERE id = %s", (userid,))
            avatar = cur.fetchone()[0]

    if request.method == 'POST':
        # Обработка загрузки файла
        if 'avatar' in request.files and request.files['avatar'].filename:  # Если файл был загружен
            avatar_file = request.files['avatar']
            filename = secure_filename(avatar_file.filename)
            avatar_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            # Сохранение нового имени файла в базе данных
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("UPDATE users SET avatar = %s WHERE id = %s", (filename, userid))
                    conn.commit()

        # Дополнительная обработка изменений профиля
        new_username = request.form.get('username')
        if new_username:
            session['username'] = new_username
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("UPDATE users SET username = %s WHERE id = %s", (new_username, userid))
                    conn.commit()

        # Обработка изменения пароля (теперь необязательное)
        old_password = request.form.get('old_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        # Если указаны старый и новый пароли, проверяем и обновляем
        if old_password or new_password or confirm_password:
            if old_password and new_password and confirm_password:
                # Получение хеша текущего пароля из базы данных для валидации
                with get_db_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute("SELECT password FROM users WHERE id = %s", (userid,))
                        current_hashed_password = cur.fetchone()[0]

                if check_password_hash(current_hashed_password, old_password):
                    if new_password == confirm_password:
                        # Хешируем новый пароль и сохраняем его
                        new_hashed_password = generate_password_hash(new_password)
                        with get_db_connection() as conn:
                            with conn.cursor() as cur:
                                cur.execute("UPDATE users SET password = %s WHERE id = %s", (new_hashed_password, userid))
                                conn.commit()
                        flash('Пароль успешно изменен!', 'success')
                    else:
                        flash('Новые пароли не совпадают.', 'error')
                else:
                    flash('Старый пароль введен неверно.', 'error')
            else:
                flash('Вы должны предоставить старый пароль и оба новых пароля для изменения пароля.', 'error')

        flash('Профиль успешно обновлен!', 'success')
        return redirect(url_for('profile'))

    return render_template('edit_profile.html', username=username, avatar=avatar)



def get_db_connection():
    conn = psycopg2.connect(
        host=os.getenv("PGHOST"),  # Хост базы данных
        database=os.getenv("PGDATABASE"),  # Имя базы данных
        user=os.getenv("PGUSER"),  # Пользователь базы данных
        password=os.getenv("PGPASSWORD"),  # Пароль пользователя
        port=os.getenv("PGPORT") or 5432  # Порт базы данных по умолчанию 5432
    )
    return conn




@app.route('/')
def main_page():
    return render_template('mainpage.html')

@app.route('/licenc')
def licenc():
    return render_template('licenc.html')

@app.route('/trans')
def trans():
    return render_template('trans.html')

@app.route('/tools')
def tools():
    return render_template('tools.html')

@app.route('/spra')
def spra():
    return render_template('spra.html')

@app.route('/like_video/<int:video_id>', methods=['POST'])
def like_video(video_id):
    user_id = session.get('user_id')

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                        INSERT INTO video_ratings (video_id, user_id, rating)
                        VALUES (%s, %s, 1)
                        ON CONFLICT (video_id, user_id) DO UPDATE SET rating = 1;
                        """, (video_id, user_id))
            conn.commit()
            # Проверяем, есть ли уже запись в favorites
            cur.execute("""
                SELECT EXISTS(SELECT 1 FROM favorites WHERE user_id = %s AND video_id = %s);
            """, (user_id, video_id))
            exists = cur.fetchone()[0]

            if exists:
                # Если видео уже в "Понравившихся", удаляем его
                cur.execute("""
                    DELETE FROM favorites WHERE user_id = %s AND video_id = %s;
                """, (user_id, video_id))
            else:
                # Если видео не в "Понравившихся", добавляем его
                cur.execute("""
                    INSERT INTO favorites (user_id, video_id)
                    VALUES (%s, %s);
                """, (user_id, video_id))

            conn.commit()

    return redirect(url_for('glav'))


@app.route('/popular')
def popular():
    videos = []
    userid = session.get('user_id')
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Получение видео с более чем 5 лайками
            cur.execute("""
                SELECT v.id, v.filename, v.user_id, v.title, v.description, u.username
                FROM videos v
                JOIN users u ON v.user_id = u.id
                JOIN (
                    SELECT video_id
                    FROM video_ratings
                    WHERE rating = 1
                    GROUP BY video_id
                    HAVING COUNT(*) > 5
                ) AS popular_videos ON v.id = popular_videos.video_id;
            """)
            videos_data = cur.fetchall()

            # Получение лайков и дизлайков, аналогично как в /glav
            for video in videos_data:
                video_id = video[0]
                cur.execute("""
                    SELECT COUNT(*) FILTER (WHERE rating = 1) AS likes,
                           COUNT(*) FILTER (WHERE rating = -1) AS dislikes
                    FROM video_ratings WHERE video_id = %s;
                """, (video_id,))
                ratings = cur.fetchone()

                # Получение комментариев для каждого видео
                cur.execute(
                    "SELECT u.username, c.comment, c.created_at FROM comments c JOIN users u ON c.user_id = u.id WHERE c.video_id = %s;",
                    (video_id,))
                comments = cur.fetchall()

                videos.append({
                    'id': video[0],
                    'filename': video[1],
                    'user_id': video[2],
                    'title': video[3],
                    'description': video[4],
                    'username': video[5],
                    'likes': ratings[0] if ratings else 0,
                    'dislikes': ratings[1] if ratings else 0,
                    'comments': comments
                })
                cur.execute("SELECT avatar FROM users WHERE id = %s", (userid,))
                result = cur.fetchone()
                avatar = result[0] if result else None
    return render_template('popular.html', videos=videos, avatar=avatar)

@app.route('/favorites')
def favorites():
    userid = session.get('user_id')
    videos = []
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Получение всех "Понравившихся" видео
            cur.execute("""
                SELECT v.id, v.filename, v.user_id, v.title, v.description, u.username
                FROM favorites f
                JOIN videos v ON f.video_id = v.id
                JOIN users u ON v.user_id = u.id
                WHERE f.user_id = %s;
            """, (userid,))
            videos_data = cur.fetchall()

            # Получение лайков и дизлайков, аналогично как в /glav
            for video in videos_data:
                video_id = video[0]
                cur.execute("""
                    SELECT COUNT(*) FILTER (WHERE rating = 1) AS likes,
                           COUNT(*) FILTER (WHERE rating = -1) AS dislikes
                    FROM video_ratings WHERE video_id = %s;
                """, (video_id,))
                ratings = cur.fetchone()

                # Получение комментариев для каждого видео
                cur.execute(
                    "SELECT u.username, c.comment, c.created_at FROM comments c JOIN users u ON c.user_id = u.id WHERE c.video_id = %s;",
                    (video_id,))
                comments = cur.fetchall()

                videos.append({
                    'id': video[0],
                    'filename': video[1],
                    'user_id': video[2],
                    'title': video[3],
                    'description': video[4],
                    'username': video[5],
                    'likes': ratings[0] if ratings else 0,
                    'dislikes': ratings[1] if ratings else 0,
                    'comments': comments
                })
                if userid:
                    cur.execute("SELECT avatar FROM users WHERE id = %s", (userid,))
                    result = cur.fetchone()
                    avatar = result[0] if result else None
                else:
                    avatar = None
    return render_template('favorites.html', videos=videos, avatar=avatar)

@app.route('/dislike_video/<int:video_id>', methods=['POST'])
def dislike_video(video_id):
    user_id = session.get('user_id')
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Insert or update the dislike
            cur.execute("""
                INSERT INTO video_ratings (video_id, user_id, rating)
                VALUES (%s, %s, -1)
                ON CONFLICT (video_id, user_id) DO UPDATE SET rating = -1;
            """, (video_id, user_id))
            conn.commit()
    return redirect(url_for('glav'))

@app.route('/comment_video/<int:video_id>', methods=['POST'])
def comment_video(video_id):
    user_id = session.get('user_id')
    comment = request.form['comment']
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO comments (video_id, user_id, comment) VALUES (%s, %s, %s)",
                       (video_id, user_id, comment))
            conn.commit()
    return redirect(url_for('glav'))

@app.route('/get_video_data')
def get_video_data(video_id):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Get likes, dislikes and comments for the video
            cur.execute("""
                SELECT COUNT(*) FILTER (WHERE rating = 1) AS likes,
                       COUNT(*) FILTER (WHERE rating = -1) AS dislikes
                FROM video_ratings WHERE video_id = %s;
            """, (video_id,))
            ratings = cur.fetchone()

            cur.execute("SELECT u.username, c.comment, c.created_at FROM comments c JOIN users u ON c.user_id = u.id WHERE c.video_id = %s;", (video_id,))
            comments = cur.fetchall()

    return jsonify({'likes': ratings[0], 'dislikes': ratings[1], 'comments': comments})


@app.route('/glav')
def glav():
    userid = session.get('user_id')
    videos = []

    sort_date = request.args.get('sort_date', 'desc')
    sort_likes = request.args.get('sort_likes', 'desc')

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Получение данных о видео с учетом сортировки
            cur.execute(f"""
                SELECT v.id, v.filename, v.user_id, v.title, v.description, u.username, v.upload_date
                FROM videos v
                JOIN users u ON v.user_id = u.id
                ORDER BY v.upload_date {sort_date},  
                         (SELECT COUNT(*) FILTER (WHERE rating = 1) FROM video_ratings WHERE video_id = v.id) {sort_likes}
            """)
            videos_data = cur.fetchall()

            for video in videos_data:
                video_id = video[0]
                cur.execute("""
                    SELECT COUNT(*) FILTER (WHERE rating = 1) AS likes,
                           COUNT(*) FILTER (WHERE rating = -1) AS dislikes
                    FROM video_ratings WHERE video_id = %s;
                """, (video_id,))
                ratings = cur.fetchone()

                cur.execute(
                    "SELECT u.username, c.comment, c.created_at FROM comments c JOIN users u ON c.user_id = u.id WHERE c.video_id = %s;",
                    (video_id,))
                comments = cur.fetchall()

                videos.append({
                    'id': video[0],
                    'filename': video[1],
                    'user_id': video[2],
                    'title': video[3],
                    'description': video[4],
                    'username': video[5],
                    'likes': ratings[0] if ratings else 0,
                    'dislikes': ratings[1] if ratings else 0,
                    'comments': comments,
                    'upload_date': video[6]  # Include upload date for sorting purposes
                })

            cur.execute("SELECT avatar FROM users WHERE id = %s", (userid,))
            result = cur.fetchone()
            avatar = result[0] if result else None

    return render_template('glav.html', videos=videos, avatar=avatar)

@app.route('/user_channel/<int:user_id>')
def user_channel(user_id):
    # Get the logged-in user's id
    logged_in_userid = session.get('user_id')
    videos = []

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Fetch the user's avatar and username using user_id from the URL
            cur.execute("SELECT avatar, username FROM users WHERE id = %s", (user_id,))
            result = cur.fetchone()
            avatar = result[0] if result else None
            username = result[1] if result else "Unknown User"

            # Fetch the user's videos
            cur.execute("SELECT id, filename, title, description FROM videos WHERE user_id = %s", (user_id,))
            videos = cur.fetchall()  # Gets all the user's videos
            videos_count = len(videos)

            # Check if the logged-in user is subscribed to the channel
            cur.execute("SELECT COUNT(*) FROM subscriptions WHERE subscriber_id = %s AND subscribed_to_id = %s",
                        (logged_in_userid, user_id))
            is_subscribed = cur.fetchone()[0] > 0

            # Get the number of subscribers
            cur.execute("SELECT COUNT(*) FROM subscriptions WHERE subscribed_to_id = %s", (user_id,))
            subscribers_count = cur.fetchone()[0]

    return render_template('chanuser.html', avatar=avatar, user_id=user_id, username=username,
                           videos=videos, videos_count=videos_count,
                           logged_in_userid=logged_in_userid, is_subscribed=is_subscribed,
                           subscribers_count=subscribers_count)  # передаём количество подписчиков



@app.route('/subscribe/<int:user_id>', methods=['POST'])
def subscribe(user_id):
    logged_in_userid = session.get('user_id')
    if logged_in_userid:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                try:
                    cur.execute("INSERT INTO subscriptions (subscriber_id, subscribed_to_id) VALUES (%s, %s)",
                                (logged_in_userid, user_id))
                    conn.commit()
                    flash('Подписка успешна!', 'success')
                except Exception as e:
                    print(e)
                    flash('Не удалось подписаться на пользователя.', 'error')
    return redirect(url_for('user_channel', user_id=user_id))

@app.route('/unsubscribe/<int:user_id>', methods=['POST'])
def unsubscribe(user_id):
    logged_in_userid = session.get('user_id')
    if logged_in_userid:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                try:
                    cur.execute("DELETE FROM subscriptions WHERE subscriber_id = %s AND subscribed_to_id = %s",
                                (logged_in_userid, user_id))
                    conn.commit()
                    flash('Успешная отписка!', 'success')
                except Exception as e:
                    print(e)
                    flash('Не удалось отписаться от пользователя.', 'error')
    return redirect(url_for('user_channel', user_id=user_id))

@app.route('/sub')
def subscriptions():
    logged_in_userid = session.get('user_id')
    subscriptions = []
    userid = session.get('user_id')
    if logged_in_userid:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT u.id, u.username, u.avatar 
                    FROM subscriptions s
                    JOIN users u ON s.subscribed_to_id = u.id
                    WHERE s.subscriber_id = %s
                """, (logged_in_userid,))
                subscriptions = cur.fetchall()
                cur.execute("SELECT avatar FROM users WHERE id = %s", (userid,))
                result = cur.fetchone()
                avatar = result[0] if result else None
    return render_template('sub.html', subscriptions=subscriptions, avatar=avatar)


@app.route('/mychannel')
def my_channel():
    userid = session.get('user_id')
    videos = []
    logged_in_userid = session.get('user_id')

    sort_date = request.args.get('sort_date', 'desc')
    sort_likes = request.args.get('sort_likes', 'desc')

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT avatar FROM users WHERE id = %s", (userid,))
            result = cur.fetchone()
            avatar = result[0] if result else None

            # Получение видео с учетом сортировки
            cur.execute(f"""
                SELECT id, filename, title, description, upload_date
                FROM videos 
                WHERE user_id = %s
                ORDER BY upload_date {sort_date}, 
                         (SELECT COUNT(*) FILTER (WHERE rating = 1) FROM video_ratings WHERE video_id = videos.id) {sort_likes}
            """, (userid,))
            videos = cur.fetchall()  # Gets all user's videos
            videos_count = len(videos)

            cur.execute("SELECT COUNT(*) FROM subscriptions WHERE subscriber_id = %s AND subscribed_to_id = %s",
                        (logged_in_userid, userid))
            is_subscribed = cur.fetchone()[0] > 0

            cur.execute("SELECT COUNT(*) FROM subscriptions WHERE subscribed_to_id = %s", (userid,))
            subscribers_count = cur.fetchone()[0]

    return render_template('mychannel.html', avatar=avatar, userid=userid, videos=videos, videos_count=videos_count,
                           is_subscribed=is_subscribed, subscribers_count=subscribers_count)

@app.route('/channels')
def channels():
    logged_in_userid = session.get('user_id')
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, username, avatar FROM users")
            users = cur.fetchall()  # Get all users
            cur.execute("SELECT avatar FROM users WHERE id = %s", (logged_in_userid,))
            result = cur.fetchone()
            avatar = result[0] if result else None
    return render_template('channels.html', users=users, avatar=avatar)


@app.route('/search_videos')
def search_videos():
    userid = session.get('user_id')
    search_query = request.args.get('s')
    videos = []
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT avatar FROM users WHERE id = %s", (userid,))
            result = cur.fetchone()
            avatar = result[0] if result else None
            if search_query:
                # Поиск видео по названию
                cur.execute("""
                    SELECT v.id, v.filename, v.user_id, v.title, v.description, u.username
                    FROM videos v
                    JOIN users u ON v.user_id = u.id
                    WHERE v.title LIKE %s
                """, (f"%{search_query}%",))  # Используем LIKE для частичного совпадения
                videos_data = cur.fetchall()

                # Обработка результатов поиска
                for video in videos_data:
                    video_id = video[0]
                    cur.execute("""
                        SELECT COUNT(*) FILTER (WHERE rating = 1) AS likes,
                               COUNT(*) FILTER (WHERE rating = -1) AS dislikes
                        FROM video_ratings WHERE video_id = %s;
                    """, (video_id,))
                    ratings = cur.fetchone()

                    # Получение комментариев для каждого видео
                    cur.execute(
                        "SELECT u.username, c.comment, c.created_at FROM comments c JOIN users u ON c.user_id = u.id WHERE c.video_id = %s;",
                        (video_id,))
                    comments = cur.fetchall()

                    videos.append({
                        'id': video[0],
                        'filename': video[1],
                        'user_id': video[2],
                        'title': video[3],
                        'description': video[4],
                        'username': video[5],
                        'likes': ratings[0] if ratings else 0,
                        'dislikes': ratings[1] if ratings else 0,
                        'comments': comments
                    })
    return render_template('video.html', avatar=avatar, userid=userid, videos=videos)


@app.route('/video/<int:video_id>')
def video_page(video_id):
    userid = session.get('user_id')
    video = None
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT v.id, v.filename, v.user_id, v.title, v.description, u.username
                FROM videos v
                JOIN users u ON v.user_id = u.id
                WHERE v.id = %s
            """, (video_id,))
            video_data = cur.fetchone()

            if video_data:
                video_id = video_data[0]
                cur.execute("""
                    SELECT COUNT(*) FILTER (WHERE rating = 1) AS likes,
                           COUNT(*) FILTER (WHERE rating = -1) AS dislikes
                    FROM video_ratings WHERE video_id = %s;
                """, (video_id,))
                ratings = cur.fetchone()

                # Получение комментариев для каждого видео
                cur.execute(
                    "SELECT u.username, c.comment, c.created_at FROM comments c JOIN users u ON c.user_id = u.id WHERE c.video_id = %s;",
                    (video_id,))
                comments = cur.fetchall()

                video = {
                    'id': video_data[0],
                    'filename': video_data[1],
                    'user_id': video_data[2],
                    'title': video_data[3],
                    'description': video_data[4],
                    'username': video_data[5],
                    'likes': ratings[0] if ratings else 0,
                    'dislikes': ratings[1] if ratings else 0,
                    'comments': comments
                }
            cur.execute("SELECT avatar FROM users WHERE id = %s", (userid,))
            result = cur.fetchone()
            avatar = result[0] if result else None

    return render_template('video.html', video=video, avatar=avatar, userid=userid)


@app.route('/mainpage')
def mainpage():
    userid = session.get('user_id')

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT avatar FROM users WHERE id = %s", (userid,))
            result = cur.fetchone()
            avatar = result[0] if result else None  # обработка ошибки, если пользователя нет
    return render_template('mainpage.html',  avatar=avatar, userid=userid)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        password_confirmation = request.form['password_confirmation']

        if password != password_confirmation:
            flash('Пароли не совпадают!')
            return redirect(url_for('register'))

        avatar_filename = None
        # Проверка наличия файла аватара
        if 'avatar' in request.files:
            avatar = request.files['avatar']
            if avatar and avatar.filename:  # Убедитесь, что файл загружен
                avatar_filename = secure_filename(avatar.filename)
                avatar.save(os.path.join(app.config['UPLOAD_FOLDER'], avatar_filename))

        # Проверка на существование пользователя
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM users WHERE username = %s OR email = %s", (username, email))
                existing_user = cur.fetchone()

                if existing_user:
                    flash('Пользователь с таким никнеймом или почтой уже существует!')
                    return redirect(url_for('register'))

                hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
                cur.execute("INSERT INTO users (username, email, password, avatar) VALUES (%s, %s, %s, %s)",
                            (username, email, hashed_password, avatar_filename))
                conn.commit()

        flash('Регистрация прошла успешно!')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM users WHERE username = %s", (username,))
                user = cur.fetchone()

                if user and check_password_hash(user[3], password):  # user[3] - это хэш пароля
                    session['user_id'] = user[0]  # user[0] - это id пользователя
                    session['username'] = user[1]  # user[1] - это никнейм пользователя
                    flash('Вы вошли в систему!')
                    return redirect(url_for('profile'))  # перенаправление на страницу профиля

        flash('Неверное имя пользователя или пароль.')
        return redirect(url_for('login'))

    return render_template('login.html')





@app.route('/profile')
def profile():
    if 'user_id' not in session:
        flash('Пожалуйста, войдите в систему.')
        return redirect(url_for('login'))

    userid = session['user_id']
    username = session['username']

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT email, avatar FROM users WHERE id = %s", (userid,))
            email, avatar = cur.fetchone()

    return render_template('profile.html', username=username, userid=userid, avatar=avatar, email=email)


@app.route('/search')
def search():
    query = request.args.get('s')
    search_results = []

    if query:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT v.id, v.filename, v.user_id, v.title, v.description, u.username FROM videos v JOIN users u ON v.user_id = u.id WHERE v.title ILIKE %s;",
                    ('%' + query + '%',))
                videos_data = cur.fetchall()

                for video in videos_data:
                    video_id = video[0]
                    cur.execute("""
                        SELECT COUNT(*) FILTER (WHERE rating = 1) AS likes,
                               COUNT(*) FILTER (WHERE rating = -1) AS dislikes
                        FROM video_ratings WHERE video_id = %s;
                    """, (video_id,))
                    ratings = cur.fetchone()

                    cur.execute(
                        "SELECT u.username, c.comment, c.created_at FROM comments c JOIN users u ON c.user_id = u.id WHERE c.video_id = %s;",
                        (video_id,))
                    comments = cur.fetchall()

                    search_results.append({
                        'id': video[0],
                        'filename': video[1],
                        'user_id': video[2],
                        'title': video[3],
                        'description': video[4],
                        'username': video[5],
                        'likes': ratings[0] if ratings else 0,
                        'dislikes': ratings[1] if ratings else 0,
                        'comments': comments
                    })

    return render_template('search.html', search_results=search_results)


if __name__ == '__main__':
    app.run(debug=True)
