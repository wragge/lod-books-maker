from flask import render_template, Response, redirect, request
from maker import app, db, Person, Place, Resource, Identifier, Organisation, Image, Event
from rdflib import Graph
from rdflib import Namespace, BNode, Literal, RDF, URIRef
from rdflib.namespace import RDF, RDFS
from flask_wtf import Form
from wtforms import StringField, DateField, BooleanField, SelectField, SelectMultipleField, TextAreaField, FloatField
from wtforms.fields.html5 import URLField
from wtforms.validators import DataRequired, Optional, url
from werkzeug import secure_filename
from flask_wtf.file import FileField
import re
import json
import datetime
import os
from sqlalchemy.exc import IntegrityError
from config import BOOK_TITLE

ROOT = Namespace('http://lodbookdev.herokuapp.com/')

class NewDateField(DateField):

    def _value(self):
        if self.raw_data:
            return ' '.join(self.raw_data)
        else:
            return self.data and self.data.isoformat() or ''

def get_id_from_url(url):
    return re.search(r'\/(\d+)', url).group(1)

def parse_isodate(date):
    values = {}
    parts = date.split('-')
    if len(parts) == 3:
        values['date'] = datetime.datetime(int(parts[0]), int(parts[1]), int(parts[2]))
        values['month'] = True
        values['day'] = True
    elif len(parts) == 2:
        values['date'] = datetime.datetime(int(parts[0]), int(parts[1]), 1)
        values['month'] = True
        values['day'] = False
    elif len(parts) == 1:
        values['date'] = datetime.datetime(int(parts[0]), 1, 1)
        values['month'] = False
        values['day'] = False
    return values

class AddPersonForm(Form):
    blank_node = BooleanField('Blank node?', validators=[Optional()])
    name = StringField('Name', validators=[DataRequired()])
    family_name = StringField('Family name', validators=[Optional()])
    given_name = StringField('Given name', validators=[Optional()])
    birth_date = NewDateField('Date of birth', validators=[Optional()])
    birth_date_month = BooleanField('Exact month?', validators=[Optional()])
    birth_date_day = BooleanField('Exact day?', validators=[Optional()])
    birth_place_id = SelectField('Place of birth', coerce=int, validators=[Optional()])
    death_date = NewDateField('Date of death', validators=[Optional()])
    death_date_month = BooleanField('Exact month?', validators=[Optional()])
    death_date_day = BooleanField('Exact day?', validators=[Optional()])
    death_place_id = SelectField('Place of death', coerce=int, validators=[Optional()])
    knows = SelectMultipleField('Knows', coerce=int, validators=[Optional()])
    related_to = SelectMultipleField('Related to', coerce=int, validators=[Optional()])
    parents = SelectMultipleField('Parents', coerce=int, validators=[Optional()])
    spouses = SelectMultipleField('Spouses', coerce=int, validators=[Optional()])
    siblings = SelectMultipleField('Siblings', coerce=int, validators=[Optional()])
    member_of = SelectMultipleField('Member of', coerce=int, validators=[Optional()])
    employee_of = SelectMultipleField('Employee of', coerce=int, validators=[Optional()])
    url = URLField('URL', validators=[Optional()])
    img_url = FileField('Image upload', validators=[Optional()])

class AddOrganisationForm(Form):
    blank_node = BooleanField('Blank node?', validators=[Optional()])
    name = StringField('Name', validators=[DataRequired()])
    alternate_name = StringField('Alternate name', validators=[Optional()])
    founding_date = NewDateField('Date of founding', validators=[Optional()])
    founding_date_month = BooleanField('Exact month?', validators=[Optional()])
    founding_date_day = BooleanField('Exact day?', validators=[Optional()])
    dissolution_date = NewDateField('Date of dissolution', validators=[Optional()])
    dissolution_date_month = BooleanField('Exact month?', validators=[Optional()])
    dissolution_date_day = BooleanField('Exact day?', validators=[Optional()])
    location_id = SelectField('Location', coerce=int, validators=[Optional()])
    has_parts = SelectMultipleField('Sub organisations', coerce=int, validators=[Optional()])
    url = URLField('URL', validators=[Optional()])
    img_url = FileField('Image upload', validators=[Optional()])

class AddPlaceForm(Form):
    blank_node = BooleanField('Blank node?', validators=[Optional()])
    name = StringField('Name', validators=[DataRequired()])
    place_type = SelectField('Place type', validators=[Optional()])
    alternate_name = StringField('Alternate name', validators=[Optional()])
    url = URLField('URL', validators=[Optional()])
    latitude = FloatField('Latitude', validators=[Optional()])
    longitude = FloatField('Longitude', validators=[Optional()])
    contained_in = SelectMultipleField('Part of', coerce=int, validators=[Optional()])
    image_id = SelectField('Image', coerce=int, validators=[Optional()])
    img_url = FileField('Image upload', validators=[Optional()])

class AddEventForm(Form):
    blank_node = BooleanField('Blank node?', validators=[Optional()])
    name = StringField('Name', validators=[DataRequired()])
    alternate_name = StringField('Alternate name', validators=[Optional()])
    url = URLField('URL', validators=[Optional()])
    start_date = NewDateField('Start date', validators=[Optional()])
    start_date_month = BooleanField('Exact month?', validators=[Optional()])
    start_date_day = BooleanField('Exact day?', validators=[Optional()])
    end_date = NewDateField('End date', validators=[Optional()])
    end_date_month = BooleanField('Exact month?', validators=[Optional()])
    end_date_day = BooleanField('Exact day?', validators=[Optional()])
    location_id = SelectField('Location', coerce=int, validators=[Optional()])
    super_event = SelectMultipleField('Part of', coerce=int, validators=[Optional()])
    performers = SelectMultipleField('Performers', coerce=int, validators=[Optional()])
    attendees = SelectMultipleField('Attendees', coerce=int, validators=[Optional()])
    image_id = SelectField('Image', coerce=int, validators=[Optional()])
    img_url = FileField('Image upload', validators=[Optional()])

