# serveur.py - Version 6
import os
import random
from flask import Flask, render_template
from flask_socketio import SocketIO, emit, join_room

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret_dames_2026'
socketio = SocketIO(app, cors_allowed_origins="*")

parties = {}

def initialiser_grille():
    grille = [[0]*10 for _ in range(10)]
    for l in range(4):
        for c in range(10):
            if (l + c) % 2 != 0:
                grille[l][c] = 2
    for l in range(6, 10):
        for c in range(10):
            if (l + c) % 2 != 0:
                grille[l][c] = 1
    return grille

def dans_grille(l, c):
    return 0 <= l < 10 and 0 <= c < 10

def calculer_coups_pion(grille, l, c, couleur, suite_rafle=None):
    coups_normaux = {}
    prises = {}
    val = grille[l][c]
    est_dame = val in [3, 4]
    directions_toutes = [(-1, -1), (-1, 1), (1, -1), (1, 1)]

    # 1. RECHERCHE DES PRISES
    for dl, dc in directions_toutes:
        if est_dame:
            ml, mc = l + dl, c + dc
            adversaire_trouve = False
            case_pion_mange = None
            while dans_grille(ml, mc):
                cible = grille[ml][mc]
                if cible == 0:
                    if adversaire_trouve:
                        prises[f"{ml},{mc}"] = case_pion_mange
                    ml += dl
                    mc += dc
                elif (couleur == "blanc" and cible in [2, 4]) or (couleur == "noir" and cible in [1, 3]):
                    if adversaire_trouve: break
                    adversaire_trouve = True
                    case_pion_mange = f"{ml},{mc}"
                    ml += dl
                    mc += dc
                else:
                    break
        else:
            saut_l, saut_c = l + dl, c + dc
            but_l, but_c = l + 2*dl, c + 2*dc
            if dans_grille(but_l, but_c) and grille[but_l][but_c] == 0:
                cible = grille[saut_l][saut_c]
                if (couleur == "blanc" and cible in [2, 4]) or (couleur == "noir" and cible in [1, 3]):
                    prises[f"{but_l},{but_c}"] = f"{saut_l},{saut_c}"

    if suite_rafle:
        return prises

    # 2. COUPS NORMAUX
    if not est_dame:
        directions_marche = [(-1, -1), (-1, 1)] if couleur == "blanc" else [(1, -1), (1, 1)]
        for dl, dc in directions_marche:
            nl, nc = l + dl, c + dc
            if dans_grille(nl, nc) and grille[nl][nc] == 0:
                coups_normaux[f"{nl},{nc}"] = None
    else:
        for dl, dc in directions_toutes:
            nl, nc = l + dl, c + dc
            while dans_grille(nl, nc) and grille[nl][nc] == 0:
                coups_normaux[f"{nl},{nc}"] = None
                nl += dl
                nc += dc

    return {"prises": prises, "normaux": coups_normaux}

def verifier_prises_globales(grille, couleur):
    toutes_prises = {}
    for l in range(10):
        for c in range(10):
            val = grille[l][c]
            if (couleur == "blanc" and val in [1, 3]) or (couleur == "noir" and val in [2, 4]):
                res = calculer_coups_pion(grille, l, c, couleur)
                if isinstance(res, dict) and res["prises"]:
                    toutes_prises[f"{l},{c}"] = res["prises"]
    return toutes_prises

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('join')
def on_join(data):
    room = data.get('room', 'default')
    mode = data.get('mode', 'web')
    join_room(room)
    
    if room not in parties:
        parties[room] = {
            "grille": initialiser_grille(),
            "tour": "blanc",
            "mode": mode,
            "suite_rafle": None
        }
    
    p = parties[room]
    emit('mise_a_jour', {"grille": p["grille"], "tour": p["tour"], "termine": None, "mode": p["mode"]})

@socketio.on('demande_coups')
def on_demande_coups(data):
    room = data.get('room', 'default')
    l, c = data['l'], data['c']
    p = parties.get(room)
    if not p: return

    val = p["grille"][l][c]
    if val == 0: return
    couleur = "blanc" if val in [1, 3] else "noir"

    if p["suite_rafle"]:
        if f"{l},{c}" != p["suite_rafle"]:
            emit('afficher_coups', {"coups": {}})
            return
        prises = calculer_coups_pion(p["grille"], l, c, couleur, suite_rafle=True)
        emit('afficher_coups', {"coups": prises})
        return

    prises_globales = verifier_prises_globales(p["grille"], p["tour"])
    res = calculer_coups_pion(p["grille"], l, c, couleur)

    if prises_globales:
        if f"{l},{c}" in prises_globales:
            emit('afficher_coups', {"coups": prises_globales[f"{l},{c}"]})
        else:
            emit('afficher_coups', {"coups": {}})
    else:
        emit('afficher_coups', {"coups": res["normaux"]})

