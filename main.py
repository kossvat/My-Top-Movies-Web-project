from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests
import os

API_KEY = os.environ.get('API_KEY')
MOVIE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_URL = 'https://image.tmdb.org/t/p/w500'

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///my-top-movies.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
Bootstrap(app)


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(250), nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String(250), nullable=True)
    img_url = db.Column(db.String(250), nullable=False)
    
    def __repr__(self):
        return f'<Book {self.title}>'
   
    
with app.app_context():
    db.create_all()
    
    # new_movie = Movie(
    #         title="Phone Booth",
    #         year=2002,
    #         description="Publicist Stuart Shepard finds himself trapped in a phone booth, pinned down by an extortionist's"
    #                     " sniper rifle. Unable to leave or receive outside help, Stuart's negotiation with the caller leads to a jaw-dropping climax.",
    #         rating=7.3,
    #         ranking=10,
    #         review="My favourite character was the caller.",
    #         img_url="https://image.tmdb.org/t/p/w500/tjrX2oWRCM3Tvarz38zlZM7Uc10.jpg"
    #     )
    # db.session.add(new_movie)
    # db.session.commit()


class RateMovieForm(FlaskForm):
    rating = StringField('Your Rating out of 10')
    review = StringField('Your Review')
    submit = SubmitField('Done')
    
    
class AddMovieForm(FlaskForm):
    title = StringField('Movie Title', validators=[DataRequired()])
    submit = SubmitField('Add Movie')


@app.route("/")
def home():
    all_movies = Movie.query.order_by(Movie.rating).all()
    for i in range(len(all_movies)):
        all_movies[i].ranking = len(all_movies) - i
    db.session.commit()
    return render_template("index.html", movies=all_movies)


@app.route('/edit', methods=['GET', 'POST'])
def edit():
    form = RateMovieForm()
    movie_id = request.args.get("id")
    movie_to_update = Movie.query.get(movie_id)
    if form.validate_on_submit():
        movie_to_update.rating = form.rating.data
        movie_to_update.review = form.review.data
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("edit.html", movie=movie_to_update, form=form)


@app.route('/delete')
def delete_movie():
    movie_id = request.args.get("id")
    movie_to_delete = Movie.query.get(movie_id)
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect(url_for('home'))


@app.route('/add', methods=['GET', 'POST'])
def add_movie():
    form = AddMovieForm()
    
    if form.validate_on_submit():
        movie_title = form.title.data
        response = requests.get(f"{MOVIE_URL}/search/movie", params={'api_key': API_KEY, 'query': movie_title})
        data = response.json()['results']
        #print(data)
        return render_template("select.html", options=data)
        
    return render_template('add.html', form=form)


@app.route('/find')
def find_movie():
    movie_api_id = request.args.get('id')
    if movie_api_id:
        movie_api_url = f'{MOVIE_URL}/movie/{movie_api_id}'
        response = requests.get(movie_api_url, params={"api_key": API_KEY, 'language': "en-US"})
        data = response.json()
        print(data)
        new_movie = Movie(
            title=data['title'],
            year=data['release_date'].split('-')[0],
            description=data['overview'],
            img_url=f"{TMDB_IMAGE_URL}{data['poster_path']}"
        )
        db.session.add(new_movie)
        db.session.commit()
        return redirect(url_for('home'))
        

if __name__ == '__main__':
    app.run(debug=True)

