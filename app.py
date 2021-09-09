from flask import (Flask, render_template, request, redirect,
                   url_for, flash, send_from_directory, session)
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from upload_cloud import upload_cloud
from paste_cloud import paste_cloud
import os


# Flaskをインスタンス化
app = Flask(__name__)

key = os.urandom(21)
app.secret_key = key

id_pwd = {'dorayaki': 'meronpan'}

# DBの定義
URI = 'sqlite:///test.db'
app.config['SQLALCHEMY_DATABASE_URI'] = URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class DB(db.Model):
    __tablename__ = 'test_table'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(30), unique=True)
    file_path = db.Column(db.String(64))
    date = db.Column(db.DateTime, nullable=False, default=datetime.today())

# DBの生成
@app.cli.command('initialize_DB')
def initialize_DB():
    db.create_all()

# エラーハンドリング
@app.errorhandler(404)
def not_found(error):
    return 'リンク先のページがないのでエラーです(´・ω・`)'

# /// メインプログラム ///
 
# index(TOP)画面へのルーティング
# sessionが無効であればlogin()関数を実行する。
@app.route('/')
def index():
    if not session.get('login'):
        return redirect(url_for('login'))
    else:
        registration_data = DB.query.all()
        return render_template('index.html', registration_data=registration_data)

# ログイン画面を展開する
@app.route('/login')
def login():
    return render_template('login.html')

# 入力されたIDとパスワードを判定する
# 合っていたらsessionをTrue（有効）に、
# 間違っていたらlogin()関数を実行してログイン画面を表示する
@app.route('/logincheck', methods=['POST'])
def logincheck():
    id = request.form['id']
    password = request.form['password']
        
    if id in id_pwd:
        if password == id_pwd[id]:
            session['login'] = True
        else:
            session['login'] = False
    else:
        session['login'] = False

    if session['login']:
        return redirect(url_for('index'))
    else:
        return redirect(url_for('login'))

# ログアウト
@app.route('/logout')
def logout():
    session.pop('login', None)
    return redirect(url_for('index'))

# ファイルアップロード画面へのルーティング
@app.route('/upload')
def upload():
    return render_template('upload.html')

# アップロードされたファイルを取得してテキストマイニングを実行する
@app.route('/upload_register', methods=['POST'])
def upload_register():
    title = request.form['title']
    if title:
        file = request.files['file']
        file_path = secure_filename(file.filename)
        file.save(file_path)
        # upload_cloud()関数を実装する
        # DBに登録するのは、アップロード時のタイトルとpngファイル
        result_path = upload_cloud(file_path)
        register_file = DB(title=title, file_path=result_path)
        db.session.add(register_file)
        db.session.commit()
        flash('結果ファイルが用意できました')
        return redirect(url_for('index'))
    else:
        flash('タイトルを入力してもう一度アップロードしてください')
        return redirect(url_for('index'))

# 貼付画面へのルーティング
@app.route('/paste')
def paste():
    return render_template('paste.html')
    
# 貼付されたデータを取得してテキストマイニングを実行する
@app.route('/paste_register', methods=['POST'])
def paste_register():
    title = request.form['title']
    if title:
        paste_data = request.form['paste_data']
        # paste_cloud()関数を実装する
        # DBに登録するのはアップロード時のタイトルとpngファイル
        result_path = paste_cloud(title, paste_data)
        register_file = DB(title=title, file_path=result_path)
        db.session.add(register_file)
        db.session.commit()
        flash('結果ファイルが用意できました')
        return redirect(url_for('index'))
    else:
        flash('タイトルを入力してもう一度アップロードしてください')
        return redirect(url_for('index'))

# ダウンロード  
@app.route('/download/<file_path>', methods=['POST'])
def download(file_path):
    return send_from_directory('static', file_path, as_attachment=True)

# 削除
@app.route('/delete/<int:id>', methods=['POST'])
def delete(id):
    delete_data = DB.query.get(id)
    delete_file = delete_data.file_path
    db.session.delete(delete_data)
    db.session.commit()
    os.remove('static/' + delete_file)
    flash('ファイルを削除しました')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