@socketio.on('jouer_coup')
def on_jouer_coup(data):
    room = data.get('room', 'default')
    p = parties.get(room)
    if not p: return

    fl, fc = data['from_l'], data['from_c']
    tl, tc = data['to_l'], data['to_c']
    mange = data['mange']

    grille = p["grille"]
    val = grille[fl][fc]
    
    grille[tl][tc] = val
    grille[fl][fc] = 0

    if mange:
        ml, mc = map(int, mange.split(','))
        grille[ml][mc] = 0
        couleur = "blanc" if val in [1, 3] else "noir"
        nouvelles_prises = calculer_coups_pion(grille, tl, tc, couleur, suite_rafle=True)
        
        if nouvelles_prises:
            p["suite_rafle"] = f"{tl},{tc}"
            emit('mise_a_jour', {"grille": grille, "tour": p["tour"], "termine": None, "mode": p["mode"]}, room=room)
            return

    # Promotion en dame uniquement si le tour s'arrête ici
    if val == 1 and tl == 0: grille[tl][tc] = 3
    if val == 2 and tl == 9: grille[tl][tc] = 4

    p["suite_rafle"] = None
    p["tour"] = "noir" if p["tour"] == "blanc" else "blanc"

    if p["mode"] == "ia" and p["tour"] == "noir":
        emit('mise_a_jour', {"grille": grille, "tour": p["tour"], "termine": None, "mode": p["mode"]}, room=room)
        socketio.sleep(0.6)
        jouer_coup_ia(p, room)
        return

    emit('mise_a_jour', {"grille": grille, "tour": p["tour"], "termine": None, "mode": p["mode"]}, room=room)

def jouer_coup_ia(p, room):
    grille = p["grille"]
    prises_globales = verifier_prises_globales(grille, "noir")
    
    if prises_globales:
        depart = random.choice(list(prises_globales.keys()))
        arrivee = random.choice(list(prises_globales[depart].keys()))
        fl, fc = map(int, depart.split(','))
        tl, tc = map(int, arrivee.split(','))
        mange = prises_globales[depart][arrivee]
    else:
        coups_possibles = []
        for l in range(10):
            for c in range(10):
                if grille[l][c] in [2, 4]:
                    res = calculer_coups_pion(grille, l, c, "noir")
                    for dest in res["normaux"]:
                        coups_possibles.append(((l, c), map(int, dest.split(','))))
        if not coups_possibles:
            emit('mise_a_jour', {"grille": grille, "tour": "blanc", "termine": "Victoire des Blancs !", "mode": p["mode"]}, room=room)
            return
        (fl, fc), (tl, tc) = random.choice(coups_possibles)
        mange = None

    val = grille[fl][fc]
    grille[tl][tc] = val
    grille[fl][fc] = 0
    
    if mange:
        ml, mc = map(int, mange.split(','))
        grille[ml][mc] = 0
        nouvelles_prises = calculer_coups_pion(grille, tl, tc, "noir", suite_rafle=True)
        if nouvelles_prises:
            socketio.sleep(0.5)
            p["suite_rafle"] = f"{tl},{tc}"
            jouer_coup_ia(p, room)
            return

    if val == 2 and tl == 9: grille[tl][tc] = 4
    p["suite_rafle"] = None
    p["tour"] = "blanc"
    emit('mise_a_jour', {"grille": grille, "tour": p["tour"], "termine": None, "mode": p["mode"]}, room=room)

@socketio.on('recommencer')
def on_recommencer(data):
    room = data.get('room', 'default')
    if room in parties:
        parties[room]["grille"] = initialiser_grille()
        parties[room]["tour"] = "blanc"
        parties[room]["suite_rafle"] = None
        emit('mise_a_jour', {"grille": parties[room]["grille"], "tour": parties[room]["tour"], "termine": None, "mode": parties[room]["mode"]}, room=room)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