class AddResourceForm(Form):
    blank_node = BooleanField('Blank node?', validators=[Optional()])
    name = StringField('Name', validators=[DataRequired()])
    resource_type = SelectField('Resource type', validators=[Optional()])
    thumbnail = FileField('Thumbnail')
    publication_date = NewDateField('Date of publication', validators=[Optional()])
    publication_date_month = BooleanField('Exact month?', validators=[Optional()])
    publication_date_day = BooleanField('Exact day?', validators=[Optional()])
    creation_date = NewDateField('Date of creation', validators=[Optional()])
    creation_date_month = BooleanField('Exact month?', validators=[Optional()])
    creation_date_day = BooleanField('Exact day?', validators=[Optional()])
    start_date = NewDateField('Start date', validators=[Optional()])
    start_date_month = BooleanField('Exact month?', validators=[Optional()])
    start_date_day = BooleanField('Exact day?', validators=[Optional()])
    end_date = NewDateField('End date', validators=[Optional()])
    end_date_month = BooleanField('Exact month?', validators=[Optional()])
    end_date_day = BooleanField('Exact day?', validators=[Optional()])
    position = StringField('Control symbol', validators=[Optional()])
    page_start = StringField('Page start', validators=[Optional()])
    page_end = StringField('Page end', validators=[Optional()])
    pagination = StringField('Pages', validators=[Optional()])
    part_of = SelectField('Part of', coerce=int, validators=[Optional()])
    creators = SelectMultipleField('Creators', coerce=int, validators=[Optional()])
    about_people = SelectMultipleField('About these people', coerce=int, validators=[Optional()])
    mentions_people = SelectMultipleField('Mentions these people', coerce=int, validators=[Optional()])
    about_organisations = SelectMultipleField('About these organisations', coerce=int, validators=[Optional()])
    mentions_organisations = SelectMultipleField('Mentions these organisations', coerce=int, validators=[Optional()])
    about_events = SelectMultipleField('About these events', coerce=int, validators=[Optional()])
    mentions_events = SelectMultipleField('Mentions these events', coerce=int, validators=[Optional()])
    publisher_id = SelectField('Publisher', coerce=int, validators=[Optional()])
    provider_id = SelectField('Provider', coerce=int, validators=[Optional()])
    url = URLField('URL', validators=[Optional()])
    img_url = FileField('Image upload', validators=[Optional()])

class AddSameasPersonForm(Form):
    identifier = URLField('Identifier', validators=[url()])

class AddSameasResourceForm(Form):
    identifier = URLField('Identifier', validators=[url()])

class AddSameasOrganisationForm(Form):
    identifier = URLField('Identifier', validators=[url()])    

class AddSameasPlaceForm(Form):
    identifier = URLField('Identifier', validators=[url()])

class LoadJSONLDForm(Form):
    jsonld = TextAreaField('JSON-LD', validators=[DataRequired()])


def create_id(entity, e_type):
    if entity.blank_node:
        e_id = BNode('{}-{}'.format(e_type, entity.id))
    else:
        e_id = URIRef('{}#!/{}/{}/'.format(ROOT, e_type, entity.id))
    return e_id


