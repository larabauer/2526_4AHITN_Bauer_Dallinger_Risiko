# 🌍 Risiko – Python Edition

Risiko Spiel als Destopanwendung mit Pygame :)
Von Lara Bauer und Sebastian Dallinger
---

## ✨ Features

- Klassisches Risiko-Spielprinzip mit allen 42 Territorien
- Unterstützung für zwei bis fünf Spieler 
- Mehrspielerprinzip an einem einzigen Rechner
- Terretirien werden automatisch zugewiesen
- Truppen werden automatisiert berechnet, auch Kontinentenbonus wird hinzugefügt
- Spieler können bei ihrem Zug Truppen platzieren & andere Terriitorien angreifen
- Beim Angriff sieht man die gewürfelten Zahlen von sich und dem Gegner, das Kampfergebnis wird automatisch ausgerechnet
- Am Ende des Zuges kann der Spieler seine Truppen noch verschieben

---

## 🚀 Installation

# Repository klonen
git clone https://github.com/larabauer/2526_4AHITN_Bauer_Dallinger_Risiko.git
cd 2526_4AHITN_Bauer_Dallinger_Risiko

# Virtuelle Umgebung erstellen (empfohlen)
python -m venv .venv
source .venv/bin/activate        # Linux/macOS
.venv\Scripts\activate           # Windows

---

## 🎮 Verwendung

# Spiel starten
python main.py

---

## 📁 Projektstruktur

2526_4AHITN_Bauer_Dallinger_Risiko/
├── src
│   ├── resources.py
|   |   ├── continents.json
|   ├── combat.py
|   ├── initializer.py
│   ├── main.py
│   ├── map_data.py
│   ├── map_loader.py
│   ├── player.py
│   ├── player_select.py
│   ├── territory.py
│   ├── risk_map.svg
│   ├── turn_manager.py

---

## 📖 Spielregeln (Kurzübersicht)

Das Spiel läuft in drei Phasen ab:

1. **Verstärkung** – Zu Beginn jeder Runde erhält der Spieler neue Truppen basierend auf gehaltenen Territorien und Kontinenten.
2. **Angriff** – Der Angreifer würfelt mit bis zu 3 Würfeln, der Verteidiger auch mit bis zu 3. Das höchste Paar entscheidet jeweils über einen Truppenverlust.
3. **Bewegung** – Zum Abschluss dürfen Truppen zwischen eigenen verbundenen Territorien verschoben werden.

--- 

# Einblicke ins Spiel

Anzahl der Spieler auswählen:
<img width="406" height="338" alt="image" src="https://github.com/user-attachments/assets/628dab5c-e675-4fd4-952f-da307948e56c" />

Erster Spieler ist an der Reihe, er soll seine Truppen setzen
<img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/8412b176-775e-4be7-95b5-5fe1b2114b88" />

Der Spieler setzt seine Truppen, auf eines seiner Territorien
<img width="445" height="389" alt="image" src="https://github.com/user-attachments/assets/d368a092-5505-4705-bda9-f827e1d4dfb2" />

Die Angriffsphase startet nun
<img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/a13008ce-0305-443c-85d9-891ac44c9784" />

Der Spieler wählt eines seiner Territorien zum Angriff aus
<img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/9a242e99-d6d0-41ef-822f-11b796413a21" />

Der Spieler sieht sein ausgewähltes Territorium und solche, die er angreifen könnte
<img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/3b048d62-0333-4390-a9c5-05f49a979d15" />

Der Spieler kann sich nun aussuchen, mit vielen Würfeln er angreifen möchte
<img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/a893a397-5305-4a16-ad1f-a110ca77a2c8" />

Verliert der Spieler kann er aufhören oder weiterspielen
<img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/db3ff653-e09b-4fe7-a9e2-11c1d2663f88" />

Ist der Kampf gewonnen, so sieht der Spieler folgende Nachricht
<img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/fc58af6d-20ab-4cd1-b84b-4cc18a49ceee" />

Danach kann der Spieler noch seine Truppen bewegen
<img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/d41b97d9-a8f0-4aac-bf60-d82c99ef1a44" />

Der nächste Spieler ist nun an der Reihe.
<img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/537c3712-3603-42e8-b820-ccfd41cda4c9" />
