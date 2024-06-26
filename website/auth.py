import re
from flask import Blueprint, flash, redirect, render_template, url_for, request, session
from flask_login import login_user, login_required, logout_user, current_user
from .models import User, Game, Leaderboard, PlayerScore, Event, db
from datetime import datetime

auth = Blueprint('auth', __name__)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    data = request.form
    dbUser = ""
    if request.method == 'POST':
        inputEmail = request.form.get('email')
        inputPassword = request.form.get('password1')
        dbUser = User.query.filter_by(email=inputEmail).first()
        if dbUser:
            if dbUser.check_password(inputPassword):
                flash('Logged in successfully', category='success')
                login_user(dbUser, remember=True)
                return redirect(url_for('views.home'))
        else:
            flash('Invalid email or password', category='error')
    return render_template('login.html', user=current_user)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))


@auth.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        regemail = request.form.get('email')
        regusername = request.form.get('username')
        regpassword1 = request.form.get('password1')
        regpassword2 = request.form.get('password2')
        is_game_owner = True if request.form.get('is_game_owner') else False

        if len(regemail) < 4:
            flash('Email must be greater than 4 characters.', category='error')
        elif len(regusername) < 2:
            flash('Username must be greater than 1 character.', category='error')
        elif regpassword1 != regpassword2:
            flash('Passwords must match', category='error')
        elif len(regpassword1) < 7:
            flash('Minimum 8 characters required', category='error')
        else:
            new_user = User(
                username=regusername,
                email=regemail,
                is_game_owner=is_game_owner
            )
            new_user.set_password(regpassword1)  # Set the password
            db.session.add(new_user)  # Add the user to the session
            db.session.commit()
            login_user(new_user, remember=True)
            flash('Account created!', category='success')
            return redirect(url_for('views.home'))

    return render_template('register.html', user=current_user)

@auth.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == 'ADMINPASS':  # Replace with your desired admin password
            session['admin_logged_in'] = True
            return redirect(url_for('auth.admin_dashboard'))
        else:
            flash('Invalid password. Please try again.', 'error')
            return redirect(url_for('auth.admin_login'))
    return render_template('admin_login.html')

@auth.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('auth.admin_login'))

@auth.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('auth.admin_login'))
    users = User.query.all()
    games = Game.query.all()
    leaderboards = Leaderboard.query.all()
    player_scores = PlayerScore.query.all()
    events = Event.query.all()
    return render_template('admin_dashboard.html', users=users, games=games, leaderboards=leaderboards, player_scores=player_scores, events=events)

@auth.route('/add_user', methods=['POST'])
def add_user():
    if not session.get('admin_logged_in'):
        return redirect(url_for('auth.admin_login'))
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    is_game_owner = True if request.form.get('is_game_owner') else False
    new_user = User(username=username, email=email, is_game_owner=is_game_owner)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()
    return redirect(url_for('auth.admin_dashboard'))

@auth.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('auth.admin_login'))
    user = User.query.get_or_404(user_id)
    if request.method == 'POST':
        user.username = request.form.get('username')
        user.email = request.form.get('email')
        user.is_game_owner = True if request.form.get('is_game_owner') else False
        db.session.commit()
        return redirect(url_for('auth.admin_dashboard'))
    return render_template('edit_user.html', user=user)

@auth.route('/delete_user/<int:user_id>')
def delete_user(user_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('auth.admin_login'))
    user = User.query.get_or_404(user_id)

    # Delete associated data
    PlayerScore.query.filter_by(player_id=user.id).delete()
    Event.query.filter_by(owner_id=user.id).delete()
    Game.query.filter_by(owner_id=user.id).delete()

    db.session.delete(user)
    db.session.commit()
    return redirect(url_for('auth.admin_dashboard'))

@auth.route('/add_game', methods=['POST'])
def add_game():
    if not session.get('admin_logged_in'):
        return redirect(url_for('auth.admin_login'))
    title = request.form.get('title')
    description = request.form.get('description')
    release_date = datetime.strptime(request.form.get('release_date'), '%Y-%m-%d')
    owner_id = request.form.get('owner_id')
    new_game = Game(title=title, description=description, release_date=release_date, owner_id=owner_id)
    db.session.add(new_game)
    db.session.commit()
    return redirect(url_for('auth.admin_dashboard'))

@auth.route('/edit_game/<int:game_id>', methods=['GET', 'POST'])
def edit_game(game_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('auth.admin_login'))
    game = Game.query.get_or_404(game_id)
    users = User.query.all()
    if request.method == 'POST':
        game.title = request.form.get('title')
        game.description = request.form.get('description')
        game.release_date = datetime.strptime(request.form.get('release_date'), '%Y-%m-%d')
        game.owner_id = request.form.get('owner_id')
        db.session.commit()
        return redirect(url_for('auth.admin_dashboard'))
    return render_template('edit_game.html', game=game, users=users)

@auth.route('/delete_game/<int:game_id>')
def delete_game(game_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('auth.admin_login'))
    game = Game.query.get_or_404(game_id)

    # Delete associated data
    Leaderboard.query.filter_by(game_id=game.id).delete()
    PlayerScore.query.filter_by(game_id=game.id).delete()
    Event.query.filter_by(game_id=game.id).delete()

    db.session.delete(game)
    db.session.commit()
    return redirect(url_for('auth.admin_dashboard'))

