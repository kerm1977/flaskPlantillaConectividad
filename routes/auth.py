from datetime import datetime
from flask import request, jsonify, session, redirect, url_for, render_template
from models import User
from users import hash_password, check_password
from db import db
from routes import bp
from security import check_rate_limit, validate_password_strength


@bp.route('/login')
def login_page():
    if 'user_id' in session:
        return redirect(url_for('main.home'))
    return render_template('login.html')


@bp.route('/register')
def register_page():
    if 'user_id' in session:
        return redirect(url_for('main.home'))
    return render_template('register.html')


@bp.route('/api/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email', '').lower()
    
    if not check_rate_limit(email):
        return jsonify({'error': 'Demasiados intentos. Espere 15 minutos.'}), 429
    
    user = User.query.filter_by(email=email).first()
    if user and check_password(data.get('password'), user.password_hash):
        if user.status == 'Bloqueado':
            return jsonify({'error': 'Usuario bloqueado'}), 403
        session['user_id'] = user.id
        session['role'] = user.role
        session['avatar'] = user.avatar or 'default.png'
        return jsonify({'success': True})
    return jsonify({'error': 'Credenciales inválidas'}), 401


@bp.route('/api/register', methods=['POST'])
def register():
    data = request.json
    password = data.get('password', '')
    
    valid, msg = validate_password_strength(password)
    if not valid:
        return jsonify({'error': msg}), 400
    
    if User.query.filter_by(email=data.get('email').lower()).first():
        return jsonify({'error': 'Email ya registrado'}), 400
        
    try:
        new_user = User(
            name=data.get('name'),
            last_name_1=data.get('last_name_1'),
            last_name_2=data.get('last_name_2'),
            email=data.get('email').lower(),
            password_hash=hash_password(password)
        )
        
        if data.get('phone_code'): new_user.phone_code = data.get('phone_code')
        if data.get('phone'): new_user.phone = data.get('phone')
        if data.get('dob'): new_user.dob = datetime.strptime(data.get('dob'), '%Y-%m-%d').date()

        if data.get('whatsapp') and hasattr(new_user, 'whatsapp'): new_user.whatsapp = data.get('whatsapp')
        if data.get('facebook') and hasattr(new_user, 'facebook'): new_user.facebook = data.get('facebook')
        if data.get('instagram') and hasattr(new_user, 'instagram'): new_user.instagram = data.get('instagram')
        if data.get('address') and hasattr(new_user, 'address'): new_user.address = data.get('address')
        if data.get('institution') and hasattr(new_user, 'institution'): new_user.institution = data.get('institution')
        if data.get('other_info') and hasattr(new_user, 'other_info'): new_user.other_info = data.get('other_info')

        db.session.add(new_user)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback() 
        return jsonify({'error': str(e)}), 500



@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.home'))

