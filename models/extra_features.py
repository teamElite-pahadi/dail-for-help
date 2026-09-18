from datetime import datetime
from extensions import db

class Notification(db.Model):
    __tablename__='notifications'
    id=db.Column(db.Integer,primary_key=True)
    user_id=db.Column(db.Integer,db.ForeignKey('users.id',ondelete='CASCADE'),nullable=False)
    title=db.Column(db.String(180),nullable=False)
    message=db.Column(db.Text,nullable=False)
    is_read=db.Column(db.Boolean,default=False,nullable=False)
    created_at=db.Column(db.DateTime,default=datetime.utcnow,nullable=False)

class ChatMessage(db.Model):
    __tablename__='chat_messages'
    id=db.Column(db.Integer,primary_key=True)
    booking_id=db.Column(db.Integer,db.ForeignKey('bookings.id',ondelete='CASCADE'),nullable=False)
    sender_id=db.Column(db.Integer,db.ForeignKey('users.id',ondelete='CASCADE'),nullable=False)
    message=db.Column(db.Text,nullable=False)
    created_at=db.Column(db.DateTime,default=datetime.utcnow,nullable=False)
    sender=db.relationship('User', foreign_keys=[sender_id])

class Coupon(db.Model):
    __tablename__='coupons'
    id=db.Column(db.Integer,primary_key=True)
    code=db.Column(db.String(40),unique=True,nullable=False,index=True)
    discount_percent=db.Column(db.Float,default=0,nullable=False)
    max_discount=db.Column(db.Float,default=0,nullable=False)
    is_active=db.Column(db.Boolean,default=True,nullable=False)
    expires_at=db.Column(db.DateTime)
    created_at=db.Column(db.DateTime,default=datetime.utcnow,nullable=False)

class BookingExtra(db.Model):
    __tablename__='booking_extras'
    id=db.Column(db.Integer,primary_key=True)
    booking_id=db.Column(db.Integer,db.ForeignKey('bookings.id',ondelete='CASCADE'),unique=True,nullable=False)
    is_emergency=db.Column(db.Boolean,default=False,nullable=False)
    coupon_code=db.Column(db.String(40))
    discount_amount=db.Column(db.Float,default=0,nullable=False)
    worker_latitude=db.Column(db.Float)
    worker_longitude=db.Column(db.Float)
    worker_location_updated_at=db.Column(db.DateTime)
    completion_otp=db.Column(db.String(255))
    completion_otp_verified=db.Column(db.Boolean,default=False,nullable=False)
    proof_filename=db.Column(db.String(255))