@app.route('/jsonld/')
def view_jsonld():
    graph = Graph()
    schema = Namespace('http://schema.org/')
    context = {'@vocab': 'http://schema.org/', 
        'subjectOf': {'@reverse': 'about'},
        'created': {'@reverse': 'creator'},
        'mentionedBy': {'@reverse': 'mentions'},
        'subOrganizationOf': {'@reverse': 'subOrganization'},
        'contains': {'@reverse': 'containedIn'},
        'attended': {'@reverse': 'attendee'},
        'provides': {'@reverse': 'provider'},
        'publishes': {'@reverse': 'publisher'},
        'ArchivalSeries': 'Series',
        'ArchivalUnit': 'Series',
        'Letter': 'CreativeWork'
        }
    for person in Person.query.all():
        person_id = create_id(person, 'people')
        graph.add((person_id, RDF['type'], schema['Person']))
        graph.add((person_id, schema['name'], Literal(person.name)))
        if person.family_name:
            graph.add((person_id, schema['family_name'], Literal(person.family_name)))
        if person.given_name:
            for name in person.given_name.split():
               graph.add((person_id, schema['given_name'], Literal(name)))
        if person.birth_date:
            graph.add((person_id, schema['birthDate'], Literal(person.display_birth_date())))
        if person.birth_place:
            place_id = create_id(person.birth_place, 'places')
            graph.add((person_id, schema['birthPlace'], place_id))
        if person.death_date:
            graph.add((person_id, schema['deathDate'], Literal(person.display_death_date())))
        if person.death_place:
            place_id = create_id(person.death_place, 'places')
            graph.add((person_id, schema['deathPlace'], place_id))
        if person.url:
            graph.add((person_id, schema['url'], Literal(person.url)))
        if person.img_url:
            graph.add((person_id, schema['image'], Literal(person.img_url[7:])))
        for node in person.knows_all():
            n_id = create_id(node, 'people')
            graph.add((person_id, schema['knows'], n_id))
        for node in person.related_all():
            n_id = create_id(node, 'people')
            graph.add((person_id, schema['relatedTo'], n_id))
        for node in person.parents:
            n_id = create_id(node, 'people')
            graph.add((person_id, schema['parent'], n_id))
        for node in person.children:
            n_id = create_id(node, 'people')
            graph.add((person_id, schema['children'], n_id))
        for node in person.spouse_all():
            n_id = create_id(node, 'people')
            graph.add((person_id, schema['spouse'], n_id))
        for node in person.sibling_all():
            n_id = create_id(node, 'people')
            graph.add((person_id, schema['sibling'], n_id))
        for node in person.member_of:
            n_id = create_id(node, 'organisations')
            graph.add((person_id, schema['memberOf'], n_id))
        for node in person.employee_of:
            n_id = create_id(node, 'organisations')
            graph.add((person_id, schema['worksFor'], n_id))
        for node in person.creations:
            n_id = create_id(node, 'resources')
            graph.add((person_id, schema['created'], n_id))
        for node in person.about:
            n_id = create_id(node, 'resources')
            graph.add((person_id, schema['subjectOf'], n_id))
        for node in person.mentioned:
            n_id = create_id(node, 'resources')
            graph.add((person_id, schema['mentionedBy'], n_id))
        for node in person.performed:
            n_id = create_id(node, 'events')
            graph.add((person_id, schema['performedIn'], n_id))
        for node in person.attended:
            n_id = create_id(node, 'events')
            graph.add((person_id, schema['attended'], n_id))
        for same_as in person.same_as:
            graph.add((person_id, schema['sameAs'], URIRef(same_as.identifier)))
    for entity in Organisation.query.all():
        e_id = create_id(entity, 'organisations')
        graph.add((e_id, RDF['type'], schema['Organization']))
        graph.add((e_id, schema['name'], Literal(entity.name)))
        if entity.alternate_name:
            graph.add((e_id, schema['alternateName'], Literal(entity.alternate_name)))
        if entity.founding_date:
            graph.add((e_id, schema['foundingDate'], Literal(entity.display_founding_date())))
        if entity.dissolution_date:
            graph.add((e_id, schema['dissolutionDate'], Literal(entity.display_dissolution_date())))
        if entity.location:
            place_id = create_id(entity.location, 'places')
            graph.add((e_id, schema['location'], place_id))
        for node in entity.has_parts:
            n_id = create_id(node, 'organisations')
            graph.add((e_id, schema['subOrganization'], n_id))
        for node in entity.part_of:
            n_id = create_id(node, 'organisations')
            graph.add((e_id, schema['subOrganizationOf'], n_id))
        for node in entity.members:
            n_id = create_id(node, 'people')
            graph.add((e_id, schema['member'], n_id))
        for node in entity.employees:
            n_id = create_id(node, 'people')
            graph.add((e_id, schema['employee'], n_id))
        for node in entity.about:
            n_id = create_id(node, 'resources')
            graph.add((e_id, schema['subjectOf'], n_id))
        for node in entity.mentioned:
            n_id = create_id(node, 'resources')
            graph.add((e_id, schema['mentionedBy'], n_id))
        for node in entity.provides:
            n_id = create_id(node, 'resources')
            graph.add((e_id, schema['provides'], n_id))
        for node in entity.publishes:
            n_id = create_id(node, 'resources')
            graph.add((e_id, schema['publishes'], n_id))
        if entity.url:
            graph.add((e_id, schema['url'], Literal(entity.url)))
        if entity.img_url:
            graph.add((e_id, schema['image'], Literal(entity.img_url[7:])))
        for same_as in entity.same_as:
            graph.add((e_id, schema['sameAs'], URIRef(same_as.identifier)))
    for entity in Place.query.all():
        if entity.place_type:
            place_type = entity.place_type
        else:
            place_type = 'Place'
        e_id = create_id(entity, 'places')
        graph.add((e_id, RDF['type'], schema[place_type]))
        graph.add((e_id, schema['name'], Literal(entity.name)))
        if entity.alternate_name:
            graph.add((e_id, schema['alternateName'], Literal(entity.alternate_name)))
        if entity.latitude and entity.longitude:
            geo_id = BNode()
            graph.add((geo_id, RDF['type'], schema['GeoCoordinates']))
            graph.add((geo_id, schema['latitude'], Literal(entity.latitude)))
            graph.add((geo_id, schema['longitude'], Literal(entity.longitude)))
            graph.add((e_id, schema['geo'], geo_id))
        for node in entity.contained_in:
            n_id = create_id(node, 'places')
            graph.add((e_id, schema['containedIn'], n_id))
        for node in entity.containing:
            n_id = create_id(node, 'places')
            graph.add((e_id, schema['contains'], n_id))
        if entity.url:
            graph.add((e_id, schema['url'], Literal(entity.url)))
        if entity.img_url:
            graph.add((e_id, schema['image'], Literal(entity.img_url[7:])))
        for same_as in entity.same_as:
            graph.add((e_id, schema['sameAs'], URIRef(same_as.identifier)))
    for entity in Event.query.all():
        e_id = create_id(entity, 'events')
        graph.add((e_id, RDF['type'], schema['Event']))
        graph.add((e_id, schema['name'], Literal(entity.name)))
        if entity.alternate_name:
            graph.add((e_id, schema['alternateName'], Literal(entity.alternate_name)))
        if entity.start_date:
            graph.add((e_id, schema['startDate'], Literal(entity.display_start_date())))
        if entity.end_date:
            graph.add((e_id, schema['endDate'], Literal(entity.display_end_date())))
        if entity.location:
            place_id = create_id(entity.location, 'places')
            graph.add((e_id, schema['location'], place_id))
        #These are around the wrong way in the db
        for node in entity.super_event:
            n_id = create_id(node, 'events')
            graph.add((e_id, schema['subEvent'], n_id))
        for node in entity.containing:
            n_id = create_id(node, 'events')
            graph.add((e_id, schema['superEvent'], n_id))
        for node in entity.performers:
            n_id = create_id(node, 'people')
            graph.add((e_id, schema['performer'], n_id))
        for node in entity.attendees:
            n_id = create_id(node, 'people')
            graph.add((e_id, schema['attendee'], n_id))
        for node in entity.about:
            n_id = create_id(node, 'resources')
            graph.add((e_id, schema['subjectOf'], n_id))
        for node in entity.mentioned:
            n_id = create_id(node, 'resources')
            graph.add((e_id, schema['mentionedBy'], n_id))
        if entity.url:
            graph.add((e_id, schema['url'], Literal(entity.url)))
        if entity.img_url:
            graph.add((e_id, schema['image'], Literal(entity.img_url[7:])))
        for same_as in entity.same_as:
            graph.add((e_id, schema['sameAs'], URIRef(same_as.identifier)))
    for entity in Resource.query.all():
        if entity.resource_type:
            resource_type = entity.resource_type
        else:
            resource_type = 'CreativeWork'
        e_id = create_id(entity, 'resources')
        graph.add((e_id, RDF['type'], schema[resource_type]))
        graph.add((e_id, schema['name'], Literal(entity.name)))
        if entity.publication_date:
            graph.add((e_id, schema['publicationDate'], Literal(entity.display_publication_date())))
        if entity.creation_date:
            graph.add((e_id, schema['creationDate'], Literal(entity.display_creation_date())))
        if entity.start_date:
            graph.add((e_id, schema['startDate'], Literal(entity.display_start_date())))
        if entity.end_date:
            graph.add((e_id, schema['endDate'], Literal(entity.display_end_date())))
        if entity.position:
            graph.add((e_id, schema['position'], Literal(entity.position)))
        for node in entity.creators:
            n_id = create_id(node, 'people')
            graph.add((e_id, schema['creator'], n_id))
        for node in entity.about_people:
            n_id = create_id(node, 'people')
            graph.add((e_id, schema['about'], n_id))
        for node in entity.mentions_people:
            n_id = create_id(node, 'people')
            graph.add((e_id, schema['mentions'], n_id))
        for node in entity.about_organisations:
            n_id = create_id(node, 'organisations')
            graph.add((e_id, schema['about'], n_id))
        for node in entity.mentions_organisations:
            n_id = create_id(node, 'organisations')
            graph.add((e_id, schema['mentions'], n_id))
        for node in entity.about_events:
            n_id = create_id(node, 'events')
            graph.add((e_id, schema['about'], n_id))
        for node in entity.mentions_events:
            n_id = create_id(node, 'events')
            graph.add((e_id, schema['mentions'], n_id))
        for node in entity.part_of:
            n_id = create_id(node, 'resources')
            graph.add((e_id, schema['isPartOf'], n_id))
        for node in entity.has_parts:
            n_id = create_id(node, 'resources')
            graph.add((e_id, schema['hasPart'], n_id))
        if entity.publisher:
            n_id = create_id(entity.publisher, 'organisations')
            graph.add((e_id, schema['publisher'], n_id))
        if entity.provider:
            n_id = create_id(entity.provider, 'organisations')
            graph.add((e_id, schema['provider'], n_id))
        if entity.url:
            graph.add((e_id, schema['url'], Literal(entity.url)))
        if entity.thumbnail_url:
            graph.add((e_id, schema['thumbnailUrl'], Literal(entity.thumbnail_url[7:])))
        if entity.img_url:
            graph.add((e_id, schema['image'], Literal(entity.img_url[7:])))
        for same_as in entity.same_as:
            graph.add((e_id, schema['sameAs'], URIRef(same_as.identifier)))
    jsonld = graph.serialize(format='json-ld', context=context, indent=4)
    response = Response(response=jsonld, status=200, mimetype="application/json")
    return response

