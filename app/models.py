from app import db
from datetime import datetime
from sqlalchemy.dialects.mysql import LONGTEXT


class User_info(db.Model):  # 用户信息表

    __tablename__ = 'user_info'

    id = db.Column(db.Integer, primary_key=True, unique=True)
    uid = db.Column(db.String(225), unique=True)
    password = db.Column(db.String(225))
    name = db.Column(db.String(225))
    email = db.Column(db.String(225))
    sign = db.Column(LONGTEXT)
    icon = db.Column(db.String(225))
    register_login = db.Column(db.DateTime())  # 注册时间
    collected_id = db.Column(LONGTEXT) # 收藏的信息id列表，以；隔开
    like_id = db.Column(LONGTEXT)# 点赞的信息id列表，以；隔开

    def __init__(self, uid, password, name, icon, sign, email, register_login,collected_id,like_id):
        self.uid = uid
        self.password = password
        self.name = name
        self.email = email
        self.sign = sign
        self.icon = icon
        self.register_login = register_login
        self.collected_id = collected_id
        self.like_id = like_id
    def __repr__(self):
        return "<user uid '{}'>".format(self.uid)


# 客户信息表
class Client(User_info):

    __tablename__ = 'clients'

    money = db.Column(db.Integer)  # 钱包
    credit_card_number = db.Column(db.String(225))  # 银行卡号
    address = db.Column(db.String(225))  # 常住地
    feedback = db.Column(LONGTEXT)  # 反馈信息
    membership = db.Column(db.Integer)  # 会员信息
    logging_status = db.Column(db.Integer)  # 登录状态
    score = db.Column(db.Integer)  # 总积分

    def __init__(self, uid, username, password, icon, email, phone_number, wechat, qq, weibo, name, gender, birthdate, ID_number, register_date, sign, money, credit_card_number, address, feedback, membership, logging_status, score):
        self.uid = uid
        self.username = username
        self.password = password
        self.icon = icon
        self.email = email
        self.phone_number = phone_number
        self.wechat = wechat
        self.qq = qq
        self.weibo = weibo
        self.name = name
        self.gender = gender
        self.birthdate = birthdate
        self.ID_number = ID_number
        self.register_date = register_date
        self.sign = sign
        self.money = money
        self.credit_card_number = credit_card_number
        self.address = address
        self.feedback = feedback
        self.membership = membership
        self.logging_status = logging_status
        self.score = score

        db.create_all()

    def __repr__(self):
        return "<clients uid '{}'>".format(self.uid)


class Blog_info(db.Model):  # 分享内容信息表

    __tablename__ = 'blog_info'
    id = db.Column(db.Integer, primary_key=True, unique=True)
    title = db.Column(db.String(225))
    blog_markdown = db.Column(db.Text)
    tag = db.Column(db.String(225))  # 标签
    imag = db.Column(db.String(225)) #照片或视频路径
    audio = db.Column(db.String(225))
    blog_type = db.Column(db.Integer)
    upload_time = db.Column(db.DateTime()) # 发布时间
    blog_timeid = db.Column(db.String(225))
    user_id = db.Column(db.String(225), db.ForeignKey('user_info.uid'))
    view_count = db.Column(db.Integer)  # 浏览次数
    comment_count = db.Column(db.Integer)  # 评论数
    like_count = db.Column(db.Integer)  # 点赞数
    collected_count = db.Column(db.Integer)  # 被收藏次数
    lon = db.Column(db.DECIMAL(precision=15, scale=10))  # 经度
    lat = db.Column(db.DECIMAL(precision=15, scale=10))  # 纬度

    def __init__(self, title, blog_markdown, imag, audio, blog_type, upload_time, blog_timeid, user_id,tag,view_count,comment_count,like_count,collected_count,lon,lat):
        self.title = title
        self.blog_markdown = blog_markdown
        self.imag = imag
        self.audio = audio
        self.blog_type = blog_type
        self.user_id = user_id
        self.upload_time = upload_time
        self.blog_timeid = blog_timeid
        self.tag = tag
        self.view_count = view_count
        self.comment_count = comment_count
        self.like_count = like_count
        self.collected_count = collected_count
        self.lon = lon
        self.lat = lat

    def __repr__(self):
        return "<blog id '{}'>".format(self.id)


class Comment_info(db.Model):

    __tablename__ = 'comment_info'
    id = db.Column(db.Integer, primary_key=True, unique=True)
    comment = db.Column(db.String(225))
    blog_id = db.Column(db.Integer, db.ForeignKey('blog_info.id'))
    user_id = db.Column(db.String(225), db.ForeignKey('user_info.uid'))
    upload_time = db.Column(db.DateTime())

    def __init__(self, comment, blog_id, user_id, upload_time):
        self.comment = comment
        self.blog_id = blog_id
        self.user_id = user_id
        self.upload_time = upload_time

    def __repr__(self):
        return "<comment id '{}'>".format(self.id)
