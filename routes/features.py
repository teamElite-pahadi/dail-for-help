from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from extensions import db
from models.worker import Worker
from models.service import Service
from models.worker_service import WorkerService
from models.booking import Booking
from models.extra_features import Notification, ChatMessage, Coupon, BookingExtra

features_bp=Blueprint('features',__name__,url_prefix='/features')

def notify(user_id,title,message):
    db.session.add(Notification(user_id=user_id,title=title,message=message))

def customer_only(): return current_user.is_authenticated and current_user.is_customer

@features_bp.route('/assistant',methods=['GET','POST'])
def assistant():
    answer=None; suggestions=[]
    q=request.form.get('problem','').strip() if request.method=='POST' else ''
    if q:
        rules=[('ac','AC Repair'),('cool','AC Repair'),('wire','Electrical'),('light','Electrical'),('fan','Electrical'),('leak','Plumbing'),('tap','Plumbing'),('pipe','Plumbing'),('clean','Cleaning'),('laptop','Computer Repair'),('computer','Computer Repair'),('paint','Painting'),('wood','Carpentry'),('furniture','Carpentry'),('fridge','Appliance Repair')]
        found=[]
        for key,name in rules:
            if key in q.lower() and name not in found: found.append(name)
        suggestions=Service.query.filter(Service.is_active.is_(True),Service.name.in_(found)).all() if found else Service.query.filter(Service.is_active.is_(True)).order_by(Service.name).limit(4).all()
        answer='Based on your problem, these services may match. Choose a service to see approved available workers.'
    return render_template('features/assistant.html',answer=answer,suggestions=suggestions,q=q)

@features_bp.route('/estimate',methods=['GET','POST'])
def estimate():
    services=Service.query.filter_by(is_active=True).order_by(Service.name).all(); result=None
    if request.method=='POST':
        service=Service.query.get_or_404(int(request.form.get('service_id')))
        hours=max(.5,float(request.form.get('hours',1) or 1)); emergency=request.form.get('emergency')=='1'
        rates=[w.hourly_rate for w in Worker.query.join(Worker.service_links).filter(WorkerService.service_id==service.id,Worker.is_approved.is_(True)).all() if w.hourly_rate]
        base=(sum(rates)/len(rates) if rates else 500)*hours; surcharge=base*.25 if emergency else 0
        result={'service':service,'base':round(base),'emergency':round(surcharge),'total':round(base+surcharge)}
    return render_template('features/estimate.html',services=services,result=result)

@features_bp.route('/notifications')
@login_required
def notifications():
    items=Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).limit(50).all()
    for n in items: n.is_read=True
    db.session.commit(); return render_template('features/notifications.html',notifications=items)

@features_bp.route('/booking/<int:booking_id>/chat',methods=['GET','POST'])
@login_required
def chat(booking_id):
    b=Booking.query.get_or_404(booking_id)
    if current_user.id not in (b.customer_id,b.worker.user_id): return 'Forbidden',403
    if request.method=='POST':
        msg=request.form.get('message','').strip()
        if msg: db.session.add(ChatMessage(booking_id=b.id,sender_id=current_user.id,message=msg)); notify(b.worker.user_id if current_user.id==b.customer_id else b.customer_id,'New chat message',f'New message for booking #{b.id}.'); db.session.commit(); return redirect(url_for('features.chat',booking_id=b.id))
    messages=ChatMessage.query.filter_by(booking_id=b.id).order_by(ChatMessage.created_at).all()
    return render_template('features/chat.html',booking=b,messages=messages)

@features_bp.route('/booking/<int:booking_id>/invoice')
@login_required
def invoice(booking_id):
    b=Booking.query.get_or_404(booking_id)
    if current_user.id not in (b.customer_id,b.worker.user_id) and not current_user.is_admin: return 'Forbidden',403
    extra=BookingExtra.query.filter_by(booking_id=b.id).first()
    discount=extra.discount_amount if extra else 0
    total=max(0,(b.price or 0)-discount)
    return render_template('features/invoice.html',booking=b,discount=discount,total=total)

@features_bp.route('/booking/<int:booking_id>/emergency',methods=['POST'])
@login_required
def emergency(booking_id):
    b=Booking.query.get_or_404(booking_id)
    if current_user.id!=b.customer_id: return 'Forbidden',403
    e=BookingExtra.query.filter_by(booking_id=b.id).first() or BookingExtra(booking_id=b.id)
    e.is_emergency=True; b.status='pending'; b.updated_at=datetime.utcnow(); notify(b.worker.user_id,'🚨 Emergency booking','Customer marked booking #%s as EMERGENCY.'%b.id); db.session.add(e); db.session.commit(); flash('Emergency request sent to the worker.','success'); return redirect(url_for('booking.detail',booking_id=b.id))

