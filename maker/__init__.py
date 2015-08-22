from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy

from flask.ext.migrate import Migrate
import calendar
import config

app = Flask(__name__)

app.config['WTF_CSRF_ENABLED'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = config.BOOK_DB
app.debug = True

db = SQLAlchemy(app)
migrate = Migrate(app, db)

knows = db.Table('knows',
    db.Column('person_knows_id', db.Integer, db.ForeignKey('person.id')),
    db.Column('person_known_id', db.Integer, db.ForeignKey('person.id'))
    )

related = db.Table('related',
    db.Column('person_left_id', db.Integer, db.ForeignKey('person.id')),
    db.Column('person_right_id', db.Integer, db.ForeignKey('person.id'))
    )

parents = db.Table('parents',
    db.Column('child_id', db.Integer, db.ForeignKey('person.id')),
    db.Column('parent_id', db.Integer, db.ForeignKey('person.id'))
    )

spouses = db.Table('spouses',
    db.Column('spouse_left_id', db.Integer, db.ForeignKey('person.id')),
    db.Column('spouse_right_id', db.Integer, db.ForeignKey('person.id'))
    )

siblings = db.Table('siblings',
    db.Column('sibling_left_id', db.Integer, db.ForeignKey('person.id')),
    db.Column('sibling_right_id', db.Integer, db.ForeignKey('person.id'))
    )

membership = db.Table('membership',
    db.Column('person_id', db.Integer, db.ForeignKey('person.id')),
    db.Column('organisation_id', db.Integer, db.ForeignKey('organisation.id'))  
    )

employment = db.Table('employment',
    db.Column('person_id', db.Integer, db.ForeignKey('person.id')),
    db.Column('organisation_id', db.Integer, db.ForeignKey('organisation.id'))  
    )

person_same_as = db.Table('person_same_as',
    db.Column('person_id', db.Integer, db.ForeignKey('person.id')),
    db.Column('identifier_id', db.Integer, db.ForeignKey('identifier.id'))
    )

class DateMixin(object):

    def __repr__(self):
          return unicode(self.__dict__)

    def display_date(self, date, exact_month, exact_day, format):
        display_date = ''
        if date:
            year = date.year
            month = date.month
            day = date.day
            if not exact_month:
                month = None
                day = None
            elif not exact_day:
                day = None
            if format == 'iso':
                display_date = self.display_iso_date(year, month, day)
            elif format == 'pretty':
                display_date = self.display_pretty_date(year, month, day)
        return display_date

    def display_iso_date(self, year, month, day):
        if day:
            display_date = '{}-{}-{}'.format(year, str(month).zfill(2), str(day).zfill(2))
        elif month:
            display_date = '{}-{}'.format(year, str(month).zfill(2))
        else:
            display_date = str(year)
        return display_date

    def display_pretty_date(self, year, month, day):
        if month:
            month = calendar.month_name[month]
        if day:
            display_date = '{} {} {}'.format(day, str(month).zfill(2), year)
        elif month:
            display_date = '{} {}'.format(str(month).zfill(2), year)
        else:
            display_date = str(year)
        return display_date


class Person(db.Model, DateMixin):
    id = db.Column(db.Integer, primary_key=True)
    blank_node = db.Column(db.Boolean)
    name = db.Column(db.String(100))
    family_name = db.Column(db.String(100))
    given_name = db.Column(db.String(100))
    other_name = db.Column(db.String(100))
    birth_date = db.Column(db.Date)
    birth_date_month = db.Column(db.Boolean)
    birth_date_day = db.Column(db.Boolean)
    birth_place_id = db.Column(db.Integer, db.ForeignKey('place.id'))
    birth_place = db.relationship('Place', foreign_keys='Person.birth_place_id')
    death_date = db.Column(db.Date)
    death_date_month = db.Column(db.Boolean)
    death_date_day = db.Column(db.Boolean)
    death_place_id = db.Column(db.Integer, db.ForeignKey('place.id'))
    death_place = db.relationship('Place', foreign_keys='Person.death_place_id')
    url = db.Column(db.String(100))
    img_url = db.Column(db.String(100))
    knows = db.relationship('Person',
                                secondary='knows',
                                primaryjoin='Person.id==knows.c.person_knows_id',
                                secondaryjoin='Person.id==knows.c.person_known_id',
                                backref='knownby'
                                )
    related_to = db.relationship('Person',
                                secondary='related',
                                primaryjoin='Person.id==related.c.person_left_id',
                                secondaryjoin='Person.id==related.c.person_right_id',
                                backref='related_back'
                                )
    parents = db.relationship('Person',
                                secondary='parents',
                                primaryjoin='Person.id==parents.c.child_id',
                                secondaryjoin='Person.id==parents.c.parent_id',
                                backref='children'
                                )
    spouses = db.relationship('Person',
                                secondary='spouses',
                                primaryjoin='Person.id==spouses.c.spouse_left_id',
                                secondaryjoin='Person.id==spouses.c.spouse_right_id',
                                backref='spouses_back'
                                )
    siblings = db.relationship('Person',
                                secondary='siblings',
                                primaryjoin='Person.id==siblings.c.sibling_left_id',
                                secondaryjoin='Person.id==siblings.c.sibling_right_id',
                                backref='siblings_back'
                                )
    member_of = db.relationship('Organisation', secondary='membership', backref='members')
    employee_of = db.relationship('Organisation', secondary='employment', backref='employees')
    same_as = db.relationship('Identifier', secondary='person_same_as')

    def __repr__(self):
        return '<Person {!r}>'.format(self.name)

    def knows_all(self):
        knows_all = []
        knows = self.knows
        known_by = self.knownby
        knows_all = list(set(knows) | set(known_by))
        knows_all = sorted(knows_all, key=lambda k: k.name)
        return knows_all

    def related_all(self):
        related_to = self.related_to
        related_back = self.related_back
        related_all = list(set(related_to) | set(related_back))
        related_all = sorted(related_all, key=lambda k: k.name)
        return related_all

    def spouse_all(self):
        spouse_to = self.spouses
        spouse_back = self.spouses_back
        spouse_all = list(set(spouse_to) | set(spouse_back))
        spouse_all = sorted(spouse_all, key=lambda k: k.name)
        return spouse_all

    def sibling_all(self):
        sibling_to = self.siblings
        sibling_back = self.siblings_back
        sibling_all = list(set(sibling_to) | set(sibling_back))
        sibling_all = sorted(sibling_all, key=lambda k: k.name)
        return sibling_all

    def display_birth_date(self, format='iso'):
        return self.display_date(
            self.birth_date, 
            self.birth_date_month, 
            self.birth_date_day,
            format
            )

    def display_death_date(self, format='iso'):
        return self.display_date(
            self.death_date, 
            self.death_date_month, 
            self.death_date_day,
            format
            )        

sub_organisations = db.Table('sub_organisations',
    db.Column('organisation_id', db.Integer, db.ForeignKey('organisation.id')),
    db.Column('sub_organisation_id', db.Integer, db.ForeignKey('organisation.id'))
    )

organisation_same_as = db.Table('organisation_same_as',
    db.Column('organisation_id', db.Integer, db.ForeignKey('organisation.id')),
    db.Column('identifier_id', db.Integer, db.ForeignKey('identifier.id'))
    )

class Organisation(db.Model, DateMixin):
    id = db.Column(db.Integer, primary_key=True)
    blank_node = db.Column(db.Boolean)
    name = db.Column(db.String(100))
    alternate_name = db.Column(db.String(100))
    #Start date
    founding_date = db.Column(db.Date)
    founding_date_month = db.Column(db.Boolean)
    founding_date_day = db.Column(db.Boolean)
    #End date
    dissolution_date = db.Column(db.Date)
    dissolution_date_month = db.Column(db.Boolean)
    dissolution_date_day = db.Column(db.Boolean)
    location_id = db.Column(db.Integer, db.ForeignKey('place.id'))
    location = db.relationship('Place', foreign_keys='Organisation.location_id')
    has_parts = db.relationship('Organisation',
                            secondary='sub_organisations',
                            primaryjoin='Organisation.id==sub_organisations.c.organisation_id',
                            secondaryjoin='Organisation.id==sub_organisations.c.sub_organisation_id',
                            backref='part_of'
                            )
    url = db.Column(db.String(100))
    img_url = db.Column(db.String(100))
    image_id = db.Column(db.Integer, db.ForeignKey('image.id'))
    image = db.relationship('Image', foreign_keys='Organisation.image_id')
    same_as = db.relationship('Identifier', secondary='organisation_same_as')

    def __repr__(self):
        return '<Organisation {!r}>'.format(self.name)

    def display_founding_date(self, format='iso'):
        return self.display_date(
            self.founding_date, 
            self.founding_date_month, 
            self.founding_date_day,
            format
            )

    def display_dissolution_date(self, format='iso'):
        return self.display_date(
            self.dissolution_date, 
            self.dissolution_date_month, 
            self.dissolution_date_day,
            format
            ) 

place_containers = db.Table('place_containers',
    db.Column('contained_id', db.Integer, db.ForeignKey('place.id')),
    db.Column('container_id', db.Integer, db.ForeignKey('place.id'))
    )

place_same_as = db.Table('place_same_as',
    db.Column('place_id', db.Integer, db.ForeignKey('place.id')),
    db.Column('identifier_id', db.Integer, db.ForeignKey('identifier.id'))
    )

class Place(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    blank_node = db.Column(db.Boolean)
    place_type = db.Column(db.String(20))
    name = db.Column(db.String(100))
    alternate_name = db.Column(db.String(100))
    url = db.Column(db.String(100))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    contained_in = db.relationship('Place',
                            secondary='place_containers',
                            primaryjoin='Place.id==place_containers.c.contained_id',
                            secondaryjoin='Place.id==place_containers.c.container_id',
                            backref='containing'
                            )
    img_url = db.Column(db.String(100))
    image_id = db.Column(db.Integer, db.ForeignKey('image.id'))
    image = db.relationship('Image', foreign_keys='Place.image_id')
    same_as = db.relationship('Identifier', secondary='place_same_as')

    def __repr__(self):
        return '<Place {!r}>'.format(self.name)

event_containers = db.Table('event_containers',
    db.Column('contained_id', db.Integer, db.ForeignKey('event.id')),
    db.Column('container_id', db.Integer, db.ForeignKey('event.id'))
    )

performers = db.Table('performers',
    db.Column('person_id', db.Integer, db.ForeignKey('person.id')),
    db.Column('event_id', db.Integer, db.ForeignKey('event.id'))  
    )

attendees = db.Table('attendees',
    db.Column('person_id', db.Integer, db.ForeignKey('person.id')),
    db.Column('event_id', db.Integer, db.ForeignKey('event.id'))  
    )

event_same_as = db.Table('event_same_as',
    db.Column('event_id', db.Integer, db.ForeignKey('event.id')),
    db.Column('identifier_id', db.Integer, db.ForeignKey('identifier.id'))
    )

class Event(db.Model, DateMixin):
    id = db.Column(db.Integer, primary_key=True)
    blank_node = db.Column(db.Boolean)
    name = db.Column(db.String(100))
    alternate_name = db.Column(db.String(100))
    url = db.Column(db.String(100))
    img_url = db.Column(db.String(100))
    #Start date
    start_date = db.Column(db.Date)
    start_date_month = db.Column(db.Boolean)
    start_date_day = db.Column(db.Boolean)
    #End date
    end_date = db.Column(db.Date)
    end_date_month = db.Column(db.Boolean)
    end_date_day = db.Column(db.Boolean)
    location_id = db.Column(db.Integer, db.ForeignKey('place.id'))
    location = db.relationship('Place', foreign_keys='Event.location_id')
    super_event = db.relationship('Event',
                        secondary='event_containers',
                        primaryjoin='Event.id==event_containers.c.contained_id',
                        secondaryjoin='Event.id==event_containers.c.container_id',
                        backref='containing'
                        )
    performers = db.relationship('Person', secondary='performers', backref='performed')
    attendees = db.relationship('Person', secondary='attendees', backref='attended')
    image_id = db.Column(db.Integer, db.ForeignKey('image.id'))
    image = db.relationship('Image', foreign_keys='Event.image_id')
    same_as = db.relationship('Identifier', secondary='event_same_as')

    def __repr__(self):
        return '<Event {!r}>'.format(self.name)

    def display_start_date(self, format='iso'):
        return self.display_date(
            self.start_date, 
            self.start_date_month, 
            self.start_date_day,
            format
            )

    def display_end_date(self, format='iso'):
        return self.display_date(
            self.end_date, 
            self.end_date_month, 
            self.end_date_day,
            format
            )

parts = db.Table('parts',
    db.Column('member_id', db.Integer, db.ForeignKey('resource.id')),
    db.Column('collection_id', db.Integer, db.ForeignKey('resource.id'))
    )

creators = db.Table('creators',
    db.Column('creator_id', db.Integer, db.ForeignKey('person.id')),
    db.Column('resource_id', db.Integer, db.ForeignKey('resource.id'))  
    )

about_people = db.Table('about_people',
    db.Column('subject_id', db.Integer, db.ForeignKey('person.id')),
    db.Column('resource_id', db.Integer, db.ForeignKey('resource.id'))  
    )

mentions_people = db.Table('mentions_people',
    db.Column('subject_id', db.Integer, db.ForeignKey('person.id')),
    db.Column('resource_id', db.Integer, db.ForeignKey('resource.id'))  
    )

about_organisations = db.Table('about_organisations',
    db.Column('subject_id', db.Integer, db.ForeignKey('organisation.id')),
    db.Column('resource_id', db.Integer, db.ForeignKey('resource.id'))  
    )

mentions_organisations = db.Table('mentions_organisations',
    db.Column('subject_id', db.Integer, db.ForeignKey('organisation.id')),
    db.Column('resource_id', db.Integer, db.ForeignKey('resource.id'))  
    )

about_events = db.Table('about_events',
    db.Column('subject_id', db.Integer, db.ForeignKey('event.id')),
    db.Column('resource_id', db.Integer, db.ForeignKey('resource.id'))  
    )

mentions_events = db.Table('mentions_events',
    db.Column('subject_id', db.Integer, db.ForeignKey('event.id')),
    db.Column('resource_id', db.Integer, db.ForeignKey('resource.id'))  
    )

resource_same_as = db.Table('resource_same_as',
    db.Column('resource_id', db.Integer, db.ForeignKey('resource.id')),
    db.Column('identifier_id', db.Integer, db.ForeignKey('identifier.id'))
    )

class Resource(db.Model, DateMixin):
    '''
    Types: CreativeWork, Book, Article, NewsArticle, Periodical,
    Series, Photograph, Painting
    '''
    id = db.Column(db.Integer, primary_key=True)
    blank_node = db.Column(db.Boolean)
    resource_type = db.Column(db.String(20))
    name = db.Column(db.String(100))
    thumbnail_url = db.Column(db.String(100))
    url = db.Column(db.String(100))
    img_url = db.Column(db.String(100))
    #Publication date
    publication_date = db.Column(db.Date)
    publication_date_month = db.Column(db.Boolean)
    publication_date_day = db.Column(db.Boolean)
    #Creation date
    creation_date = db.Column(db.Date)
    creation_date_month = db.Column(db.Boolean)
    creation_date_day = db.Column(db.Boolean)
    #Series start date
    start_date = db.Column(db.Date)
    start_date_month = db.Column(db.Boolean)
    start_date_day = db.Column(db.Boolean)
    #Series end date
    end_date = db.Column(db.Date)
    end_date_month = db.Column(db.Boolean)
    end_date_day = db.Column(db.Boolean)
    page_start = db.Column(db.String(20))
    page_end = db.Column(db.String(20))
    pagination = db.Column(db.String(20))
    #use for control symbols
    position = db.Column(db.String(100))
    #Relationships
    part_of = db.relationship('Resource',
                            secondary='parts',
                            primaryjoin='Resource.id==parts.c.member_id',
                            secondaryjoin='Resource.id==parts.c.collection_id',
                            backref='has_parts'
                            )
    creators = db.relationship('Person', secondary='creators', backref='creations')
    about_people = db.relationship('Person', secondary='about_people', backref='about')
    mentions_people = db.relationship('Person', secondary='mentions_people', backref='mentioned')
    about_organisations = db.relationship('Organisation', secondary='about_organisations', backref='about')
    mentions_organisations = db.relationship('Organisation', secondary='mentions_organisations', backref='mentioned')
    about_events = db.relationship('Event', secondary='about_events', backref='about')
    mentions_events = db.relationship('Event', secondary='mentions_events', backref='mentioned')
    publisher_id = db.Column(db.Integer, db.ForeignKey('organisation.id'))
    publisher = db.relationship('Organisation', backref='publishes', foreign_keys='Resource.publisher_id')
    provider_id = db.Column(db.Integer, db.ForeignKey('organisation.id'))
    provider = db.relationship('Organisation', backref='provides', foreign_keys='Resource.provider_id')
    same_as = db.relationship('Identifier', secondary='resource_same_as')

    def __repr__(self):
        return '<Resource {!r}>'.format(self.name)

    def display_publication_date(self, format='iso'):
        return self.display_date(
            self.publication_date, 
            self.publication_date_month, 
            self.publication_date_day,
            format
            )

    def display_creation_date(self, format='iso'):
        return self.display_date(
            self.creation_date, 
            self.creation_date_month, 
            self.creation_date_day,
            format
            )

    def display_start_date(self, format='iso'):
        return self.display_date(
            self.start_date, 
            self.start_date_month, 
            self.start_date_day,
            format
            )

    def display_end_date(self, format='iso'):
        return self.display_date(
            self.end_date, 
            self.end_date_month, 
            self.end_date_day,
            format
            )

encodes = db.Table('encodes',
    db.Column('image_id', db.Integer, db.ForeignKey('image.id')),
    db.Column('resource_id', db.Integer, db.ForeignKey('resource.id'))
    )

class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    thumbnail_url = db.Column(db.String(100))
    url = db.Column(db.String(100))
    encodes = db.relationship('Resource', secondary='encodes', backref='encoded_by')

    def __repr__(self):
        return '<Image {!r}>'.format(self.name)


class Identifier(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    identifier = db.Column(db.String(100))

    def __repr__(self):
        return '<Identifier {!r}>'.format(self.identifier)

db.init_app(app)
import maker.views

