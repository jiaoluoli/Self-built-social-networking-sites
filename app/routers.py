import os
import random
from datetime import datetime
import json
import hashlib
import heapq
import math
from PIL import Image

from flask import flash, get_flashed_messages, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from flask import jsonify, Response, abort

# 导入数据库
from app import app
from app import db
from .models import User_info, Blog_info, Comment_info

'''
登陆注册模块
'''
db.create_all()

@app.route('/login', methods=['GET', 'POST'])  # 登陆
def login():
    if request.method == 'POST':
        uid = request.form.get('uid')
        password = request.form.get('password')
        u_data = User_info.query.filter_by(uid=uid).first()
        try:
            lon = request.form.get('lon')
            lat = request.form.get('lat')
        except:
            # 设置默认位置
            lon = 116.310443
            lat = 39.972148
        try:
            rp = u_data.password
            if check_password_hash(rp, password):
                session['uid'] = uid
                session['lon'] = lon
                session['lat'] = lat
                return redirect(url_for('index',lon=lon,lat=lat))
            else:
                flash('密码错误')
                return render_template('login.html', flash=flash)
        except:
            flash('用户不存在')
            return render_template('login.html', flash=flash)
    else:
        return render_template('login.html')



@app.route('/registered', methods=['GET', 'POST'])  # 注册
def registered():
    if request.method == 'POST':

        uid = request.form.get('uid')  # 验证用户名
        try:
            if User_info.query.filter_by(uid=uid).first().uid:
                flash('该用户名存在')
                return render_template('registered.html', flash=flash)
        except:
            pass

        password = request.form.get('password')
        rpassword = request.form.get('rpassword')

        if password != rpassword:  # 验证密码
            flash('两次密码不一致')
            render_template('registered.html', flash=flash)
        name = request.form.get('name')
        email = request.form.get('email')

        password = generate_password_hash(password)  # 密码加密

        user = User_info(
            uid=uid,
            password=password,
            name=name,
            email=email,
            sign='初来此地，请多多指教！',  # 注册时默认
            icon='upload/icon/default.jpg',
            register_login=datetime.now(),
            collected_id="",
            like_id=""
        )

        db.session.add(user)  # 向数据库添加用户信息
        db.session.commit()
 
        return redirect(url_for('login'))
    else:
        return render_template('registered.html')


'''
主页
'''


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])  # 主页
def index():

    # 验证session
    try:
        uid = session['uid']
    except:
        flash('请先登陆')
        return render_template('login.html', flash=flash)
    # 轮播设置
    try:
        myLon = float(request.args.get('lon'))
        myLat = float(request.args.get('lat'))
    except:
        if (session['lon'] != ""):
            myLon = float(session['lon'])
            myLat = float(session['lat'])
        else:
            # 设置默认位置
            myLon = 116.310443
            myLat = 39.972148

    time = datetime.now()
    post_all1 = Blog_info.query.all()
    post_all = []
    distances = []
    for post in post_all1:
        lon = post.lon
        lat = post.lat
        distance = (2*math.asin(math.sqrt(pow(math.sin((math.radians(myLat)-math.radians(lat))/2),2)+math.cos(math.radians(lat))*math.cos(math.radians(myLat))*pow(math.sin((math.radians(myLon)-math.radians(lon))/2),2)))*6371*1000)
        if distance < 1000:
            post_all.append(post)
            distances.append(round(distance,2))
     
    post_id = []
    post_bgs_distance = []
    if len(post_all)==0:
        return redirect(url_for('showmap'))
    elif len(post_all)<5:
        post_id.append(post_all[0].id)
        post_bgs_distance.append(distances[0])
    else:
        view_counts = [post.view_count for post in post_all]
        # 浏览量最多的五个
        index_list = [a[0] for a in sorted(list(enumerate(view_counts)),key=lambda x:x[1],reverse=True)][:5]
        post_id.extend([post_all[i].id for i in index_list])
        post_bgs_distance.extend([distances[i] for i in index_list])

    # 轮播文章选择
    post_bgs = []
    post_bgs_author = []
    for i in post_id:
        post_bg = Blog_info.query.filter_by(id=i).first()
        post_bg_author = User_info.query.filter_by(uid=post_bg.user_id).first()
        post_bgs.append(post_bg)
        post_bgs_author.append(post_bg_author)
    posts = zip(post_bgs, post_bgs_author, post_bgs_distance)

    # 文章展示
    blog_ids = [post_all[i].id for i in range(len(post_all))]
    post_blogs = []
    post_blogs_author = []
    for i in blog_ids:
        post_blog = Blog_info.query.filter_by(id=i).first()
        author = User_info.query.filter_by(uid=post_blog.user_id).first()
        post_blogs.append(post_blog)
        post_blogs_author.append(author)
    blog_zip = zip(post_blogs, post_blogs_author, distances)

    return render_template('index.html', posts=posts, blog_zip=blog_zip, flash=flash)


