# VERSION 5 - MODELE LOCAL (IA & 2J LOCAL)
from config import TAILLE

class Damier:
    def __init__(self):
        self.grille = self.generer_plateau()

    def generer_plateau(self):
        p = [[0 for _ in range(TAILLE)] for _ in range(TAILLE)]
        for l in range(TAILLE):
            for c in range(TAILLE):
                if (l + c) % 2 != 0:
                    if l < 4: p[l][c] = 2  # Noirs
                    elif l > 5: p[l][c] = 1 # Blancs
        return p

    def obtenir_equipe(self, pion):
        if pion in [1, 3]: return "blanc"
        if pion in [2, 4]: return "noir"
        return None

    def calculer_mouvements(self, l, c):
        piece = self.grille[l][c]
        equipe = self.obtenir_equipe(piece)
        if not equipe: return {}
        
        mouvements = {}
        dirs = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        est_dame = piece in [3, 4]

        if est_dame:
            for dl, dc in dirs:
                pion_a_manger = None
                for dist in range(1, TAILLE):
                    nl, nc = l + dl*dist, c + dc*dist
                    if not (0 <= nl < TAILLE and 0 <= nc < TAILLE): break
                    cible = self.grille[nl][nc]
                    if cible == 0:
                        if pion_a_manger is None: mouvements[(nl, nc)] = None
                        else: mouvements[(nl, nc)] = pion_a_manger
                    else:
                        if self.obtenir_equipe(cible) == equipe: break
                        if pion_a_manger: break
                        pion_a_manger = (nl, nc)
        else:
            sens = -1 if equipe == "blanc" else 1
            for dl, dc in dirs:
                sl, sc = l + dl*2, c + dc*2
                ml, mc = l + dl, c + dc
                if 0 <= sl < TAILLE and 0 <= sc < TAILLE:
                    if self.grille[sl][sc] == 0:
                        cible = self.grille[ml][mc]
                        if cible != 0 and self.obtenir_equipe(cible) != equipe:
                            mouvements[(sl, sc)] = (ml, mc)
                if dl == sens:
                    nl, nc = l + dl, c + dc
                    if 0 <= nl < TAILLE and 0 <= nc < TAILLE and self.grille[nl][nc] == 0:
                        mouvements[(nl, nc)] = None
        return mouvements
