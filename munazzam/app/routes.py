from flask import Blueprint, render_template, request, flash, redirect, url_for
from .models import Contact
from . import db

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    return redirect(url_for('main.list_contacts'))

@bp.route('/contacts')
def list_contacts():
    contacts = Contact.query.order_by(Contact.created_at.desc()).all()
    return render_template('contacts.html', contacts=contacts)

@bp.route('/contacts/new', methods=('GET', 'POST'))
def add_contact():
    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']
        source = request.form.get('source') # .get() is safer for optional fields

        error = None

        if not name:
            error = 'الاسم مطلوب.'
        elif not phone:
            error = 'رقم الهاتف مطلوب.'

        # Check if phone number already exists
        if error is None:
            existing_contact = Contact.query.filter_by(phone=phone).first()
            if existing_contact:
                error = f'رقم الهاتف {phone} مسجل بالفعل.'

        if error is None:
            # No errors, so create the contact and save to DB
            new_contact = Contact(name=name, phone=phone, source=source)
            db.session.add(new_contact)
            db.session.commit()
            flash('تمت إضافة جهة الاتصال بنجاح!', 'success')
            return redirect(url_for('main.add_contact'))

        # If there was an error, show it to the user
        flash(error, 'danger')

    return render_template('add_contact.html')
