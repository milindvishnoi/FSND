#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
from datetime import datetime
from flask_migrate import Migrate
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    genres = db.Column(db.ARRAY(db.String))
    website = db.Column(db.String())
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean)
    seeking_description = db.Column(db.String())
    image_link = db.Column(db.String())
    shows = db.relationship('Show',
        backref=db.backref('Venue', lazy=True))
    
    def __repr__(self):
      return f'<Venue {self.id} name: {self.name}>'


class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String())
    seeking_venue = db.Column(db.Boolean)
    seeking_description = db.Column(db.String())
    image_link = db.Column(db.String())
    shows = db.relationship('Show',
        backref=db.backref('Artist', lazy=True))
    availability = db.Column(db.ARRAY(db.DateTime))


class Show(db.Model):
  __tablename__ = 'Show'

  id = db.Column(db.Integer, primary_key=True)
  start_time = db.Column(db.DateTime)
  artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'),
        nullable=False)
  venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'),
        nullable=False)

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  list_of_venues = Venue.query.distinct('city','state').all()
  data = []
  for v in list_of_venues:
        venues = Venue.query.filter(Venue.city == v.city, Venue.state == v.state).all()
        org_venues = []
        for venue in venues:
          org_venues.append(get_formatted_info(venue.id, venue))
        response = {
          'state': v.state,
          'city': v.city,
          'venues': org_venues
        }
        data.append(response)
  return render_template('pages/venues.html', areas=data);

def get_formatted_info(id: int, venue: Venue):
  response = {
    'id': venue.id,
    'name': venue.name,
    'num_upcoming_shows': get_upcoming_shows(id, venue)
  }
  return response

def get_upcoming_shows(id: int, venue:Venue):
  shows = Show.query.filter_by(venue_id=id).all()
  count = 0
  for show in shows:
    if show.start_time > datetime.now():
          count += 1
  return count
  

@app.route('/venues/search', methods=['POST'])
def search_venues():
  search_term = request.form.get('search_term', '')
  search_term = '%'+search_term+'%'
  search_result = Venue.query.filter(Venue.name.like(search_term)).all()
  data = []
  for venue in search_result:
    data.append(get_formatted_info(venue.id, venue))
  response ={
    'count':len(search_result),
    'data': data
  }
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

def get_formatted_info(id: int, artist: Artist):
  response = {
    'id': artist.id,
    'name': artist.name,
    'num_upcoming_shows': get_upcoming_shows(id, artist)
  }
  return response

def get_upcoming_shows(id: int, artist: Artist):
  shows = Show.query.filter_by(artist_id=id).all()
  count = 0
  for show in shows:
    if show.start_time > datetime.now():
      count += 1
  return count

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  venue = Venue.query.filter_by(id=venue_id).first()
  if venue is None:
    return render_template('/errors/404.html')
  past_shows = get_past_shows(venue.id, venue)
  temp = []
  past_show_count = 0
  for show in past_shows:
    if show['artist_id'] not in temp:
      temp.append(show['artist_id'])
      past_show_count += 1
  upcoming_shows = get_upcoming_show_formated(venue.id, venue)
  temp = []
  upcoming_show_count = 0
  for show in upcoming_shows:
    if show['artist_id'] not in temp:
      temp.append(show['artist_id'])
      upcoming_show_count += 1
  data = {
    "id": venue.id,
    "name": venue.name,
    "genres": venue.genres,
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website": venue.website,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_show_count": past_show_count,
    "upcoming_shows_count": upcoming_show_count,
  }
  return render_template('pages/show_venue.html', venue=data)

def get_past_shows(id: int, venue: Venue):
  shows = Show.query.filter_by(venue_id=id).all()
  response = []
  for show in shows:
    print(datetime.now())
    if show.start_time < datetime.now():
      artist = Artist.query.filter_by(id=show.artist_id).first()
      data = {
      "artist_id": artist.id,
      "artist_name": artist.name,
      "artist_image_link": artist.image_link,
      "start_time": format_datetime(str(show.start_time))
      }
      response.append(data)
  return response
  
