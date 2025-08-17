import datetime
from . import db

# Helper table for the many-to-many relationship between contacts and tags
contact_tags = db.Table('contact_tags',
    db.Column('tag_id', db.Integer, db.ForeignKey('tags.id'), primary_key=True),
    db.Column('contact_id', db.Integer, db.ForeignKey('contacts.id'), primary_key=True)
)

class Tag(db.Model):
    __tablename__ = 'tags'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

    def __repr__(self):
        return f'<Tag {self.name}>'

class Contact(db.Model):
    __tablename__ = 'contacts'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    phone = db.Column(db.String(25), unique=True, nullable=False)
    source = db.Column(db.String(150), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)

    tags = db.relationship('Tag', secondary=contact_tags,
                           lazy='subquery',
                           backref=db.backref('contacts', lazy=True))

    def __repr__(self):
        return f'<Contact {self.name}>'

# Helper table for the many-to-many relationship between campaigns and tags
campaign_tags = db.Table('campaign_tags',
    db.Column('tag_id', db.Integer, db.ForeignKey('tags.id'), primary_key=True),
    db.Column('campaign_id', db.Integer, db.ForeignKey('campaigns.id'), primary_key=True)
)

# Helper table to track which contacts received which campaign
campaign_recipients = db.Table('campaign_recipients',
    db.Column('contact_id', db.Integer, db.ForeignKey('contacts.id'), primary_key=True),
    db.Column('campaign_id', db.Integer, db.ForeignKey('campaigns.id'), primary_key=True)
)

class Campaign(db.Model):
    __tablename__ = 'campaigns'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=True, nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)

    # The tags that define the audience for this campaign
    tags = db.relationship('Tag', secondary=campaign_tags,
                           lazy='subquery',
                           backref=db.backref('campaigns', lazy=True))

    # The contacts who have received this campaign
    recipients = db.relationship('Contact', secondary=campaign_recipients,
                                 lazy='subquery',
                                 backref=db.backref('campaigns_received', lazy=True))

    def __repr__(self):
        return f'<Campaign {self.name}>'

class MessageTemplate(db.Model):
    __tablename__ = 'message_templates'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    body = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f'<MessageTemplate {self.name}>'