@features_bp.route('/booking/<int:booking_id>/worker-location',methods=['POST'])
@login_required
def worker_location(booking_id):
    b=Booking.query.get_or_404(booking_id)
    if not current_user.is_worker or b.worker_id!=current_user.worker_profile.id: return jsonify(ok=False),403
    try: lat=float(request.form.get('latitude')); lng=float(request.form.get('longitude'))
    except: return jsonify(ok=False),400
    e=BookingExtra.query.filter_by(booking_id=b.id).first() or BookingExtra(booking_id=b.id)
    e.worker_latitude=lat; e.worker_longitude=lng; e.worker_location_updated_at=datetime.utcnow(); db.session.add(e); db.session.commit(); notify(b.customer_id,'Worker location updated',f'Worker location for booking #{b.id} was updated.'); db.session.commit(); return jsonify(ok=True)

@features_bp.route('/booking/<int:booking_id>/apply-coupon',methods=['POST'])
@login_required
def apply_coupon(booking_id):
    b=Booking.query.get_or_404(booking_id)
    if current_user.id!=b.customer_id: return 'Forbidden',403
    code=request.form.get('code','').strip().upper(); c=Coupon.query.filter_by(code=code,is_active=True).first()
    if not c or (c.expires_at and c.expires_at<datetime.utcnow()): flash('Invalid or expired coupon.','danger'); return redirect(url_for('booking.detail',booking_id=b.id))
    discount=min((b.price or 0)*c.discount_percent/100,c.max_discount or (b.price or 0)); e=BookingExtra.query.filter_by(booking_id=b.id).first() or BookingExtra(booking_id=b.id); e.coupon_code=c.code; e.discount_amount=round(discount,2); db.session.add(e); db.session.commit(); flash(f'Coupon applied. You saved ₹{discount:.0f}.','success'); return redirect(url_for('booking.detail',booking_id=b.id))

# ---------- Advanced customer features ----------
@features_bp.route('/booking/<int:booking_id>/verify-otp', methods=['POST'])
@login_required
def verify_otp(booking_id):
    b=Booking.query.get_or_404(booking_id)
    if current_user.id != b.customer_id: return 'Forbidden',403
    e=BookingExtra.query.filter_by(booking_id=b.id).first()
    if not e or not e.completion_otp or request.form.get('otp','').strip() != e.completion_otp:
        flash('Invalid completion OTP.', 'danger')
        return redirect(url_for('booking.detail', booking_id=b.id))
    e.completion_otp_verified=True; db.session.commit()
    flash('OTP verified. Worker can now mark the job completed.', 'success')
    return redirect(url_for('booking.detail', booking_id=b.id))

@features_bp.route('/booking/<int:booking_id>/proof', methods=['POST'])
@login_required
def upload_proof(booking_id):
    b=Booking.query.get_or_404(booking_id)
    if not current_user.is_worker or b.worker.user_id != current_user.id: return 'Forbidden',403
    file=request.files.get('proof')
    if not file or not file.filename:
        flash('Choose a proof image/file.', 'danger'); return redirect(url_for('worker.booking_detail', booking_id=b.id))
    from werkzeug.utils import secure_filename
    name=secure_filename(file.filename)
    filename=f'proof_{b.id}_{int(datetime.utcnow().timestamp())}_{name}'
    path=__import__('os').path.join(__import__('flask').current_app.config['UPLOAD_FOLDER'], filename)
    file.save(path)
    e=BookingExtra.query.filter_by(booking_id=b.id).first() or BookingExtra(booking_id=b.id)
    e.proof_filename=filename; db.session.add(e); db.session.commit()
    flash('Completion proof uploaded.', 'success'); return redirect(url_for('worker.booking_detail', booking_id=b.id))

@features_bp.route('/booking/<int:booking_id>/directions')
@login_required
def directions(booking_id):
    b=Booking.query.get_or_404(booking_id)
    if current_user.id not in (b.customer_id, b.worker.user_id): return 'Forbidden',403
    if not b.latitude or not b.longitude:
        flash('Booking does not have GPS coordinates.', 'info'); return redirect(url_for('booking.detail', booking_id=b.id))
    import urllib.parse
    target=f'{b.latitude},{b.longitude}'
    maps='https://www.google.com/maps/dir/?api=1&destination='+urllib.parse.quote(target)
    return redirect(maps)

