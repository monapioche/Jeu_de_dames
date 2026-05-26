# VERSION 5 - VUE TKINTER
import tkinter as tk
from config import *

class InterfaceDames:
    def __init__(self, root, clic_callback, callback_mode, callback_recommencer, callback_menu):
        self.root = root
        self.clic_callback = clic_callback
        self.callback_mode = callback_mode
        self.callback_recommencer = callback_recommencer
        self.callback_menu = callback_menu
        
        self.canvas = tk.Canvas(root, width=TAILLE*DIM_CASE, height=TAILLE*DIM_CASE, highlightthickness=0, bg="#1a1a1a")
        self.canvas.pack(padx=25, pady=15)
        
        self.barre_outils = tk.Frame(root, bg="#1a1a1a")
        self.boutons_menu = []

    def afficher_menu(self):
        self.canvas.delete("all")
        self.nettoyer_boutons_menu()
        self.barre_outils.pack_forget() 
        
        cx, cy = (TAILLE*DIM_CASE)//2, (TAILLE*DIM_CASE)//2
        self.canvas.create_text(cx, cy-120, text="JEU DE DAMES", fill="white", font=("Impact", 50))
        
        btn_ia = tk.Button(self.root, text="CONTRE L'IA", font=("Arial", 14, "bold"), 
                           bg="#8B0000", fg="white", width=22, command=lambda: self.callback_mode("ia"))
        self.canvas.create_window(cx, cy-30, window=btn_ia)
        self.boutons_menu.append(btn_ia)
        
        btn_multi = tk.Button(self.root, text="MULTIJOUEURS (2J LOCAL)", font=("Arial", 14, "bold"), 
                              bg="#2c3e50", fg="white", width=22, command=lambda: self.callback_mode("multi"))
        self.canvas.create_window(cx, cy+30, window=btn_multi)
        self.boutons_menu.append(btn_multi)

        btn_distance = tk.Button(self.root, text="JOUER À DISTANCE (WEB)", font=("Arial", 14, "bold"), 
                              bg="#d35400", fg="white", width=22, command=lambda: self.callback_mode("distance"))
        self.canvas.create_window(cx, cy+90, window=btn_distance)
        self.boutons_menu.append(btn_distance)

    def afficher_barre_outils(self):
        for widget in self.barre_outils.winfo_children():
            widget.destroy()

        btn_reset = tk.Button(self.barre_outils, text="Recommencer", font=("Arial", 11, "bold"),
                              bg="#27ae60", fg="white", padx=10, pady=5, command=self.callback_recommencer)
        btn_reset.pack(side=tk.LEFT, padx=10)

        btn_menu = tk.Button(self.barre_outils, text="Retour au Menu", font=("Arial", 11, "bold"),
                             bg="#7f8c8d", fg="white", padx=10, pady=5, command=self.callback_menu)
        btn_menu.pack(side=tk.RIGHT, padx=10)
        
        self.barre_outils.pack(pady=10, fill=tk.X)

    def nettoyer_boutons_menu(self):
        for btn in self.boutons_menu:
            try: btn.destroy()
            except: pass
        self.boutons_menu = []

    def dessiner_dame(self, x1, y1, x2, y2, couleur):
        self.canvas.create_oval(x1+6, y1+12, x2-6, y2-2, fill="#111", outline="")
        self.canvas.create_oval(x1+6, y1+8, x2-6, y2-4, fill=couleur, outline="#000")
        self.canvas.create_oval(x1+6, y1+4, x2-6, y2-8, fill=couleur, outline="#000")
        self.canvas.create_text((x1+x2)/2, (y1+y2)/2 - 2, text="♔", fill="#000", font=("Arial", 18, "bold"))

    def rafraichir(self, plateau, selection, coups, termine, tour):
        self.canvas.delete("all")
        self.nettoyer_boutons_menu()
        self.afficher_barre_outils() 
        
        self.canvas.bind("<Button-1>", self.clic_callback)
        
        for l in range(TAILLE):
            for c in range(TAILLE):
                x1, y1, x2, y2 = c*DIM_CASE, l*DIM_CASE, (c+1)*DIM_CASE, (l+1)*DIM_CASE
                couleur_case = COULEUR_BEIGE if (l + c) % 2 == 0 else COULEUR_NOIRE
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=couleur_case, outline="")
                
                p = plateau[l][c]
                if p != 0:
                    couleur_pion = PION_BLANC if p in [1, 3] else PION_NOIR
                    if p in [3, 4]:
                        self.dessiner_dame(x1, y1, x2, y2, couleur_pion)
                    else:
                        self.canvas.create_oval(x1+8, y1+10, x2-8, y2-4, fill="#111", outline="")
                        self.canvas.create_oval(x1+7, y1+7, x2-7, y2-7, fill=couleur_pion, outline="#000")
                    if selection == (l, c):
                        self.canvas.create_rectangle(x1, y1, x2, y2, outline="#FFD700", width=3)

                if (l, c) in coups:
                    self.canvas.create_oval(x1+22, y1+22, x2-22, y2-22, fill="#FFF", outline="#000")

        if termine:
            self.afficher_fin(termine)

    def afficher_fin(self, msg):
        self.canvas.create_rectangle(0, 0, TAILLE*DIM_CASE, TAILLE*DIM_CASE, fill="black", stipple="gray50")
        cx, cy = (TAILLE*DIM_CASE)//2, (TAILLE*DIM_CASE)//2
        self.canvas.create_rectangle(cx-200, cy-70, cx+200, cy+70, fill="#2c3e50", outline="white", width=4)
        txt_color = "#2ecc71" if "VICTOIRE" in msg or "GAGNE" in msg else "#e74c3c"
        self.canvas.create_text(cx, cy-15, text=msg, fill=txt_color, font=("Impact", 40))
        self.canvas.create_text(cx, cy+35, text="BOUTONS EN BAS", fill="white", font=("Arial", 11, "bold"))