@app.route('/jsonld/load/', methods=('GET', 'POST'))
def load_jsonld():
    form = LoadJSONLDForm()
    if form.validate_on_submit():
        jsonld = json.loads(form.jsonld.data)
        #Loop first time to create the entities if they don't exist
        for entity in jsonld:
            entity_id = re.search(r'\/(\d+)', entity['@id']).group(1)
            entity_type = re.search(r'schema\.org\/(Person|Place)', entity['@type'][0]).group(1)
            name = entity['http://schema.org/name'][0]['@value']
            print '{} - {} - {}'.format(entity_id, entity_type, name)
            if entity_type == 'Person':
                try:
                    person = Person(
                        id=entity_id,
                        name=name
                        )
                    db.session.add(person)
                    db.session.commit()
                except IntegrityError:
                    db.session.rollback()
                    print 'Already exists'
                else:
                    if 'http://schema.org/birthDate' in entity:
                        dates = parse_isodate(entity['http://schema.org/birthDate'][0]['@value'])
                        person.birth_date = dates['date']
                        person.birth_date_month = dates['month']
                        person.birth_date_day = dates['day']
                    if 'http://schema.org/deathDate' in entity:
                        dates = parse_isodate(entity['http://schema.org/deathDate'][0]['@value'])
                        person.death_date = dates['date']
                        person.death_date_month = dates['month']
                        person.death_date_day = dates['day']
                    db.session.commit()
        #Loop again to pick up relationships
        for entity in jsonld:
            entity_id = re.search(r'\/(\d+)', entity['@id']).group(1)
            entity_type = re.search(r'schema\.org\/(Person|Place)', entity['@type'][0]).group(1)
            if entity_type == 'Person':
                person = Person.query.get(entity_id)
                if 'http://schema.org/knows' in entity:
                    knows = []
                    for known in entity['http://schema.org/knows']:
                        known_id = get_id_from_url(known['@id'])
                        knows.append(Person.query.get(known_id))
                    person.knows = knows
                    db.session.commit()
                if 'http://schema.org/sameAs' in entity:
                    same_as_all = []
                    for same_as in entity['http://schema.org/sameAs']:
                        same_as_all.append(Identifier(identifier=same_as['@id']))
                    person.same_as = same_as_all
                    db.session.commit()
        return redirect('/people/')
    return render_template('load_jsonld.html', form=form)

@app.route('/')
def home():
    totals = []
    totals.append(Person.query.count())
    totals.append(Place.query.count())
    totals.append(Resource.query.count())
    return render_template('home.html', totals=totals)

#PEOPLE

def add_people(field):
    people = []
    for person_id in field:
        people.append(Person.query.get(person_id))
    return people

def add_orgs(field):
    orgs = []
    for org_id in field:
        orgs.append(Organisation.query.get(org_id))
    return orgs

def add_places(field):
    places = []
    for place_id in field:
        places.append(Place.query.get(place_id))
    return places

def add_events(field):
    events = []
    for event_id in field:
        events.append(Event.query.get(event_id))
    return events

def get_ids(field):
    return [p.id for p in field]

@app.route('/people/add/', methods=('GET', 'POST'))
def add_person():
    form = AddPersonForm()
    people = [(p.id, p.name) for p in Person.query.order_by('name')]
    places = [(p.id, p.name) for p in Place.query.order_by('name')]
    places.insert(0, (0, '----'))
    organisations = [(p.id, p.name) for p in Organisation.query.order_by('name')]
    form.birth_place_id.choices = places
    form.death_place_id.choices = places
    form.knows.choices = people
    form.related_to.choices = people
    form.parents.choices = people
    form.spouses.choices = people
    form.siblings.choices = people
    form.member_of.choices = organisations
    form.employee_of.choices = organisations
    if form.validate_on_submit():
        person = Person(
            blank_node=form.blank_node.data,
            name=form.name.data, 
            family_name=form.family_name.data,
            given_name=form.given_name.data,
            birth_date=form.birth_date.data,
            birth_date_month=form.birth_date_month.data,
            birth_date_day=form.birth_date_day.data,
            birth_place_id=form.birth_place_id.data,
            death_date=form.death_date.data,
            death_date_month=form.death_date_month.data,
            death_date_day=form.death_date_day.data,
            death_place_id=form.death_place_id.data,
            url=form.url.data
            )
        if form.img_url.data:
            filename = secure_filename(form.img_url.data.filename)
            form.img_url.data.save('maker/static/images/' + filename)
            person.img_url = '/static/images/' + filename
        person.knows = add_people(form.knows.data)
        person.related_to = add_people(form.related_to.data)
        person.parents = add_people(form.parents.data)
        person.spouses = add_people(form.spouses.data)
        person.siblings = add_people(form.siblings.data)
        person.member_of = add_orgs(form.member_of.data)
        person.employee_of = add_orgs(form.employee_of.data)
        db.session.add(person)
        db.session.commit()
        return redirect('/people')
    return render_template('add_person.html', form=form)

