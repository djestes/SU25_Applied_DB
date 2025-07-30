from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import plotly.graph_objs as go
import plotly.io as pio
from markupsafe import Markup
from sqlalchemy import text

app = Flask(__name__)

# Connect to your PostgreSQL database
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:Hoo$ierdaddy123@localhost:5432/NFL'
db = SQLAlchemy(app)

# Define a simple Player model
class Player(db.Model):
    __tablename__ = 'players'
    player_id = db.Column(db.String, primary_key=True)
    name = db.Column(db.String)
    position = db.Column(db.String)
    current_team = db.Column(db.String)

# Home route (list players)
@app.route('/')
def home():
    search = request.args.get('search', '')
    if search:
        players = Player.query.filter(
            (Player.name.ilike(f'%{search}%')) |
            (Player.current_team.ilike(f'%{search}%')) |
            (Player.player_id.ilike(f'%{search}%'))
        ).all()
    else:
        players = Player.query.limit(50).all()
    return render_template('players.html', players=players)


# Add a new player
@app.route('/add', methods=['POST'])
def add_player():
    new_player = Player(
        player_id=request.form['player_id'],
        name=request.form['name'],
        position=request.form['position'],
        current_team=request.form['team']
    )
    db.session.add(new_player)
    db.session.commit()
    return redirect(url_for('home'))

# Delete a player
@app.route('/delete/<path:player_id>', methods=['POST'])
def delete_player(player_id):
    player = Player.query.get(player_id)
    if player:
        db.session.delete(player)
        db.session.commit()
    return redirect(url_for('home'))

# Update a player
@app.route('/update/<path:player_id>', methods=['POST'])
def update_player(player_id):
    player = Player.query.get(player_id)
    if player:
        player.name = request.form['name']
        player.position = request.form['position']
        player.current_team = request.form['team']
        db.session.commit()
    return redirect(url_for('home'))

# Add stats    
@app.route('/stats')
def stats():
    # Determine which stat to show (default: rushing)
    stat_type = request.args.get('stat', 'rushing')

    # Map stat type to table and column
    stat_map = {
        'rushing': ('career_stats_rushing', 'rushing_yards', 'Rushing Yards'),
        'passing': ('career_stats_passing', 'passing_yards', 'Passing Yards'),
        'receiving': ('career_stats_receiving', 'receiving_yards', 'Receiving Yards')
    }

    table, column, label = stat_map.get(stat_type, stat_map['rushing'])

    # Build SQL query dynamically
    query = text(f"""
        SELECT name, {column}
        FROM {table}
        WHERE {column} ~ '^[0-9]+$'
        ORDER BY CAST({column} AS INT) DESC
        LIMIT 10;
    """)
    results = db.session.execute(query).fetchall()

    # Extract data
    names = [row[0] for row in results]
    values = [int(row[1]) for row in results]

    # Plotly chart
    fig = go.Figure([go.Bar(x=names, y=values, marker=dict(color='royalblue'))])
    fig.update_layout(
        title=f"Top 10 {label} Leaders",
        xaxis_title="Player",
        yaxis_title=label,
        template="plotly_white"
    )

    graph_html = pio.to_html(fig, full_html=False)
    return render_template('stats.html', graph=Markup(graph_html), stat_type=stat_type)

if __name__ == '__main__':
    app.run(debug=True)
