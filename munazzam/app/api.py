from flask import Blueprint, request, jsonify
from .models import Contact, Tag, Campaign, MessageTemplate
from . import db

bp = Blueprint('api', __name__, url_prefix='/api')

@bp.route('/contacts/count', methods=['POST'])
def get_contact_count_by_tags():
    data = request.get_json()
    tag_names = data.get('tags', [])
    exclude_campaign_name = data.get('exclude_campaign_name')

    # Start a query for contacts
    query = Contact.query

    # Filter by contacts that have ALL of the specified tags
    if tag_names:
        for tag_name in tag_names:
            query = query.filter(Contact.tags.any(name=tag_name))

    # Handle the "Anti-Annoyance Shield"
    if exclude_campaign_name:
        campaign = Campaign.query.filter_by(name=exclude_campaign_name).first()
        if campaign:
            # Get IDs of contacts who have already received this campaign
            recipient_ids = [r.id for r in campaign.recipients]
            if recipient_ids:
                query = query.filter(Contact.id.notin_(recipient_ids))

    count = query.count()

    return jsonify({'count': count})

@bp.route('/templates', methods=['GET'])
def get_templates():
    templates = MessageTemplate.query.order_by(MessageTemplate.name).all()
    return jsonify([{'id': t.id, 'name': t.name, 'body': t.body} for t in templates])

@bp.route('/templates', methods=['POST'])
def create_template():
    data = request.get_json()
    name = data.get('name')
    body = data.get('body')

    if not name or not body:
        return jsonify({'error': 'Name and body are required.'}), 400

    if MessageTemplate.query.filter_by(name=name).first():
        return jsonify({'error': 'A template with this name already exists.'}), 409

    new_template = MessageTemplate(name=name, body=body)
    db.session.add(new_template)
    db.session.commit()

    return jsonify({'id': new_template.id, 'name': new_template.name, 'body': new_template.body}), 201