@app.route('/people/edit/<id>/', methods=('GET', 'POST'))
def edit_person(id):
    person = Person.query.get(id)
    form = AddPersonForm(obj=person)
    people = [(p.id, p.name) for p in Person.query.order_by('name') if p is not person]
    people.insert(0, (0, '----'))
    places = [(p.id, p.name) for p in Place.query.order_by('name')]
    places.insert(0, (0, '----'))
    organisations = [(p.id, p.name) for p in Organisation.query.order_by('name')]
    form.birth_place_id.choices = places
    form.death_place_id.choices = places
    form.knows.choices = people
    form.related_to.choices = people
    form.parents.choices = people
    form.spouses.choices = people
    form.siblings.choices = people
    form.member_of.choices = organisations
    form.employee_of.choices = organisations
    if form.validate_on_submit():
        person.blank_node = form.blank_node.data
        person.name = form.name.data
        person.family_name = form.family_name.data
        person.given_name = form.given_name.data
        person.birth_date = form.birth_date.data
        person.birth_date_month = form.birth_date_month.data
        person.birth_date_day = form.birth_date_day.data
        person.birth_place_id = form.birth_place_id.data
        person.death_date = form.death_date.data
        person.death_date_month = form.death_date_month.data
        person.death_date_day = form.death_date_day.data
        person.death_place_id = form.death_place_id.data
        person.url = form.url.data
        if form.img_url.data:
            filename = secure_filename(form.img_url.data.filename)
            form.img_url.data.save('maker/static/images/' + filename)
            person.img_url = '/static/images/' + filename
        person.knows = add_people(form.knows.data)
        person.related_to = add_people(form.related_to.data)
        person.parents = add_people(form.parents.data)
        person.spouses = add_people(form.spouses.data)
        person.siblings = add_people(form.siblings.data)
        person.member_of = add_orgs(form.member_of.data)
        person.employee_of = add_orgs(form.employee_of.data)
        db.session.commit()
        return redirect('/people/{}/'.format(person.id))
    else:
        form.knows.data = get_ids(person.knows)
        form.related_to.data = get_ids(person.related_to)
        form.spouses.data = get_ids(person.spouses)
        form.siblings.data = get_ids(person.siblings)
        form.member_of.data = get_ids(person.member_of)
        form.employee_of.data = get_ids(person.employee_of)   
    return render_template('edit_person.html', form=form, person=person)

@app.route('/people/delete/<id>/', methods=('GET', 'POST'))
def delete_person(id):
    person = Person.query.get(id)
    if request.method == 'POST':
        db.session.delete(person)
        db.session.commit()
        return redirect('/people/')
    return render_template('delete_person.html', person=person)

@app.route('/people/')
def view_people():
    people = Person.query.all()
    return render_template('people.html', people=people)

@app.route('/people/<id>/')
def view_person(id):
    person = Person.query.get_or_404(id)
    return render_template('person.html', person=person)

#ORGANISATIONS

@app.route('/organisations/add/', methods=('GET', 'POST'))
def add_organisation():
    form = AddOrganisationForm()
    places = [(p.id, p.name) for p in Place.query.order_by('name')]
    places.insert(0, (0, '----'))
    organisations = [(p.id, p.name) for p in Organisation.query.order_by('name')]
    organisations.insert(0, (0, '----'))
    form.location_id.choices = places
    form.has_parts.choices = organisations
    if form.validate_on_submit():
        organisation = Organisation(
            blank_node=form.blank_node.data,
            name=form.name.data,
            alternate_name=form.alternate_name.data,
            founding_date=form.founding_date.data,
            founding_date_month=form.founding_date_month.data,
            founding_date_day=form.founding_date_day.data,
            dissolution_date=form.dissolution_date.data,
            dissolution_date_month=form.dissolution_date_month.data,
            dissolution_date_day=form.dissolution_date_day.data,
            location_id=form.location_id.data,
            url=form.url.data
            )
        if form.img_url.data:
            filename = secure_filename(form.img_url.data.filename)
            form.img_url.data.save('maker/static/images/' + filename)
            organisation.img_url = '/static/images/' + filename
        organisation.has_parts = add_orgs(form.has_parts.data)
        db.session.add(organisation)
        db.session.commit()
        return redirect('/organisations/')
    return render_template('add_organisation.html', form=form)

@app.route('/organisations/edit/<id>/', methods=('GET', 'POST'))
def edit_organisation(id):
    organisation = Organisation.query.get(id)
    form = AddOrganisationForm(obj=organisation)
    places = [(p.id, p.name) for p in Place.query.order_by('name')]
    places.insert(0, (0, '----'))
    organisations = [(p.id, p.name) for p in Organisation.query.order_by('name')]
    organisations.insert(0, (0, '----'))
    form.location_id.choices = places
    form.has_parts.choices = organisations
    if form.validate_on_submit():
        organisation.blank_node = form.blank_node.data
        organisation.name = form.name.data
        organisation.alternate_name = form.alternate_name.data
        organisation.founding_date = form.founding_date.data
        organisation.founding_date_month = form.founding_date_month.data
        organisation.founding_date_day = form.founding_date_day.data
        organisation.dissolution_date = form.dissolution_date.data
        organisation.dissolution_date_month = form.dissolution_date_month.data
        organisation.dissolution_date_day = form.dissolution_date_day.data
        organisation.location_id = form.location_id.data
        if form.img_url.data:
            filename = secure_filename(form.img_url.data.filename)
            form.img_url.data.save('maker/static/images/' + filename)
            organisation.img_url = '/static/images/' + filename
        organisation.has_parts = add_orgs(form.has_parts.data)
        db.session.commit()
        return redirect('/organisations/{}/'.format(organisation.id))
    else:
        form.has_parts.data = get_ids(organisation.has_parts)
    return render_template('edit_organisation.html', form=form, organisation=organisation)

@app.route('/organisations/delete/<id>/', methods=('GET', 'POST'))
def delete_organisation(id):
    organisation = Organisation.query.get(id)
    if request.method == 'POST':
        db.session.delete(organisation)
        db.session.commit()
        return redirect('/organisations')
    return render_template('delete_organisation.html', organisation=organisation)

@app.route('/organisations/')
def view_organisations():
    organisations = Organisation.query.all()
    return render_template('organisations.html', organisations=organisations)

@app.route('/organisations/<id>/')
def view_organisation(id):
    organisation = Organisation.query.get_or_404(id)
    return render_template('organisation.html', organisation=organisation)


#PLACES