'''
地图模式
'''

@app.route('/showmap')
def showmap():
    # 验证session
    try:
        uid = session['uid']
    except:
        flash('请先登陆')
        return render_template('login.html',flash=flash)
        
    try:
        myLon = float(request.args.get('lon'))
        myLat = float(request.args.get('lat'))
    except:
        if (session['lon'] != ""):
            myLon = float(session['lon'])
            myLat = float(session['lat'])
        else:
            # 设置默认位置
            myLon = 116.310443
            myLat = 39.972148
    
    # 用户位置集
    user_location = {
        'self_lon': myLon,
        'self_lat': myLat
    }
    
    all_shares = Blog_info.query.all()
    if len(all_shares) == 0:
        flash("一起来开发这一公里内吧！")
    select_shares = []  # 筛选符合距离的shares

    # 遍历式查询
    r = 6371.39  # 地球平均半径,精度10m(高德地图定位精度同为10m)

    for share in all_shares:
        share_lon = share.lon  # 获取文章经纬度,float类型
        share_lat = share.lat
        # Haversine算法计算距离
        lon1, lat1, lon2, lat2 = map(
            math.radians, [myLon, myLat, share_lon, share_lat])
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        d = c * r * 1000
        if d <= 1000:
            select_shares.append(share)

    # 查询完善信息
    shares = []
    for share in select_shares:
        if share.id:
            post = {}
            post['title'] = share.title
            post['img'] = share.imag
            post['gps_lon'] = share.lon
            post['gps_lat'] = share.lat
            post['blog_id'] = share.id
            # 缩放图片,获取图片大小
            # basepath = os.path.dirname(__file__)
            # path = basepath + '/' + 'static' + '/' + share.imag 
            # img = Image.open(path)
            # post['imgh'] = 250
            # post['imgw'] = 250
            shares.append(post)
            
    return render_template('map.html', shares=shares, user_location=user_location)

       
    
   
'''
文章详情页及提交
'''


@app.route('/view/<blog_id>', methods=['GET', 'POST'])  # 文章详情页
def view(blog_id):
    # 验证session
    try:
        uid = session['uid']
    except:
        flash('请先登陆')
        return render_template('login.html', flash=flash)
    try:
        myLon = float(session['lon'])
        myLat = float(session['lat'])
    except:
        # 设置默认位置
        myLon = 116.310443
        myLat = 39.972148      

    print("myLon: "+str(myLon))
    user = User_info.query.filter_by(uid=uid).first() #获取用户信息
    blog_data = Blog_info.query.filter_by(id=blog_id).first()  # 获取文章信息
    if blog_data == None:
        blog_data = Blog_info.query.one()

    lon = blog_data.lon
    lat = blog_data.lat

    distance = (2*math.asin(math.sqrt(pow(math.sin((math.radians(myLat)-math.radians(lat))/2),2)+math.cos(math.radians(lat))*math.cos(math.radians(myLat))*pow(math.sin((math.radians(myLon)-math.radians(lon))/2),2)))*6371*1000)
    distance = round(distance,2)
    collected_ids = filter(None,user.collected_id.split(";"))
    like_ids = filter(None,user.like_id.split(";"))
    coli = ""
    if(blog_id in collected_ids):
        coli += "1"
    else:
        coli += "0"
    if(blog_id in like_ids):
        coli += "1"
    else:
        coli += "0"

    if request.method == 'POST':  # 当有留言提交时
        comment = request.form.get('comment')
        c = Comment_info(
            comment=comment,
            blog_id=blog_id,
            user_id=session['uid'],
            upload_time=datetime.now()
        )
        blog_data.comment_count += 1
        db.session.add(c)  # 向数据库添加用户信息
        db.session.commit()

    # 获取comment
    comments = Comment_info.query.filter_by(blog_id=blog_id).all()

    authors = []
    if comments is not None:
        for comment in comments:
            authors.append(User_info.query.filter_by(
                uid=comment.user_id).first())

    comment_zip = zip(comments, authors)

    # comment数量
    comment_number = len(comments)

    try:
        author_data = User_info.query.filter_by(
            uid=blog_data.user_id).first()  # 获取文章对应的author信息
    except:
        abort(404)  # 404

    blog_data.view_count += 1
    db.session.commit()

    if blog_data.blog_type == 1:  # 标准文章格式
        view = {
            'style': 'format-standard'
        }
        return render_template('single-standard.html', blog=blog_data, comment_number=comment_number, comment_zip=comment_zip, author=author_data, view=view, coli=coli, distance=distance)
    else:  # 音乐文章格式
        view = {
            'style': 'format-audio'
        }
        return render_template('single-audio.html', blog=blog_data, comment_number=comment_number, comment_zip=comment_zip, author=author_data, view=view, coli=coli, distance=distance)