@auth.route('/transfer_ownership/<int:game_id>', methods=['GET', 'POST'])
def transfer_ownership(game_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('auth.admin_login'))
    game = Game.query.get_or_404(game_id)
    game_owners = User.query.filter_by(is_game_owner=True).all()

    if request.method == 'POST':
        new_owner_id = request.form.get('new_owner_id')
        game.owner_id = new_owner_id
        db.session.commit()
        return redirect(url_for('auth.admin_dashboard'))

    return render_template('transfer_ownership.html', game=game, game_owners=game_owners)

@auth.route('/add_leaderboard', methods=['POST'])
def add_leaderboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('auth.admin_login'))
    game_id = request.form.get('game_id')
    name = request.form.get('name')

    # Check if the game already has a leaderboard
    existing_leaderboard = Leaderboard.query.filter_by(game_id=game_id).first()

    if existing_leaderboard:
        # If a leaderboard already exists, append a number to the name
        count = Leaderboard.query.filter_by(game_id=game_id).count()
        name = f"{name} {count + 1}"
    else:
        # If it's the first leaderboard for the game, set the name to "Main Leaderboard"
        name = "Main Leaderboard"

    new_leaderboard = Leaderboard(game_id=game_id, name=name)
    db.session.add(new_leaderboard)
    db.session.commit()
    return redirect(url_for('auth.admin_dashboard'))

@auth.route('/edit_leaderboard/<int:leaderboard_id>', methods=['GET', 'POST'])
def edit_leaderboard(leaderboard_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('auth.admin_login'))
    leaderboard = Leaderboard.query.get_or_404(leaderboard_id)
    games = Game.query.all()
    if request.method == 'POST':
        leaderboard.game_id = request.form.get('game_id')
        db.session.commit()
        return redirect(url_for('auth.admin_dashboard'))
    return render_template('edit_leaderboard.html', leaderboard=leaderboard, games=games)

@auth.route('/delete_leaderboard/<int:leaderboard_id>')
def delete_leaderboard(leaderboard_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('auth.admin_login'))
    leaderboard = Leaderboard.query.get_or_404(leaderboard_id)

    # Delete associated player scores
    PlayerScore.query.filter_by(leaderboard_id=leaderboard.id).delete()

    db.session.delete(leaderboard)
    db.session.commit()
    return redirect(url_for('auth.admin_dashboard'))

@auth.route('/add_player_score', methods=['POST'])
def add_player_score():
    if not session.get('admin_logged_in'):
        return redirect(url_for('auth.admin_login'))
    player_id = request.form.get('player_id')
    leaderboard_id = request.form.get('leaderboard_id')
    elo_rating = request.form.get('elo_rating')
    matches_played = request.form.get('matches_played')
    matches_won = request.form.get('matches_won')
    matches_lost = request.form.get('matches_lost')
    new_player_score = PlayerScore(player_id=player_id, leaderboard_id=leaderboard_id, elo_rating=elo_rating, matches_played=matches_played, matches_won=matches_won, matches_lost=matches_lost)
    db.session.add(new_player_score)
    db.session.commit()
    return redirect(url_for('auth.admin_dashboard'))

@auth.route('/edit_player_score/<int:player_score_id>', methods=['GET', 'POST'])
def edit_player_score(player_score_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('auth.admin_login'))
    player_score = PlayerScore.query.get_or_404(player_score_id)
    users = User.query.all()
    leaderboards = Leaderboard.query.all()
    if request.method == 'POST':
        player_score.player_id = request.form.get('player_id')
        player_score.leaderboard_id = request.form.get('leaderboard_id')
        player_score.elo_rating = request.form.get('elo_rating')
        player_score.matches_played = request.form.get('matches_played')
        player_score.matches_won = request.form.get('matches_won')
        player_score.matches_lost = request.form.get('matches_lost')
        db.session.commit()
        return redirect(url_for('auth.admin_dashboard'))
    return render_template('edit_player_score.html', player_score=player_score, users=users, leaderboards=leaderboards)

@auth.route('/delete_player_score/<int:player_score_id>')
def delete_player_score(player_score_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('auth.admin_login'))
    player_score = PlayerScore.query.get_or_404(player_score_id)
    db.session.delete(player_score)
    db.session.commit()
    return redirect(url_for('auth.admin_dashboard'))

@auth.route('/add_event', methods=['POST'])
def add_event():
    if not session.get('admin_logged_in'):
        return redirect(url_for('auth.admin_login'))
    game_id = request.form.get('game_id')
    owner_id = request.form.get('owner_id')
    start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%dT%H:%M')
    end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%dT%H:%M')
    new_event = Event(game_id=game_id, owner_id=owner_id, start_date=start_date, end_date=end_date)
    db.session.add(new_event)
    db.session.commit()
    return redirect(url_for('auth.admin_dashboard'))

@auth.route('/edit_event/<int:event_id>', methods=['GET', 'POST'])
def edit_event(event_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('auth.admin_login'))
    event = Event.query.get_or_404(event_id)
    users = User.query.all()
    games = Game.query.all()
    if request.method == 'POST':
        event.game_id = request.form.get('game_id')
        event.owner_id = request.form.get('owner_id')
        event.start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%dT%H:%M')
        event.end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%dT%H:%M')
        db.session.commit()
        return redirect(url_for('auth.admin_dashboard'))
    return render_template('edit_event.html', event=event, users=users, games=games)
@auth.route('/delete_event/<int:event_id>')
def delete_event(event_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('auth.admin_login'))
    event = Event.query.get_or_404(event_id)
    db.session.delete(event)
    db.session.commit()
    return redirect(url_for('auth.admin_dashboard'))