@app.route('/places/add/', methods=('GET', 'POST'))
def add_place():
    form = AddPlaceForm()
    places = [(p.id, p.name) for p in Place.query.order_by('name')]
    images = [(p.id, p.name) for p in Image.query.order_by('name')]
    places.insert(0, (0, '----'))
    images.insert(0, (0, '----'))
    form.contained_in.choices = places
    form.image_id.choices = images
    form.place_type.choices = [('City', 'City'), ('Country', 'Country'), ('State', 'State'), ('Landform', 'Landform')]
    if form.validate_on_submit():
        place = Place(
            blank_node=form.blank_node.data,
            name=form.name.data,
            place_type=form.place_type.data,
            alternate_name=form.alternate_name.data,
            url=form.url.data,
            latitude=form.latitude.data,
            longitude=form.longitude.data,
            image_id=form.image_id.data
            )
        if form.img_url.data:
            filename = secure_filename(form.img_url.data.filename)
            form.img_url.data.save('maker/static/images/' + filename)
            place.img_url = '/static/images/' + filename
        place.contained_in = add_places(form.contained_in.data)
        db.session.add(place)
        db.session.commit()
        return redirect('/places/')
    return render_template('add_place.html', form=form)

@app.route('/places/edit/<id>/', methods=('GET', 'POST'))
def edit_place(id):
    place = Place.query.get(id)
    form = AddPlaceForm(obj=place)
    places = [(p.id, p.name) for p in Place.query.order_by('name')]
    images = [(p.id, p.name) for p in Image.query.order_by('name')]
    places.insert(0, (0, '----'))
    images.insert(0, (0, '----'))
    form.contained_in.choices = places
    form.image_id.choices = images
    form.place_type.choices = [('City', 'City'), ('Country', 'Country'), ('State', 'State'), ('Landform', 'Landform')]
    if form.validate_on_submit():
        place.blank_node = form.blank_node.data
        place.name = form.name.data
        place.place_type = form.place_type.data
        place.alternate_name = form.alternate_name.data
        place.url = form.url.data
        place.latitude = form.latitude.data
        place.longitude = form.longitude.data
        place.image_id = form.image_id.data
        if form.img_url.data:
            filename = secure_filename(form.img_url.data.filename)
            form.img_url.data.save('maker/static/images/' + filename)
            place.img_url = '/static/images/' + filename
        place.contained_in = add_places(form.contained_in.data)
        db.session.commit()
        return redirect('/places/{}/'.format(place.id))
    else:
        form.contained_in.data = get_ids(place.contained_in)
    return render_template('edit_place.html', form=form, place=place)

@app.route('/places/delete/<id>/', methods=('GET', 'POST'))
def delete_place(id):
    place = Place.query.get(id)
    if request.method == 'POST':
        db.session.delete(place)
        db.session.commit()
        return redirect('/places')
    return render_template('delete_place.html', place=place)

@app.route('/places/')
def view_places():
    places = Place.query.all()
    return render_template('places.html', places=places)

@app.route('/places/<id>/')
def view_place(id):
    place = Place.query.get_or_404(id)
    return render_template('place.html', place=place)

#Resources

@app.route('/resources/add/', methods=('GET', 'POST'))
def add_resource():
    form = AddResourceForm()
    form.resource_type.choices = [
            ('CreativeWork', 'CreativeWork'),
            ('Book', 'Book'),
            ('ArchivalSeries', 'ArchivalSeries'),
            ('ArchivalUnit', 'ArchivalUnit'),
            ('Article', 'Article'),
            ('Letter', 'Letter'),
            ('NewsArticle', 'NewsArticle'),
            ('Periodical', 'Periodical'),
            ('Photograph', 'Photograph'),
            ('Series', 'Series'),
            ('WebPage', 'WebPage'),
            ('WebSite', 'Website'),
            ]
    resources = [(r.id, r.name) for r in Resource.query.order_by('name')]
    resources.insert(0, (0, '----'))
    people = [(p.id, p.name) for p in Person.query.order_by('name')]
    people.insert(0, (0, '----'))
    orgs = [(o.id, o.name) for o in Organisation.query.order_by('name')]
    orgs.insert(0, (0, '----'))
    events = [(o.id, o.name) for o in Event.query.order_by('name')]
    events.insert(0, (0, '----'))
    form.part_of.choices = resources
    form.creators.choices = people
    form.about_people.choices = people
    form.mentions_people.choices = people
    form.publisher_id.choices = orgs
    form.provider_id.choices = orgs
    form.about_organisations.choices = orgs
    form.mentions_organisations.choices = orgs
    form.about_events.choices = events
    form.mentions_events.choices = events
    if form.validate_on_submit():
        resource = Resource(
            blank_node=form.blank_node.data,
            resource_type=form.resource_type.data,
            name=form.name.data,
            publication_date=form.publication_date.data,
            publication_date_month=form.publication_date_month.data,
            publication_date_day=form.publication_date_day.data,
            creation_date=form.creation_date.data,
            creation_date_month=form.creation_date_month.data,
            creation_date_day=form.creation_date_day.data,
            start_date=form.start_date.data,
            start_date_month=form.start_date_month.data,
            start_date_day=form.start_date_day.data,
            end_date=form.end_date.data,
            end_date_month=form.end_date_month.data,
            page_start=form.page_start.data,
            page_end=form.page_end.data,
            pagination=form.pagination.data,
            end_date_day=form.end_date_day.data,
            position=form.position.data,
            url=form.url.data
            )
        if form.img_url.data:
            filename = secure_filename(form.img_url.data.filename)
            form.img_url.data.save('maker/static/images/' + filename)
            resource.img_url = '/static/images/' + filename
        if form.part_of.data:
            resource.part_of=[Resource.query.get(form.part_of.data)]
        creators = []
        for new_id in form.creators.data:
            creators.append(Person.query.get(new_id))
        resource.creators = creators
        about_people = []
        for new_id in form.about_people.data:
            about_people.append(Person.query.get(new_id))
        resource.about_people = about_people
        mentions_people = []
        for new_id in form.mentions_people.data:
            mentions_people.append(Person.query.get(new_id))
        resource.mentions_people = mentions_people
        about_organisations = []
        for new_id in form.about_organisations.data:
            about_organisations.append(Organisation.query.get(new_id))
        resource.about_organisations = about_organisations
        mentions_organisations = []
        for new_id in form.mentions_organisations.data:
            mentions_organisations.append(Organisation.query.get(new_id))
        resource.mentions_organisations = mentions_organisations
        about_events = []
        for new_id in form.about_events.data:
            about_events.append(Event.query.get(new_id))
        resource.about_events = about_events
        mentions_events = []
        for new_id in form.mentions_events.data:
            mentions_events.append(Event.query.get(new_id))
        resource.mentions_events = mentions_events
        resource.publisher = Organisation.query.get(form.publisher_id.data)
        resource.provider = Organisation.query.get(form.provider_id.data)
        if form.thumbnail.data:
            filename = secure_filename(form.thumbnail.data.filename)
            form.thumbnail.data.save('maker/static/images/' + filename)
            resource.thumbnail_url = '/static/images/' + filename
        db.session.add(resource)
        db.session.commit()
        return redirect('/resources/')
    return render_template('add_resource.html', form=form)