'''
作者信息展示页面
'''


@app.route('/author/<authoruid>', methods=['GET', 'POST'])  # 作者信息展示页面
def author(authoruid):

    if request.method == 'POST':

        name = request.form.get('name')
        email = request.form.get('email')
        sign = request.form.get('sign')
        icon = request.files['icon']

        fname = os.path.splitext(icon.filename)[1]
        basepath = os.path.dirname(__file__)
        filename = datetime.now().strftime('%Y%m%d%H%M%S')+fname
        icon.save(os.path.join(basepath, 'static/upload/icon', filename))
        icon = os.path.join('upload/icon', secure_filename(filename))

        User_info.query.filter_by(uid=session['uid']).update({  # 更新
            'name': name,
            'email': email,
            'sign': sign,
            'icon': icon
        })
        
        db.session.commit()
    else:
        pass

    # 验证登陆
    # 验证当前用户是否匹配以显示change
    change = None
    try:
        uid = session['uid']
    except:
        flash('请先登陆')
        return render_template('login.html')
    if uid == authoruid:
        change = 1

    u_data = User_info.query.filter_by(uid=authoruid).first()
    if u_data:
        pass
    else:
        abort(404)  # 404

    blogs = Blog_info.query.filter_by(user_id=authoruid).all()
    collected_id = filter(None, u_data.collected_id.split(";"))
    collection = []
    for i in collected_id:
        collection.append(Blog_info.query.filter_by(id=i).first())

    # 验证u_data
    # 前端检验blogs
    return render_template('author_info.html', author=u_data, blogs=blogs, change=change, collection = collection)


'''
检索功能
'''


@app.route('/index/search')
def search():  # 标题关键词检索

    # 验证session
    try:
        uid = session['uid']
    except:
        flash('请先登陆')
        return render_template('login.html', flash=flash)

    search_info = request.args.get('search_info')
    search_data = Blog_info.query.filter(
        Blog_info.title.like('%' + search_info + '%')).all()

    try:
        search_authors = []
        for i in search_data:
            author = User_info.query.filter_by(uid=i.user_id).first()
            search_authors.append(author)
            search_zip = zip(search_data, search_authors)
    except:
        pass

    if search_authors != []:
        search_zip = zip(search_data, search_authors)
    else:
        flash('很抱歉，没有检索到对应的信息')
        return redirect('index')
    return render_template('search.html', search_zip=search_zip)


'''
用户markdown文章上传
'''


