"""
Tracker vydavkov - Python + GUI (Tkinter)
Predmet: Programovacie techniky
Funkcie: pridanie, mazanie, filtrovanie podla kategorie, sucet, ukladanie do CSV.
Moderne farebne rozhranie: karty, legenda kategorii, hover efekty na tlacidlach.
"""

import csv
import os
import tkinter as tk
from datetime import date
from tkinter import messagebox, ttk

# Subor s datami sa uklada vedla programu
SUBOR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vydavky.csv")

# Kategoria -> farba pozadia riadku v tabulke
FARBY_KATEGORII = {
    "Jedlo": "#FEF08A",     # zlta
    "Doprava": "#BFDBFE",   # modra
    "Škola": "#DDD6FE",     # fialova
    "Zábava": "#FECACA",    # cervena
    "Bývanie": "#BBF7D0",   # zelena
    "Iné": "#E2E8F0",       # siva
}
KATEGORIE = list(FARBY_KATEGORII.keys())

# Farebna paleta rozhrania
POZADIE = "#F1F5F9"
KARTA = "#FFFFFF"
OBRYS = "#E2E8F0"
HLAVICKA = "#312E81"        # tmavo indigo
HLAVICKA_TEXT2 = "#C7D2FE"
AKCENT = "#4F46E5"          # indigo
TEXT = "#1E293B"
TEXT_SEDY = "#64748B"
ZELENA, ZELENA_HOVER = "#16A34A", "#15803D"
CERVENA, CERVENA_HOVER = "#DC2626", "#B91C1C"
ZLTA = "#FDE047"

PISMO = ("Segoe UI", 10)
PISMO_POPIS = ("Segoe UI", 9, "bold")