def get_upcoming_show_formated(id: int, venue: Venue):
  shows = Show.query.filter_by(venue_id=id).all()
  response = []
  for show in shows:
    print(datetime.now())
    if show.start_time > datetime.now():
      artist = Artist.query.filter_by(id=show.artist_id).first()
      data = {
      "artist_id": artist.id,
      "artist_name": artist.name,
      "artist_image_link": artist.image_link,
      "start_time": format_datetime(str(show.start_time))
      }
      response.append(data)
  return response

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  try:
    id = Venue.query.count()+1
    name = request.form['name']
    city = request.form['city']
    state = request.form['state']
    address = request.form['address']
    phone = request.form['phone']
    genres = request.form.getlist('genres')
    facebook_link = request.form['facebook_link']
    venue = Venue(id=id, name=name, city=city, state=state, address=address, phone=phone, genres=genres, facebook_link=facebook_link)
    db.session.add(venue)
    db.session.commit()
    # on successful db insert, flash success
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  except:
    db.session.rollback()
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
  finally:
    db.session.close()
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  try:
    venue = Venue.query.filter_by(id=venue_id).delete()
    db.session.commit()
    flash('Venue was successfully deleted!')
  except:
    db.session.rollback()
    venue = Venue.query.filter_by(id=venue_id).first()
    flash('An error occurred. Venue ' + venue.name + ' could not be deleted.')
  finally:
    db.session.close()
  return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  artists = Artist.query.all()
  data = []
  for artist in artists:
    response = {
      "id": artist.id,
      "name": artist.name
    }
    data.append(response)
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  response = {}
  search_term = request.form.get('search_term', '')
  search_term = '%'+search_term+'%'
  search_result = Artist.query.filter(Artist.name.ilike(search_term)).all()
  data = []
  for artist in search_result:
    data.append(get_formatted_info(artist.id, artist))
  response ={
    'count':len(search_result),
    'data': data
  }
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  artist = Artist.query.filter_by(id=artist_id).first()
  if artist is None:
    return render_template('/errors/404.html')
  past_shows = get_past_shows_artist(artist_id, artist)
  temp = []
  past_show_count = 0
  for show in past_shows:
    if show['venue_id'] not in temp:
      temp.append(show['venue_id'])
      past_show_count += 1
  upcoming_shows = get_upcoming_show_formated_artist(artist_id, artist)
  temp = []
  upcoming_show_count = 0
  for show in upcoming_shows:
    if show['venue_id'] not in temp:
      temp.append(show['venue_id'])
      upcoming_show_count += 1
  data = {
    "id": artist.id,
    "name": artist.name,
    "genres": artist.genres,
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "facebook_link": artist.facebook_link,
    "seeking_venue": artist.seeking_venue,
    "seeking_description": artist.seeking_description,
    "image_link": artist.image_link,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": past_show_count,
    "upcoming_shows_count": upcoming_show_count
  }
  return render_template('pages/show_artist.html', artist=data)

def get_past_shows_artist(id: int, artist: Artist):
  shows = Show.query.filter_by(artist_id=id).all()
  response = []
  for show in shows:
    if show.start_time < datetime.now():
      venue = Venue.query.filter_by(id=show.venue_id).first()
      data = {
      "venue_id": venue.id,
      "venue_name": venue.name,
      "venue_image_link": venue.image_link,
      "start_time": format_datetime(str(show.start_time))
      }
      response.append(data)
  return response
  