@app.route('/markdown', methods=['GET', 'POST'])
def blog_markdown():

    # 验证session
    try:
        uid = session['uid']
    except:
        flash('请先登陆')
        return render_template('login.html', flash=flash)

    # markdown编辑
    if request.method == 'POST':

        # 获取基本信息
        title = request.form.get('title')
        blog_markdown = request.form.get('basic-editormd-html-code')
        try:
            lon = request.form.get('lon')
            lat = request.form.get('lat')
        except:
            flash('未允许地理位置！')
            return render_template('index.html', flash=flash)
        tag = request.form.get('tag')
        upload_time = datetime.now()
        blog_type = 1
        blog_timeid = datetime.now().strftime('%Y%m%d%H%M%S')
        collected_count = 0
        like_count = 0
        view_count = 0
        comment_count = 0

        # imag or vid
        basepath = os.path.dirname(__file__)
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)            
        if file and allowed_file(file.filename):
            fname = secure_filename(file.filename)  
            filename = md5secret(fname)+fname[fname.rfind("."):]
            file.save(os.path.join(basepath, 'static/upload/images', filename))                  
        fname = os.path.splitext(file.filename)[1]
        imag = 'upload/images/' + filename

        # 是否上传音乐
        try:
            audio = request.files['audio']
            fname = os.path.splitext(audio.filename)[1]
            basepath = os.path.dirname(__file__)
            filename = datetime.now().strftime('%Y%m%d%H%M%S')+fname
            audio.save(os.path.join(basepath, 'static/upload/audio', filename))
            audio = os.path.join('upload/audio', secure_filename(filename))
            blog_type = 2
        except:
            audio = None

        blog = Blog_info(
            title=title,
            blog_markdown=blog_markdown,
            imag=imag,
            audio=audio,
            blog_type=blog_type,
            blog_timeid=blog_timeid,
            upload_time=upload_time,
            user_id=uid,
            lon =  lon,
            lat = lat,
            tag = tag,
            collected_count = collected_count,
            view_count = view_count,
            like_count = like_count,
            comment_count = comment_count

        )

        try:
            db.session.add(blog)
            db.session.commit()
        except:
            abort(404)

        blog = Blog_info.query.filter_by(blog_timeid=blog_timeid).first()
        return redirect(url_for('view', blog_id=blog.id))
    else:
        return render_template('markdown.html')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in set(['png', 'jpg', 'jpeg', 'gif','mp4','mov','ogg'])
def md5secret(word):
    md5 = hashlib.md5()
    md5.update(word.encode("utf8"))
    return md5.hexdigest()


@app.route('/collect', methods=['POST'])
def collect():
    # 验证session
    try:
        uid = session['uid']
    except:
        flash('请先登陆')
        return render_template('login.html', flash=flash)
    blog_id = request.values['blog_id']
    blog = Blog_info.query.filter_by(id=blog_id).first()
    if blog == None:
        return jsonify({"status":0})
    else:
        user = User_info.query.filter_by(uid=uid).first()
        if request.values['collector']=="true":
            user.collected_id += ";" + str(blog_id)
            blog.collected_count += 1

        else:
            ucid = user.collected_id
            user.collected_id = ucid[:ucid.rfind(";")]
            blog.collected_count -= 1
        
        db.session.commit()
        data = {"status":1,"count":blog.collected_count}
        return jsonify(data)        


@app.route('/like', methods=['POST'])
def likeblo():
    # 验证session
    try:
        uid = session['uid']
    except:
        flash('请先登陆')
        return render_template('login.html', flash=flash)   
    blog_id = request.values['blog_id']
    blog = Blog_info.query.filter_by(id=blog_id).first()
    if blog == None:
        return jsonify({"status":0})
    else:
        user = User_info.query.filter_by(uid=uid).first()
        if request.values['good']=="true":
            user.like_id += ";" + str(blog_id)
            blog.like_count += 1

        else:
            ucid = user.like_id
            user.like_id = ucid[:ucid.rfind(";")]
            blog.like_count -= 1
        
        db.session.commit()
        data = {"status":1,"count":blog.like_count}
        return jsonify(data)        


@app.route('/uploadimages', methods=['POST'])  # 图片上传处理 for edithormd
def uploadimages():
    file = request.files.get('editormd-image-file')
    if not file:
        res = {
            'success': 0,
            'message': u'文件格式异常'
        }
    else:
        fname = os.path.splitext(file.filename)[1]
        basepath = os.path.dirname(__file__)
        filename = datetime.now().strftime('%Y%m%d%H%M%S')+fname
        file.save(os.path.join(basepath, 'static/upload/images', filename))
        res = {
            'success': 1,
            'url': url_for('.image', name=filename)
        }
    return jsonify(res)


@app.route('/image/<name>')  # 编辑器显示图片处理 for editormd
def image(name):
    basepath = os.path.dirname(__file__)
    with open(os.path.join(basepath, 'static/upload/images', name), 'rb') as f:
        resp = Response(f.read(), mimetype="image/jpeg")
    return resp


'''
文学少女介绍
'''


@app.route('/bungakushojoinfo')
def bungakushojoinfo():
    # 验证session
    try:
        uid = session['uid']
    except:
        flash('请先登陆')
        return render_template('login.html', flash=flash)

    return render_template('info.html')


'''
404
'''


@app.errorhandler(404)
def page_404(er):
    return render_template('404.html')