@features_bp.route('/support', methods=['GET','POST'])
@login_required
def support():
    from models.advanced import Complaint
    if request.method=='POST':
        subject=request.form.get('subject','').strip(); message=request.form.get('message','').strip()
        if not subject or not message: flash('Subject and message are required.','danger')
        else:
            db.session.add(Complaint(user_id=current_user.id, booking_id=request.form.get('booking_id') or None, subject=subject, message=message))
            db.session.commit(); flash('Support request submitted.','success'); return redirect(url_for('features.support'))
    complaints=Complaint.query.filter_by(user_id=current_user.id).order_by(Complaint.created_at.desc()).all()
    return render_template('features/support.html', complaints=complaints)

@features_bp.route('/addresses', methods=['GET','POST'])
@login_required
def addresses():
    from models.advanced import Address
    if request.method=='POST':
        address=request.form.get('address','').strip(); label=request.form.get('label','Home').strip() or 'Home'
        if address:
            if request.form.get('is_default')=='on':
                Address.query.filter_by(user_id=current_user.id).update({'is_default':False})
            db.session.add(Address(user_id=current_user.id,label=label,address=address,is_default=request.form.get('is_default')=='on'))
            db.session.commit(); flash('Address saved.','success')
    return render_template('features/addresses.html', addresses=Address.query.filter_by(user_id=current_user.id).order_by(Address.created_at.desc()).all())

@features_bp.route('/addresses/<int:address_id>/delete', methods=['POST'])
@login_required
def delete_address(address_id):
    from models.advanced import Address
    a=Address.query.filter_by(id=address_id,user_id=current_user.id).first_or_404(); db.session.delete(a); db.session.commit(); flash('Address removed.','info'); return redirect(url_for('features.addresses'))

@features_bp.route('/rewards')
@login_required
def rewards():
    return render_template('features/rewards.html')

@features_bp.route('/payments')
@login_required
def payments():
    from models.advanced import Payment
    if not current_user.is_customer:
        return redirect(url_for('main.home'))
    items = Payment.query.filter_by(customer_id=current_user.id).order_by(Payment.created_at.desc()).all()
    total = sum(p.amount for p in items if p.status == 'paid')
    pending = sum(p.amount for p in items if p.status == 'pending')
    return render_template('features/payments.html', payments=items, total=total, pending=pending)

@features_bp.route('/booking/<int:booking_id>/pay')
@login_required
def pay_booking(booking_id):
    """Open checkout. Uses Razorpay when configured; otherwise uses a safe local demo payment."""
    from models.advanced import Payment
    if not current_user.is_customer:
        return 'Forbidden', 403
    booking = Booking.query.filter_by(id=booking_id, customer_id=current_user.id).first_or_404()
    if booking.status != 'completed':
        flash('Payment is available after the booking is completed.', 'warning')
        return redirect(url_for('booking.detail', booking_id=booking.id))
    amount = round(max(0, booking.price or 0), 2)
    if amount <= 0:
        flash('This booking has no payable amount.', 'warning')
        return redirect(url_for('booking.detail', booking_id=booking.id))
    payment = Payment.query.filter_by(booking_id=booking.id).first()
    if payment and payment.status == 'paid':
        flash('This booking is already paid.', 'info')
        return redirect(url_for('features.payments'))

    import uuid
    if not payment:
        commission = round(amount * 0.10, 2)
        payment = Payment(
            booking_id=booking.id, customer_id=current_user.id,
            worker_id=booking.worker_id, amount=amount,
            commission_amount=commission, worker_amount=round(amount-commission, 2),
            method='Demo Payment', status='pending',
            transaction_id='DFS-PENDING-' + uuid.uuid4().hex[:12].upper()
        )
        db.session.add(payment)
        db.session.commit()

    razorpay_enabled = bool(current_app.config.get('RAZORPAY_KEY_ID') and current_app.config.get('RAZORPAY_KEY_SECRET'))
    if razorpay_enabled:
        import razorpay
        client = razorpay.Client(auth=(current_app.config['RAZORPAY_KEY_ID'], current_app.config['RAZORPAY_KEY_SECRET']))
        if not payment.razorpay_order_id:
            order = client.order.create({
                'amount': int(round(amount * 100)), 'currency': 'INR',
                'receipt': f'dfs_booking_{booking.id}',
                'notes': {'booking_id': str(booking.id)}
            })
            payment.razorpay_order_id = order['id']
            payment.method = 'Razorpay'
            db.session.commit()
        return render_template('features/checkout.html', booking=booking, payment=payment,
                               razorpay_key=current_app.config['RAZORPAY_KEY_ID'], razorpay_enabled=True)

    return render_template('features/checkout.html', booking=booking, payment=payment,
                           razorpay_key='', razorpay_enabled=False)