def get_upcoming_show_formated_artist(id: int, artist: Artist):
  shows = Show.query.filter_by(artist_id=id).all()
  response = []
  for show in shows:
    if show.start_time > datetime.now():
      venue = Venue.query.filter_by(id=show.venue_id).first()
      data = {
      "venue_id": venue.id,
      "venue_name": venue.name,
      "venue_image_link": venue.image_link,
      "start_time": format_datetime(str(show.start_time))
      }
      response.append(data)
  return response

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist = Artist.query.filter_by(id=artist_id).first()
  if artist is None:
    return render_template('errors/404.html')
  form['name'].data = artist.name
  form['genres'].data = artist.genres
  form['city'].data = artist.city
  form['state'].data = artist.state
  form['phone'].data = artist.phone
  form['facebook_link'].data = artist.facebook_link
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  error = False
  try:
    artist = Artist.query.filter_by(id=artist_id).first()
    artist.name = request.form['name']
    artist.genres = request.form.getlist('genres')
    artist.city = request.form['city']
    artist.state = request.form['state']
    artist.phone = request.form['phone']
    artist.facebook_link = request.form['facebook_link']
    db.session.add(artist)
    db.session.commit()
    flash("Artist was edited!")
  except:
    error = True
    db.session.rollback()
  finally:
    db.session.close()
    if not error:
      return redirect(url_for('show_artist', artist_id=artist_id))
    return render_template("errors/500.html")

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue = Venue.query.filter_by(id=venue_id).first()
  if venue is None:
    return render_template('errors/404.html')
  form['name'].data = venue.name
  form['genres'].data = venue.genres
  form['city'].data = venue.city
  form['state'].data = venue.state
  form['phone'].data = venue.phone
  form['facebook_link'].data = venue.facebook_link
  form['address'].data = venue.address
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  error = False
  try:
    venue = Venue.query.filter_by(id=venue_id).first()
    venue.name = request.form['name']
    venue.genres = request.form.getlist('genres')
    venue.city = request.form['city']
    venue.address = request.form['address']
    venue.state = request.form['state']
    venue.phone = request.form['phone']
    venue.facebook_link = request.form['facebook_link']
    db.session.add(venue)
    db.session.commit()
    flash("Venue was edited!")
  except:
    error = True
    db.session.rollback()
  finally:
    db.session.close()
    if not error:
      return redirect(url_for('show_venue', venue_id=venue_id))
    return render_template("errors/500.html")
  

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  try:
    id = Artist.query.count()+1
    name = request.form['name']
    city = request.form['city']
    state = request.form['state']
    phone = request.form['phone']
    genres = request.form.getlist('genres')
    facebook_link = request.form['facebook_link']
    artist = Artist(id=id, name=name, city=city, state=state, address=address, phone=phone, genres=genres, facebook_link=facebook_link)
    db.session.add(artist)
    db.session.commit()
    # on successful db insert, flash success
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  except:
    db.session.rollback()
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
  finally:
    db.session.close()
    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  data = []
  shows = Show.query.all()
  for show in shows:
    venue = Venue.query.filter_by(id=show.venue_id).first()
    artist = Artist.query.filter_by(id=show.artist_id).first()
    response = {
      "venue_id": venue.id,
      "venue_name": venue.name,
      "artist_id": artist.id,
      "artist_name": artist.name,
      "artist_image_link": artist.image_link,
      "start_time": format_datetime(str(show.start_time))
    }
    data.append(response)
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  artist_id = request.form['artist_id']
  start_time = request.form['start_time']
  artist = Artist.query.filter_by(id=artist_id).first()
  artist_availability = []
  if artist.availability is not None: artist_availability = artist.availability
  for availability in artist_availability:
    if start_time == availability:
      try:
        id = Show.query.count()+1
        venue_id = request.form['venue_id']
        venue = Venue.query.filter_by(id=venue_id).first()
        if venue is not None and artist is not None:
          flash("Invalid Reservation Try!")
          return render_template('pages/home.html')
        show = Show(id=id, venue_id=venue_id, artist_id=artist_id, start_time=start_time)
        db.session.add(show)
        db.session.commit()
        # on successful db insert, flash success
        flash('Show was successfully listed!')
      except:
        flash('An error occurred. Show could not be listed.')
        db.session.rollback()
      finally:
        db.session.close()
        return render_template('pages/home.html')
  # If not available at that time then
  flash("Artist not available at that time")
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
