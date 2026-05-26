# VERSION 5 - SERVEUR FLASK (WEB)
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from modele2 import DamierWeb

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

jeu = DamierWeb()
joueurs = {} 
tour = "blanc"
jeu_termine = False

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    global joueurs
    sid = request.sid
    if "blanc" not in joueurs.values():
        joueurs[sid] = "blanc"
        emit('assigner_couleur', {'couleur': 'blanc'})
    elif "noir" not in joueurs.values():
        joueurs[sid] = "noir"
        emit('assigner_couleur', {'couleur': 'noir'})
    else:
        emit('assigner_couleur', {'couleur': 'spectateur'})
    
    envoyer_etat_partie()

@socketio.on('disconnect')
def handle_disconnect():
    global joueurs
    if request.sid in joueurs:
        del joueurs[request.sid]

@socketio.on('demande_coups')
def handle_demande_coups(data):
    if joueurs.get(request.sid) != tour: return
    l, c = data['l'], data['c']
    coups = jeu.calculer_mouvements(l, c)
    emit('afficher_coups', {'coups': coups})

@socketio.on('jouer_coup')
def handle_jouer_coup(data):
    global tour, jeu_termine
    if joueurs.get(request.sid) != tour or jeu_termine: return
    
    l1, c1 = data['from_l'], data['from_c']
    l2, c2 = data['to_l'], data['to_c']
    mange = data['mange']

    p = jeu.grille[l1][c1]
    jeu.grille[l2][c2] = p
    jeu.grille[l1][c1] = 0
    
    if mange:
        ml, mc = map(int, mange.split(','))
        jeu.grille[ml][mc] = 0

    if (l2 == 0 and p == 1) or (l2 == 9 and p == 2):
        if p in [1, 2]: jeu.grille[l2][c2] += 2

    b = sum(row.count(1) + row.count(3) for row in jeu.grille)
    n = sum(row.count(2) + row.count(4) for row in jeu.grille)
    if b == 0: jeu_termine = "LES NOIRS GAGNENT !"
    elif n == 0: jeu_termine = "LES BLANCS GAGNENT !"

    tour = "noir" if tour == "blanc" else "blanc"
    envoyer_etat_partie()

@socketio.on('recommencer')
def handle_recommencer():
    global jeu, tour, jeu_termine
    jeu = DamierWeb()
    tour = "blanc"
    jeu_termine = False
    envoyer_etat_partie()

def envoyer_etat_partie():
    socketio.emit('mise_a_jour', {
        'grille': jeu.grille,
        'tour': tour,
        'termine': jeu_termine
    })

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)