class TrackerVydavkov:
    def __init__(self, root):
        self.root = root
        self.root.title("Tracker výdavkov")
        self.root.minsize(760, 600)
        self.root.configure(bg=POZADIE)
        self.vycentruj(800, 640)

        # Zoznam vsetkych vydavkov: kazdy je (datum, popis, kategoria, suma)
        self.vydavky = []

        self.nastav_styl()
        self.vytvor_hlavicku()

        telo = tk.Frame(self.root, bg=POZADIE)
        telo.pack(fill="both", expand=True, padx=18, pady=14)

        self.vytvor_formular(telo)
        self.vytvor_filter(telo)
        self.vytvor_tabulku(telo)
        self.vytvor_spodny_panel(telo)

        self.nacitaj()
        self.obnov_tabulku()

        # Klavesove skratky: Enter = pridat, Delete = zmazat
        self.root.bind("<Return>", lambda e: self.pridaj())
        self.tabulka.bind("<Delete>", lambda e: self.zmaz_vybrane())

        self.root.protocol("WM_DELETE_WINDOW", self.pri_zatvoreni)
        self.popis_entry.focus_set()

    # ---------- Pomocne funkcie ----------
    def vycentruj(self, sirka, vyska):
        x = (self.root.winfo_screenwidth() - sirka) // 2
        y = max((self.root.winfo_screenheight() - vyska) // 2 - 30, 0)
        self.root.geometry(f"{sirka}x{vyska}+{x}+{y}")

    @staticmethod
    def karta(rodic):
        """Biely panel s tenkym obrysom (vyzera ako 'karta')."""
        return tk.Frame(rodic, bg=KARTA, highlightbackground=OBRYS,
                        highlightthickness=1)

    @staticmethod
    def tlacidlo(rodic, text, prikaz, farba, farba_hover):
        """Ploche tlacidlo, ktore meni farbu pri nabehnuti mysou."""
        t = tk.Button(
            rodic, text=text, command=prikaz, bg=farba, fg="white",
            activebackground=farba_hover, activeforeground="white",
            font=("Segoe UI", 10, "bold"), relief="flat", bd=0,
            padx=18, pady=7, cursor="hand2",
        )
        t.bind("<Enter>", lambda e: t.config(bg=farba_hover))
        t.bind("<Leave>", lambda e: t.config(bg=farba))
        return t

    @staticmethod
    def vstup(rodic, premenna, sirka):
        return tk.Entry(
            rodic, textvariable=premenna, width=sirka, font=PISMO, fg=TEXT,
            bg="#F8FAFC", relief="flat", insertbackground=TEXT,
            highlightthickness=1, highlightbackground="#CBD5E1",
            highlightcolor=AKCENT,
        )

    # ---------- Vytvorenie rozhrania ----------
    def nastav_styl(self):
        styl = ttk.Style()
        styl.theme_use("clam")  # tema, ktora podporuje farby

        # Tabulka bez okraja, vyssie riadky
        styl.layout("Treeview", [("Treeview.treearea", {"sticky": "nswe"})])
        styl.configure("Treeview", rowheight=34, font=PISMO, borderwidth=0,
                       background=KARTA, fieldbackground=KARTA, foreground=TEXT)
        styl.configure("Treeview.Heading", background=AKCENT, foreground="white",
                       font=("Segoe UI", 10, "bold"), relief="flat",
                       padding=(8, 9), borderwidth=0)
        styl.map("Treeview.Heading", background=[("active", "#4338CA")])
        styl.map("Treeview", background=[("selected", HLAVICKA)],
                 foreground=[("selected", "white")])

        # Rozbalovacie zoznamy
        styl.configure("TCombobox", fieldbackground="#F8FAFC", background="#E2E8F0",
                       foreground=TEXT, arrowcolor=AKCENT, padding=5,
                       bordercolor="#CBD5E1", lightcolor="#CBD5E1",
                       darkcolor="#CBD5E1")
        styl.map("TCombobox", fieldbackground=[("readonly", "#F8FAFC")],
                 selectbackground=[("readonly", "#F8FAFC")],
                 selectforeground=[("readonly", TEXT)])
        self.root.option_add("*TCombobox*Listbox.font", PISMO)
        self.root.option_add("*TCombobox*Listbox.selectBackground", AKCENT)

        # Posuvnik
        styl.configure("Vertical.TScrollbar", background="#CBD5E1",
                       troughcolor=KARTA, bordercolor=KARTA, arrowcolor=TEXT_SEDY)

    def vytvor_hlavicku(self):
        hlavicka = tk.Frame(self.root, bg=HLAVICKA)
        hlavicka.pack(fill="x")
        tk.Label(hlavicka, text="Tracker výdavkov", bg=HLAVICKA, fg="white",
                 font=("Segoe UI", 20, "bold")).pack(pady=(14, 0))
        tk.Label(hlavicka, text="Prehľad a evidencia osobných výdavkov",
                 bg=HLAVICKA, fg=HLAVICKA_TEXT2,
                 font=("Segoe UI", 10)).pack(pady=(0, 14))
        # Tenky farebny pasik pod hlavickou
        tk.Frame(self.root, bg=ZLTA, height=4).pack(fill="x")

    def vytvor_formular(self, rodic):
        karta = self.karta(rodic)
        karta.pack(fill="x")
        vnutro = tk.Frame(karta, bg=KARTA)
        vnutro.pack(fill="x", padx=16, pady=14)
        vnutro.columnconfigure(0, weight=1)

        tk.Label(vnutro, text="NOVÝ VÝDAVOK", bg=KARTA, fg=AKCENT,
                 font=("Segoe UI", 9, "bold")).grid(row=0, column=0,
                                                    sticky="w", pady=(0, 8))

        popisky = [("POPIS", 0), ("SUMA (€)", 1), ("KATEGÓRIA", 2)]
        for text, stlpec in popisky:
            tk.Label(vnutro, text=text, bg=KARTA, fg=TEXT_SEDY,
                     font=PISMO_POPIS).grid(row=1, column=stlpec, sticky="w",
                                            padx=(0, 10))

        self.popis_var = tk.StringVar()
        self.popis_entry = self.vstup(vnutro, self.popis_var, 26)
        self.popis_entry.grid(row=2, column=0, sticky="ew", padx=(0, 10), ipady=6)

        self.suma_var = tk.StringVar()
        self.vstup(vnutro, self.suma_var, 10).grid(
            row=2, column=1, padx=(0, 10), ipady=6)

        self.kategoria_var = tk.StringVar(value=KATEGORIE[0])
        ttk.Combobox(vnutro, textvariable=self.kategoria_var, values=KATEGORIE,
                     state="readonly", width=11, font=PISMO).grid(
            row=2, column=2, padx=(0, 14))

        self.tlacidlo(vnutro, "+ Pridať", self.pridaj, ZELENA,
                      ZELENA_HOVER).grid(row=2, column=3)

    def vytvor_filter(self, rodic):
        panel = tk.Frame(rodic, bg=POZADIE)
        panel.pack(fill="x", pady=(14, 8))

        tk.Label(panel, text="Zobraziť:", bg=POZADIE, fg=TEXT,
                 font=("Segoe UI", 10, "bold")).pack(side="left")
        self.filter_var = tk.StringVar(value="Všetky")
        filter_box = ttk.Combobox(panel, textvariable=self.filter_var,
                                  values=["Všetky"] + KATEGORIE,
                                  state="readonly", width=12, font=PISMO)
        filter_box.pack(side="left", padx=8)
        filter_box.bind("<<ComboboxSelected>>", lambda e: self.obnov_tabulku())

        # Legenda farieb kategorii (zprava)
        for kat in reversed(KATEGORIE):
            tk.Label(panel, text=kat, bg=FARBY_KATEGORII[kat], fg=TEXT,
                     font=("Segoe UI", 8, "bold"), padx=8, pady=2).pack(
                side="right", padx=2)

    def vytvor_tabulku(self, rodic):
        karta = self.karta(rodic)
        karta.pack(fill="both", expand=True)

        stlpce = ("datum", "popis", "kategoria", "suma")
        self.tabulka = ttk.Treeview(karta, columns=stlpce, show="headings",
                                    selectmode="extended")
        self.tabulka.heading("datum", text="Dátum")
        self.tabulka.heading("popis", text="Popis")
        self.tabulka.heading("kategoria", text="Kategória")
        self.tabulka.heading("suma", text="Suma (€)")
        self.tabulka.column("datum", width=110, anchor="center")
        self.tabulka.column("popis", width=300, anchor="w")
        self.tabulka.column("kategoria", width=120, anchor="center")
        self.tabulka.column("suma", width=100, anchor="e")

        # Farba riadku podla kategorie
        for kat, farba in FARBY_KATEGORII.items():
            self.tabulka.tag_configure(kat, background=farba)

        posuvnik = ttk.Scrollbar(karta, orient="vertical",
                                 command=self.tabulka.yview)
        self.tabulka.configure(yscrollcommand=posuvnik.set)
        self.tabulka.pack(side="left", fill="both", expand=True)
        posuvnik.pack(side="right", fill="y")

    def vytvor_spodny_panel(self, rodic):
        panel = tk.Frame(rodic, bg=POZADIE)
        panel.pack(fill="x", pady=(12, 0))

        self.tlacidlo(panel, "Zmazať vybrané", self.zmaz_vybrane, CERVENA,
                      CERVENA_HOVER).pack(side="left", anchor="s")

        sucet_ramec = tk.Frame(panel, bg=ZLTA, padx=18, pady=6)
        sucet_ramec.pack(side="right")
        tk.Label(sucet_ramec, text="SPOLU", bg=ZLTA, fg="#713F12",
                 font=("Segoe UI", 8, "bold")).pack(anchor="e")
        self.sucet_label = tk.Label(sucet_ramec, text="0.00 €", bg=ZLTA,
                                    fg=TEXT, font=("Segoe UI", 18, "bold"))
        self.sucet_label.pack(anchor="e")

        self.pocet_label = tk.Label(panel, text="", bg=POZADIE, fg=TEXT_SEDY,
                                    font=PISMO)
        self.pocet_label.pack(side="right", padx=18, anchor="s", pady=(0, 6))

    # ---------- Logika ----------
    def pridaj(self):
        popis = self.popis_var.get().strip()
        suma_text = self.suma_var.get().strip().replace(",", ".")

        if not popis:
            messagebox.showwarning("Chyba", "Zadaj popis výdavku.")
            return
        try:
            suma = float(suma_text)
            if suma <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Chyba", "Suma musí byť kladné číslo.")
            return

        datum = date.today().strftime("%d.%m.%Y")
        self.vydavky.append((datum, popis, self.kategoria_var.get(), suma))

        self.popis_var.set("")
        self.suma_var.set("")
        self.popis_entry.focus_set()
        self.uloz()
        self.obnov_tabulku()

    def zmaz_vybrane(self):
        vybrane = self.tabulka.selection()
        if not vybrane:
            messagebox.showinfo("Info", "Najprv vyber riadok v tabuľke.")
            return
        if not messagebox.askyesno("Potvrdenie", "Naozaj zmazať vybrané výdavky?"):
            return

        # iid riadku = index v zozname; mazeme od najvyssieho, aby sa indexy nepomiesali
        for iid in sorted((int(i) for i in vybrane), reverse=True):
            del self.vydavky[iid]

        self.uloz()
        self.obnov_tabulku()

    def obnov_tabulku(self):
        self.tabulka.delete(*self.tabulka.get_children())
        filter_kat = self.filter_var.get()
        sucet = 0.0
        pocet = 0

        for index, (datum, popis, kat, suma) in enumerate(self.vydavky):
            if filter_kat == "Všetky" or kat == filter_kat:
                self.tabulka.insert(
                    "", "end", iid=str(index),
                    values=(datum, popis, kat, f"{suma:.2f}"),
                    tags=(kat,),
                )
                sucet += suma
                pocet += 1

        self.sucet_label.config(text=f"{sucet:.2f} €")
        self.pocet_label.config(text=f"Počet záznamov: {pocet}")

    # ---------- Praca so suborom ----------
    def uloz(self):
        try:
            with open(SUBOR, "w", newline="", encoding="utf-8") as f:
                csv.writer(f).writerows(self.vydavky)
        except OSError as chyba:
            messagebox.showerror("Chyba", f"Nepodarilo sa uložiť súbor:\n{chyba}")

    def nacitaj(self):
        if not os.path.exists(SUBOR):
            return
        try:
            with open(SUBOR, newline="", encoding="utf-8") as f:
                for riadok in csv.reader(f):
                    if len(riadok) == 4:
                        self.vydavky.append(
                            (riadok[0], riadok[1], riadok[2], float(riadok[3]))
                        )
        except (OSError, ValueError) as chyba:
            messagebox.showerror("Chyba", f"Nepodarilo sa načítať súbor:\n{chyba}")

    def pri_zatvoreni(self):
        self.uloz()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    TrackerVydavkov(root)
    root.mainloop()