@app.route('/resources/edit/<id>/', methods=('GET', 'POST'))
def edit_resource(id):
    resource = Resource.query.get(id)
    form = AddResourceForm(obj=resource)
    form.resource_type.choices = [
            ('CreativeWork', 'CreativeWork'),
            ('Book', 'Book'),
            ('ArchivalSeries', 'ArchivalSeries'),
            ('ArchivalUnit', 'ArchivalUnit'),
            ('Article', 'Article'),
            ('Letter', 'Letter'),
            ('NewsArticle', 'NewsArticle'),
            ('Periodical', 'Periodical'),
            ('Photograph', 'Photograph'),
            ('Series', 'Series'),
            ('WebPage', 'WebPage'),
            ('WebSite', 'Website'),
            ]
    resources = [(r.id, r.name) for r in Resource.query.order_by('name')]
    resources.insert(0, (0, '----'))
    people = [(p.id, p.name) for p in Person.query.order_by('name')]
    people.insert(0, (0, '----'))
    orgs = [(o.id, o.name) for o in Organisation.query.order_by('name')]
    orgs.insert(0, (0, '----'))
    events = [(o.id, o.name) for o in Event.query.order_by('name')]
    events.insert(0, (0, '----'))
    form.part_of.choices = resources
    form.creators.choices = people
    form.about_people.choices = people
    form.mentions_people.choices = people
    form.publisher_id.choices = orgs
    form.provider_id.choices = orgs
    form.about_organisations.choices = orgs
    form.mentions_organisations.choices = orgs
    form.about_events.choices = events
    form.mentions_events.choices = events
    if form.validate_on_submit():
        resource.blank_node = form.blank_node.data
        resource.resource_type = form.resource_type.data
        resource.name = form.name.data
        resource.publication_date = form.publication_date.data
        resource.publication_date_month = form.publication_date_month.data
        resource.publication_date_day = form.publication_date_day.data
        resource.creation_date = form.creation_date.data
        resource.creation_date_month = form.creation_date_month.data
        resource.creation_date_day = form.creation_date_day.data
        resource.start_date = form.start_date.data
        resource.start_date_month = form.start_date_month.data
        resource.start_date_day = form.start_date_day.data
        resource.end_date = form.end_date.data
        resource.end_date_month = form.end_date_month.data
        resource.end_date_day = form.end_date_day.data
        resource.position = form.position.data
        resource.page_start = form.page_start.data
        resource.page_end = form.page_end.data
        resource.pagination = form.pagination.data
        resource.url = form.url.data
        resource.publisher = Organisation.query.get(form.publisher_id.data)
        resource.provider = Organisation.query.get(form.provider_id.data)
        if form.img_url.data:
            filename = secure_filename(form.img_url.data.filename)
            form.img_url.data.save('maker/static/images/' + filename)
            resource.img_url = '/static/images/' + filename
        if form.part_of.data:
            resource.part_of = [Resource.query.get(form.part_of.data)]
        creators = []
        for new_id in form.creators.data:
            creators.append(Person.query.get(new_id))
        resource.creators = creators
        about_people = []
        for new_id in form.about_people.data:
            about_people.append(Person.query.get(new_id))
        resource.about_people = about_people
        mentions_people = []
        for new_id in form.mentions_people.data:
            mentions_people.append(Person.query.get(new_id))
        resource.mentions_people = mentions_people
        about_organisations = []
        for new_id in form.about_organisations.data:
            about_organisations.append(Organisation.query.get(new_id))
        resource.about_organisations = about_organisations
        mentions_organisations = []
        for new_id in form.mentions_organisations.data:
            mentions_organisations.append(Organisation.query.get(new_id))
        resource.mentions_organisations = mentions_organisations
        about_events = []
        for new_id in form.about_events.data:
            about_events.append(Event.query.get(new_id))
        resource.about_events = about_events
        mentions_events = []
        for new_id in form.mentions_events.data:
            mentions_events.append(Event.query.get(new_id))
        resource.mentions_events = mentions_events
        if form.thumbnail.data:
            filename = secure_filename(form.thumbnail.data.filename)
            if not os.path.exists(filename):
                form.thumbnail.data.save('maker/static/images/' + filename)
            resource.thumbnail_url = '/static/images/' + filename
        db.session.commit()
        return redirect('/resources/{}/'.format(resource.id))
    else:
        #Set current values for relationships
        #Has to happen post-form processing to prevent overwriting values
        part_of_ids = [p.id for p in resource.part_of]
        if part_of_ids:
            form.part_of.data = part_of_ids[0]
        creator_ids = [p.id for p in resource.creators]
        form.creators.data = creator_ids
        about_people_ids = [p.id for p in resource.about_people]
        form.about_people.data = about_people_ids
        mentions_people_ids = [p.id for p in resource.mentions_people]
        form.mentions_people.data = mentions_people_ids
        about_organisations_ids = [p.id for p in resource.about_organisations]
        form.about_organisations.data = about_organisations_ids
        mentions_organisations_ids = [p.id for p in resource.mentions_organisations]
        form.mentions_organisations.data = mentions_organisations_ids
        about_events_ids = [p.id for p in resource.about_events]
        form.about_events.data = about_events_ids
        mentions_events_ids = [p.id for p in resource.mentions_events]
        form.mentions_events.data = mentions_events_ids

    return render_template('edit_resource.html', form=form, resource=resource)

@app.route('/resources/delete/<id>/', methods=('GET', 'POST'))
def delete_resource(id):
    resource = Resource.query.get(id)
    if request.method == 'POST':
        db.session.delete(resource)
        db.session.commit()
        return redirect('/resources/')
    return render_template('delete_resource.html', resource=resource)

@app.route('/resources/')
def view_resources():
    resources = Resource.query.all()
    return render_template('resources.html', resources=resources)

