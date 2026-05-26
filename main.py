# VERSION 5 - MAIN TKINTER
import tkinter as tk
import random
import webbrowser
import subprocess
from config import *
from modele import Damier
from vue import InterfaceDames

class ControleurJeu:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Dames Classiques - Tournoi 10x10")
        self.root.configure(bg="#1a1a1a")
        
        self.vue = InterfaceDames(self.root, self.clic_souris, self.choisir_mode, self.recommencer_partie, self.lancer_menu)
        self.mode = None 
        self.etat = "MENU" 
        
        self.lancer_menu()

    def lancer_menu(self):
        self.etat = "MENU"
        self.mode = None
        self.vue.afficher_menu()

    def choisir_mode(self, mode):
        if mode == "distance":
            subprocess.Popen(["python", "serveur.py"], shell=True)
            self.root.after(1000, lambda: webbrowser.open("http://localhost:5000"))
            self.lancer_menu()
            return
            
        self.mode = mode
        self.etat = "JEU"
        self.recommencer_partie()

    def recommencer_partie(self):
        if self.etat == "JEU":
            self.modele = Damier()
            self.tour = "blanc"
            self.selection = None
            self.coups_possibles = {}
            self.jeu_termine = False
            self.actualiser()

    def clic_souris(self, event):
        if self.jeu_termine: return 

        c, l = event.x // DIM_CASE, event.y // DIM_CASE
        if not (0 <= l < TAILLE and 0 <= c < TAILLE): return

        pion = self.modele.grille[l][c]
        equipe_pion = self.modele.obtenir_equipe(pion)

        if equipe_pion == self.tour:
            self.selection = (l, c)
            self.coups_possibles = self.modele.calculer_mouvements(l, c)
        
        elif self.selection and (l, c) in self.coups_possibles:
            mange = self.coups_possibles[(l, c)]
            self.appliquer_mouvement(self.selection, (l, c), mange)
            self.selection = None
            self.coups_possibles = {}
            
            if not self.verifier_fin():
                self.tour = "noir" if self.tour == "blanc" else "blanc"
                
                if self.mode == "ia" and self.tour == "noir":
                    self.actualiser()
                    self.root.after(600, self.jouer_ia)
        
        self.actualiser()

    def appliquer_mouvement(self, dep, arr, mange):
        l1, c1, l2, c2 = dep[0], dep[1], arr[0], arr[1]
        p = self.modele.grille[l1][c1]
        self.modele.grille[l2][c2] = p
        self.modele.grille[l1][c1] = 0
        if mange: self.modele.grille[mange[0]][mange[1]] = 0
        
        if (l2 == 0 and p == 1) or (l2 == 9 and p == 2):
            if p in [1, 2]: self.modele.grille[l2][c2] += 2

    def jouer_ia(self):
        if self.jeu_termine: return
        coups_ia = []
        for l in range(TAILLE):
            for c in range(TAILLE):
                if self.modele.obtenir_equipe(self.modele.grille[l][c]) == "noir":
                    for dest, mange in self.modele.calculer_mouvements(l, c).items():
                        coups_ia.append(((l, c), dest, mange))
        if coups_ia:
            prises = [k for k in coups_ia if k[2]]
            choix = random.choice(prises if prises else coups_ia)
            self.appliquer_mouvement(choix[0], choix[1], choix[2])
            self.tour = "blanc"
            self.verifier_fin()
            self.actualiser()

    def verifier_fin(self):
        b = sum(row.count(1) + row.count(3) for row in self.modele.grille)
        n = sum(row.count(2) + row.count(4) for row in self.modele.grille)
        
        if b == 0: 
            self.jeu_termine = "LES NOIRS GAGNENT" if self.mode == "multi" else "DÉFAITE..."
        elif n == 0: 
            self.jeu_termine = "LES BLANCS GAGNENT" if self.mode == "multi" else "VICTOIRE !"
        return self.jeu_termine

    def actualiser(self):
        if self.etat == "JEU":
            self.vue.rafraichir(self.modele.grille, self.selection, self.coups_possibles, self.jeu_termine, self.tour)

if __name__ == "__main__":
    app = ControleurJeu()
    app.root.mainloop()
