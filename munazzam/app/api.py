from flask import Blueprint, request, jsonify
from .models import Contact, Tag, Campaign

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
