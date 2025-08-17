from flask import Blueprint, render_template, request, flash, redirect, url_for, send_file
from openpyxl import Workbook
from io import BytesIO
from datetime import datetime
from .models import Contact, Tag, Campaign
from . import db

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    return redirect(url_for('main.dashboard'))

@bp.route('/dashboard')
def dashboard():
    # Calculate stats
    total_contacts = Contact.query.count()

    today = datetime.utcnow().date()
    first_day_of_month = today.replace(day=1)
    new_contacts_monthly = Contact.query.filter(Contact.created_at >= first_day_of_month).count()

    campaigns_sent = Campaign.query.filter(Campaign.recipients.any()).count()

    stats = {
        'total_contacts': total_contacts,
        'new_contacts_monthly': new_contacts_monthly,
        'campaigns_sent': campaigns_sent
    }

    # Fetch recent campaigns
    recent_campaigns = Campaign.query.filter(Campaign.recipients.any()).order_by(Campaign.created_at.desc()).limit(5).all()

    return render_template('dashboard.html', stats=stats, recent_campaigns=recent_campaigns)

@bp.route('/contacts')
def list_contacts():
    contacts = Contact.query.order_by(Contact.created_at.desc()).all()
    return render_template('contacts.html', contacts=contacts)

@bp.route('/campaigns/new', methods=('GET', 'POST'))
def new_campaign():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'save_draft':
            name = request.form.get('campaign_name')
            message = request.form.get('message')
            tags_string = request.form.get('tags', '')

            if not name or not message:
                flash('اسم الحملة ونص الرسالة حقول إلزامية.', 'danger')
                return render_template('new_campaign.html')

            # Create the campaign
            new_campaign = Campaign(name=name, message=message)
            db.session.add(new_campaign) # Add to session before creating relationships

            # Handle tags
            if tags_string:
                tag_names = [name.strip() for name in tags_string.split(',') if name.strip()]
                for tag_name in tag_names:
                    tag = Tag.query.filter_by(name=tag_name).first()
                    if not tag:
                        tag = Tag(name=tag_name)
                        db.session.add(tag)
                    new_campaign.tags.append(tag)

            db.session.commit()

            flash(f'تم حفظ الحملة "{name}" كمسودة بنجاح!', 'success')
            return redirect(url_for('main.new_campaign'))

        # The 'export' action will be handled in the next step
        elif action == 'export':
            name = request.form.get('campaign_name')
            message = request.form.get('message')
            tags_string = request.form.get('tags', '')
            use_shield = request.form.get('anti_spam_shield_active') == 'on'

            if not name or not message:
                flash('اسم الحملة ونص الرسالة حقول إلزامية للتصدير.', 'danger')
                return render_template('new_campaign.html')

            # Find or create campaign object
            campaign = Campaign.query.filter_by(name=name).first()
            if not campaign:
                campaign = Campaign(name=name, message=message)
                db.session.add(campaign)
            else: # if campaign exists, update its message
                campaign.message = message

            # Find or create tag objects and associate them with the campaign
            campaign.tags.clear()
            tag_names = [name.strip() for name in tags_string.split(',') if name.strip()]
            for tag_name in tag_names:
                tag = Tag.query.filter_by(name=tag_name).first()
                if not tag:
                    tag = Tag(name=tag_name)
                    db.session.add(tag)
                campaign.tags.append(tag)

            # Determine final recipient list
            query = Contact.query
            if tag_names:
                for tag_name in tag_names:
                    query = query.filter(Contact.tags.any(name=tag_name))

            if use_shield:
                # Get IDs of contacts who have already received this campaign
                existing_recipient_ids = [r.id for r in campaign.recipients]
                if existing_recipient_ids:
                    query = query.filter(Contact.id.notin_(existing_recipient_ids))

            final_recipients = query.all()

            if not final_recipients:
                flash('لا يوجد مستلمين جدد لهذه الحملة.', 'warning')
                return redirect(url_for('main.new_campaign'))

            # Log new recipients and prepare data for Excel
            excel_data = []
            for contact in final_recipients:
                campaign.recipients.append(contact)
                personalized_message = message.replace('[الاسم]', contact.name)
                excel_data.append([contact.phone, personalized_message])

            db.session.commit()

            # Create Excel file in memory
            wb = Workbook()
            ws = wb.active
            ws.title = "Campaign Export"
            ws.append(['PhoneNumber', 'Message']) # Add headers
            for row in excel_data:
                ws.append(row)

            # Save to a virtual file
            target = BytesIO()
            wb.save(target)
            target.seek(0)

            flash(f'تم تصدير {len(final_recipients)} جهة اتصال بنجاح!', 'success')

            return send_file(
                target,
                as_attachment=True,
                download_name=f'{name}_export.xlsx',
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )

    return render_template('new_campaign.html')

@bp.route('/contacts/<int:contact_id>/edit', methods=('GET', 'POST'))
def edit_contact(contact_id):
    contact = Contact.query.get_or_404(contact_id)

    if request.method == 'POST':
        tags_string = request.form.get('tags', '').strip()
        if tags_string:
            tag_names = [name.strip() for name in tags_string.split(',') if name.strip()]

            for name in tag_names:
                # Check if tag already exists
                tag = Tag.query.filter_by(name=name).first()
                if not tag:
                    # If not, create it
                    tag = Tag(name=name)
                    db.session.add(tag)

                # Add the tag to the contact if it's not already there
                if tag not in contact.tags:
                    contact.tags.append(tag)

            db.session.commit()
            flash('تم تحديث الوسوم بنجاح!', 'success')
        return redirect(url_for('main.edit_contact', contact_id=contact.id))

    return render_template('edit_contact.html', contact=contact)

@bp.route('/contacts/new', methods=('GET', 'POST'))
def add_contact():
    # This page is now secondary, but the logic is still needed.
    # It might be converted to a modal dialog in the future.
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