@features_bp.route('/booking/<int:booking_id>/demo-payment', methods=['POST'])
@login_required
def demo_payment(booking_id):
    """Local/test payment: no bank, UPI or card is charged."""
    from models.advanced import Payment, WorkerEarning
    if not current_user.is_customer:
        return 'Forbidden', 403
    booking = Booking.query.filter_by(id=booking_id, customer_id=current_user.id).first_or_404()
    if booking.status != 'completed':
        flash('Payment is available after the booking is completed.', 'warning')
        return redirect(url_for('booking.detail', booking_id=booking.id))
    amount = round(max(0, booking.price or 0), 2)
    if amount <= 0:
        flash('This booking has no payable amount.', 'warning')
        return redirect(url_for('booking.detail', booking_id=booking.id))
    payment = Payment.query.filter_by(booking_id=booking.id).first()
    import uuid
    if not payment:
        commission = round(amount * 0.10, 2)
        payment = Payment(booking_id=booking.id, customer_id=current_user.id, worker_id=booking.worker_id,
                          amount=amount, commission_amount=commission, worker_amount=round(amount-commission, 2),
                          method='Demo Payment', status='pending',
                          transaction_id='DFS-PENDING-' + uuid.uuid4().hex[:12].upper())
        db.session.add(payment)
    if payment.status != 'paid':
        payment.status = 'paid'
        payment.method = 'Demo Payment'
        payment.transaction_id = 'DFS-DEMO-' + uuid.uuid4().hex[:12].upper()
        if not WorkerEarning.query.filter_by(booking_id=booking.id).first():
            db.session.add(WorkerEarning(worker_id=booking.worker_id, booking_id=booking.id,
                                         gross_amount=payment.amount, commission_amount=payment.commission_amount,
                                         net_amount=payment.worker_amount))
        db.session.commit()
    flash('Demo payment successful. No real money was charged.', 'success')
    return redirect(url_for('features.payments'))

@features_bp.route('/booking/<int:booking_id>/payment-success', methods=['POST'])
@login_required
def payment_success(booking_id):
    from models.advanced import Payment, WorkerEarning
    if not current_user.is_customer:
        return 'Forbidden', 403
    booking = Booking.query.filter_by(id=booking_id, customer_id=current_user.id).first_or_404()
    payment = Payment.query.filter_by(booking_id=booking.id).first_or_404()
    if payment.status == 'paid':
        return jsonify({'ok': True, 'redirect': url_for('features.payments')})
    if not current_app.config.get('RAZORPAY_KEY_SECRET'):
        return jsonify({'ok': False, 'message': 'Razorpay secret is not configured.'}), 503
    razorpay_payment_id = request.form.get('razorpay_payment_id','').strip()
    razorpay_order_id = request.form.get('razorpay_order_id','').strip()
    razorpay_signature = request.form.get('razorpay_signature','').strip()
    if not razorpay_payment_id or not razorpay_order_id or not razorpay_signature or razorpay_order_id != payment.razorpay_order_id:
        return jsonify({'ok': False, 'message': 'Invalid payment response.'}), 400
    import razorpay
    client = razorpay.Client(auth=(current_app.config['RAZORPAY_KEY_ID'], current_app.config['RAZORPAY_KEY_SECRET']))
    try:
        client.utility.verify_payment_signature({'razorpay_order_id': razorpay_order_id, 'razorpay_payment_id': razorpay_payment_id, 'razorpay_signature': razorpay_signature})
    except Exception:
        return jsonify({'ok': False, 'message': 'Payment signature verification failed.'}), 400
    payment.status='paid'; payment.method='Razorpay'; payment.razorpay_payment_id=razorpay_payment_id; payment.razorpay_signature=razorpay_signature; payment.transaction_id=razorpay_payment_id
    if not WorkerEarning.query.filter_by(booking_id=booking.id).first():
        db.session.add(WorkerEarning(worker_id=booking.worker_id, booking_id=booking.id, gross_amount=payment.amount, commission_amount=payment.commission_amount, net_amount=payment.worker_amount))
    db.session.commit()
    flash('Payment successful. Thank you!', 'success')
    return jsonify({'ok': True, 'redirect': url_for('features.payments')})

@features_bp.route('/language/<lang>')
def language(lang):
    from flask import session
    session['lang'] = 'hi' if lang == 'hi' else 'en'
    return redirect(request.referrer or url_for('main.home'))
