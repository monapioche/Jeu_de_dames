# serveur.py - Version 8
import os
import random
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret_dames_2026'
socketio = SocketIO(app, cors_allowed_origins="*")

parties = {}

def initialiser_grille():
    grille = [[0]*10 for _ in range(10)]
    for l in range(4):
        for c in range(10):
            if (l + c) % 2 != 0: grille[l][c] = 2
    for l in range(6, 10):
        for c in range(10):
            if (l + c) % 2 != 0: grille[l][c] = 1
    return grille

def dans_grille(l, c):
    return 0 <= l < 10 and 0 <= c < 10

def copier_grille(grille):
    return [ligne[:] for ligne in grille]

def chercher_rafles_pion(grille, l, c, couleur, est_dame, pions_manges_actuels=None):
    if pions_manges_actuels is None:
        pions_manges_actuels = []

    directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    rafles_trouvees = []

    for dl, dc in directions:
        if est_dame:
            ml, mc = l + dl, c + dc
            adversaire_trouve = False
            case_pion_mange = None
            while dans_grille(ml, mc):
                cible = grille[ml][mc]
                if cible == 0:
                    if adversaire_trouve and (ml, mc) not in pions_manges_actuels:
                        nouvelle_grille = copier_grille(grille)
                        nouvelle_grille[ml][mc] = nouvelle_grille[l][c]
                        nouvelle_grille[l][c] = 0
                        manges = pions_manges_actuels + [case_pion_mange]
                        
                        sub_rafles = chercher_rafles_pion(nouvelle_grille, ml, mc, couleur, est_dame, manges)
                        if sub_rafles:
                            rafles_trouvees.extend(sub_rafles)
                        else:
                            rafles_trouvees.append({"fin": f"{ml},{mc}", "manges": manges})
                    ml += dl
                    mc += dc
                elif (couleur == "blanc" and cible in [2, 4]) or (couleur == "noir" and cible in [1, 3]):
                    if adversaire_trouve or f"{ml},{mc}" in pions_manges_actuels: break
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
                case_pion_mange = f"{saut_l},{saut_c}"
                if ((couleur == "blanc" and cible in [2, 4]) or (couleur == "noir" and cible in [1, 3])) and case_pion_mange not in pions_manges_actuels:
                    nouvelle_grille = copier_grille(grille)
                    nouvelle_grille[but_l][but_c] = nouvelle_grille[l][c]
                    nouvelle_grille[l][c] = 0
                    manges = pions_manges_actuels + [case_pion_mange]
                    
                    sub_rafles = chercher_rafles_pion(nouvelle_grille, but_l, but_c, couleur, est_dame, manges)
                    if sub_rafles:
                        rafles_trouvees.extend(sub_rafles)
                    else:
                        rafles_trouvees.append({"fin": f"{but_l},{but_c}", "manges": manges})

    return rafles_trouvees

def calculer_meilleurs_coups(grille, l, c, couleur):
    val = grille[l][c]
    est_dame = val in [3, 4]
    
    rafles = chercher_rafles_pion(grille, l, c, couleur, est_dame)
    
    if rafles:
        max_manges = max(len(r["manges"]) for r in rafles)
        meilleures_rafles = [r for r in rafles if len(r["manges"]) == max_manges]
        
        coups_prises = {}
        for r in meilleures_rafles:
            coups_prises[r["fin"]] = r["manges"]
        return {"prises": coups_prises, "normaux": {}}

    coups_normaux = {}
    if not est_dame:
        directions_marche = [(-1, -1), (-1, 1)] if couleur == "blanc" else [(1, -1), (1, 1)]
        for dl, dc in directions_marche:
            nl, nc = l + dl, c + dc
            if dans_grille(nl, nc) and grille[nl][nc] == 0:
                coups_normaux[f"{nl},{nc}"] = []
    else:
        directions_toutes = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        for dl, dc in directions_toutes:
            nl, nc = l + dl, c + dc
            while dans_grille(nl, nc) and grille[nl][nc] == 0:
                coups_normaux[f"{nl},{nc}"] = []
                nl += dl
                nc += dc

    return {"prises": {}, "normaux": coups_normaux}

def verifier_prises_globales(grille, couleur):
    toutes_prises = {}
    max_absolu = 0
    
    for l in range(10):
        for c in range(10):
            val = grille[l][c]
            if (couleur == "blanc" and val in [1, 3]) or (couleur == "noir" and val in [2, 4]):
                res = calculer_meilleurs_coups(grille, l, c, couleur)
                if res["prises"]:
                    cle_premiere = list(res["prises"].keys())[0]
                    nb_manges = len(res["prises"][cle_premiere])
                    if nb_manges > max_absolu:
                        max_absolu = nb_manges
                        toutes_prises = {f"{l},{c}": res["prises"]}
                    elif nb_manges == max_absolu:
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
    sid = request.sid
    
    if room not in parties:
        parties[room] = {
            "grille": initialiser_grille(),
            "tour": "blanc",
            "mode": mode,
            "joueurs": {"blanc": None, "noir": None}
        }
    
    p = parties[room]
    
    role = "tout"
    if mode == "web":
        if p["joueurs"]["blanc"] == sid:
            role = "blanc"
        elif p["joueurs"]["noir"] == sid:
            role = "noir"
        elif p["joueurs"]["blanc"] is None:
            p["joueurs"]["blanc"] = sid
            role = "blanc"
        elif p["joueurs"]["noir"] is None:
            p["joueurs"]["noir"] = sid
            role = "noir"
        else:
            role = "spectateur"

    emit('assigner_couleur', {"couleur": role})
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

    prises_globales = verifier_prises_globales(p["grille"], p["tour"])
    res = calculer_meilleurs_coups(p["grille"], l, c, couleur)

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
    manges = data['manges']

    grille = p["grille"]
    val = grille[fl][fc]
    
    grille[tl][tc] = val
    grille[fl][fc] = 0

    if manges:
        for m in manges:
            ml, mc = map(int, m.split(','))
            grille[ml][mc] = 0

    if val == 1 and tl == 0: grille[tl][tc] = 3
    if val == 2 and tl == 9: grille[tl][tc] = 4

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
        manges = prises_globales[depart][arrivee]
    else:
        coups_possibles = []
        for l in range(10):
            for c in range(10):
                if grille[l][c] in [2, 4]:
                    res = calculer_meilleurs_coups(grille, l, c, "noir")
                    for dest in res["normaux"]:
                        coups_possibles.append(((l, c), map(int, dest.split(','))))
        if not coups_possibles:
            emit('mise_a_jour', {"grille": grille, "tour": "blanc", "termine": "Victoire des Blancs !", "mode": p["mode"]}, room=room)
            return
        (fl, fc), (tl, tc) = random.choice(coups_possibles)
        manges = []

    val = grille[fl][fc]
    grille[tl][tc] = val
    grille[fl][fc] = 0
    
    if manges:
        for m in manges:
            ml, mc = map(int, m.split(','))
            grille[ml][mc] = 0

    if val == 2 and tl == 9: grille[tl][tc] = 4
    p["tour"] = "blanc"
    emit('mise_a_jour', {"grille": grille, "tour": p["tour"], "termine": None, "mode": p["mode"]}, room=room)

@socketio.on('recommencer')
def on_recommencer(data):
    room = data.get('room', 'default')
    if room in parties:
        parties[room]["grille"] = initialiser_grille()
        parties[room]["tour"] = "blanc"
        emit('mise_a_jour', {"grille": parties[room]["grille"], "tour": parties[room]["tour"], "termine": None, "mode": parties[room]["mode"]}, room=room)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