@app.route('/resources/<id>/')
def view_resource(id):
    resource = Resource.query.get_or_404(id)
    return render_template('resource.html', resource=resource)

#EVENTS

@app.route('/events/add/', methods=('GET', 'POST'))
def add_event():
    form = AddEventForm()
    events = [(p.id, p.name) for p in Event.query.order_by('name')]
    places = [(p.id, p.name) for p in Place.query.order_by('name')]
    images = [(p.id, p.name) for p in Image.query.order_by('name')]
    events.insert(0, (0, '----'))
    images.insert(0, (0, '----'))
    places.insert(0, (0, '----'))
    people = [(p.id, p.name) for p in Person.query.order_by('name')]
    people.insert(0, (0, '----'))
    form.super_event.choices = events
    form.image_id.choices = images
    form.location_id.choices = places
    form.performers.choices = people
    form.attendees.choices = people
    if form.validate_on_submit():
        event = Event(
            blank_node=form.blank_node.data,
            name=form.name.data,
            alternate_name=form.alternate_name.data,
            start_date=form.start_date.data,
            start_date_month=form.start_date_month.data,
            start_date_day=form.start_date_day.data,
            end_date=form.end_date.data,
            end_date_month=form.end_date_month.data,
            end_date_day=form.end_date_day.data,
            url=form.url.data,
            location_id=form.location_id.data,
            image_id=form.image_id.data
            )
        if form.img_url.data:
            filename = secure_filename(form.img_url.data.filename)
            form.img_url.data.save('maker/static/images/' + filename)
            event.img_url = '/static/images/' + filename
        event.super_event = add_events(form.super_event.data)
        event.performers = add_people(form.performers.data)
        event.attendees = add_people(form.attendees.data)
        db.session.add(event)
        db.session.commit()
        return redirect('/events/')
    return render_template('add_event.html', form=form)

@app.route('/events/edit/<id>/', methods=('GET', 'POST'))
def edit_event(id):
    event = Event.query.get(id)
    form = AddEventForm(obj=event)
    events = [(p.id, p.name) for p in Event.query.order_by('name')]
    images = [(p.id, p.name) for p in Image.query.order_by('name')]
    places = [(p.id, p.name) for p in Place.query.order_by('name')]
    events.insert(0, (0, '----'))
    images.insert(0, (0, '----'))
    places.insert(0, (0, '----'))
    people = [(p.id, p.name) for p in Person.query.order_by('name')]
    people.insert(0, (0, '----'))
    form.super_event.choices = events
    form.image_id.choices = images
    form.performers.choices = people
    form.attendees.choices = people
    form.location_id.choices = places
    if form.validate_on_submit():
        event.blank_node = form.blank_node.data
        event.name = form.name.data
        event.alternate_name = form.alternate_name.data
        event.url = form.url.data
        event.start_date = form.start_date.data
        event.start_date_month = form.start_date_month.data
        event.start_date_day = form.start_date_day.data
        event.end_date = form.end_date.data
        event.end_date_month = form.end_date_month.data
        event.end_date_day = form.end_date_day.data
        event.image_id = form.image_id.data
        event.location_id = form.location_id.data
        if form.img_url.data:
            filename = secure_filename(form.img_url.data.filename)
            form.img_url.data.save('maker/static/images/' + filename)
            event.img_url = '/static/images/' + filename
        event.super_event = add_events(form.super_event.data)
        event.performers = add_people(form.performers.data)
        event.attendees = add_people(form.attendees.data)
        db.session.commit()
        return redirect('/events/{}/'.format(event.id))
    else:
        form.super_event.data = get_ids(event.super_event)
        form.performers.data = get_ids(event.performers)
        form.attendees.data = get_ids(event.attendees)
    return render_template('edit_event.html', form=form, event=event)

@app.route('/events/delete/<id>/', methods=('GET', 'POST'))
def delete_event(id):
    event = Event.query.get(id)
    if request.method == 'POST':
        db.session.delete(event)
        db.session.commit()
        return redirect('/events')
    return render_template('delete_event.html', event=event)

@app.route('/events/')
def view_events():
    events = Event.query.all()
    return render_template('events.html', events=events)

@app.route('/events/<id>/')
def view_event(id):
    event = Event.query.get_or_404(id)
    return render_template('event.html', event=event)

#IDENTIFIERS
@app.route('/people/sameas/<id>/', methods=('GET', 'POST'))
def add_sameas_person(id):
    person = Person.query.get(id)
    form = AddSameasPersonForm()
    if form.validate_on_submit():
        identifier = Identifier(
                identifier=form.identifier.data
            )
        db.session.add(identifier)
        if identifier not in person.same_as:
            person.same_as.append(identifier)
        db.session.commit()
        return redirect('/people/{}/'.format(id))
    return render_template('add_sameas_person.html', person=person, form=form)


@app.route('/resources/sameas/<id>/', methods=('GET', 'POST'))
def add_sameas_resource(id):
    resource = Resource.query.get(id)
    form = AddSameasResourceForm()
    if form.validate_on_submit():
        identifier = Identifier(
                identifier=form.identifier.data
            )
        db.session.add(identifier)
        if identifier not in resource.same_as:
            resource.same_as.append(identifier)
        db.session.commit()
        return redirect('/resources/{}/'.format(id))
    return render_template('add_sameas_resource.html', resource=resource, form=form)

@app.route('/organisations/sameas/<id>/', methods=('GET', 'POST'))
def add_sameas_organisation(id):
    organisation = Organisation.query.get(id)
    form = AddSameasOrganisationForm()
    if form.validate_on_submit():
        identifier = Identifier(
                identifier=form.identifier.data
            )
        db.session.add(identifier)
        if identifier not in organisation.same_as:
            organisation.same_as.append(identifier)
        db.session.commit()
        return redirect('/organisations/{}/'.format(id))
    return render_template('add_sameas_organisation.html', organisation=organisation, form=form)

@app.route('/places/sameas/<id>/', methods=('GET', 'POST'))
def add_sameas_place(id):
    place = Place.query.get(id)
    form = AddSameasPlaceForm()
    if form.validate_on_submit():
        identifier = Identifier(
                identifier=form.identifier.data
            )
        db.session.add(identifier)
        if identifier not in place.same_as:
            place.same_as.append(identifier)
        db.session.commit()
        return redirect('/places/{}/'.format(id))
    return render_template('add_sameas_place.html', place=place, form=form)


@app.context_processor
def inject_details():
    return dict(book_title=BOOK_TITLE)
