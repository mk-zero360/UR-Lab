# 🎭 Synthetische User Research Demo

Eine interaktive Streamlit-Anwendung für Workshop-Demonstrationen zu synthetischer User Research mit KI-generierten Personas.

## ✨ Features

- **📝 Persona-Konfiguration**: Detaillierte Erstellung von User Personas mit Demografie, Rolle und Pain Points
- **🚀 Produkt-Definition**: Eingabe von Produktbeschreibung und Value Proposition
- **💬 KI-Interview Chat**: Interaktive Gespräche mit der konfigurierten Persona
- **📊 Live-Insights**: Automatische Extraktion und Anzeige von Insights aus dem Gespräch
- **📈 Visualisierungen**: Metriken und Charts zur Gesprächsanalyse
- **💾 Export-Funktion**: Download der Interview-Daten als JSON

## 🚀 Installation & Setup

### 1. Repository klonen oder Dateien herunterladen

```bash
# Falls Git verwendet wird
git clone <repository-url>
cd user-research-demo
```

### 2. Virtuelle Umgebung erstellen (empfohlen)

```bash
python -m venv venv

# Aktivieren (macOS/Linux)
source venv/bin/activate

# Aktivieren (Windows)
venv\Scripts\activate
```

### 3. Dependencies installieren

```bash
pip install -r requirements.txt
```

### 4. Anwendung starten

```bash
streamlit run app.py
```

Die Anwendung öffnet sich automatisch im Browser unter `http://localhost:8501`

## 🎯 Nutzung

### 1. Persona konfigurieren
- **Demografie**: Alter, Geschlecht, Beruf, Einkommen, Wohnort
- **Rolle & Erfahrung**: Position im Unternehmen und relevante Erfahrungen
- **Pain Points**: Hauptprobleme und Herausforderungen der Persona

### 2. Produkt definieren
- **Produktbeschreibung**: Was ist das Produkt/Service?
- **Value Proposition**: Welchen Nutzen bietet es?

### 3. Interview führen
- Klicke auf "🎬 Interview starten" um zu beginnen
- Die Persona stellt sich vor basierend auf der Konfiguration
- Stelle Fragen über das Chat-Interface
- Beobachte Live-Insights in der rechten Spalte

### 4. Insights analysieren
- **Automatische Extraktion**: Pain Points, Bedürfnisse und positives Feedback
- **Live-Metriken**: Anzahl Nachrichten und erkannte Insights
- **Visualisierungen**: Gesprächsverteilung und Progress-Charts

### 5. Daten exportieren
- Download der kompletten Interview-Session als JSON
- Enthält Persona-Konfiguration, Chat-Historie und Insights

## 🛠 Technische Details

### Architektur
- **Frontend**: Streamlit mit Custom CSS
- **State Management**: `st.session_state` für Chat-Historie und Konfiguration
- **Visualisierungen**: Plotly für interaktive Charts
- **Styling**: Custom CSS für moderne, ansprechende UI

### Mock-Implementierung
Die aktuelle Version verwendet Mock-Responses für die KI-Persona. Für produktive Nutzung:

1. OpenAI API Key in `.env` Datei hinzufügen:
```
OPENAI_API_KEY=your_api_key_here
```

2. Mock-Funktion `chat_with_persona()` durch echte OpenAI-Integration ersetzen

### Insight-Extraktion
Automatische Erkennung von:
- **Pain Points**: Probleme, Frustrationen
- **Bedürfnisse**: Was die Persona braucht/wünscht
- **Positives Feedback**: Zustimmung und Interesse

## 🎨 UI-Features

- **Responsive Design**: Optimiert für verschiedene Bildschirmgrößen
- **Color-Coded Messages**: Unterschiedliche Farben für Interviewer und Persona
- **Progress Tracking**: Visuelle Darstellung des Interview-Fortschritts
- **Interactive Sidebar**: Einfache Konfiguration während des Interviews

## 🔧 Anpassungen

### Neue Insight-Typen hinzufügen
Erweitere die `extract_insights()` Funktion um neue Kategorien:

```python
# Beispiel für neue Insight-Kategorie
concern_indicators = ['sorge', 'bedenken', 'risiko', 'problem']
if any(indicator in text for indicator in concern_indicators):
    insights.append({
        'type': 'Bedenken',
        'content': message['content'][:200] + '...',
        'timestamp': datetime.now()
    })
```

### Persona-Felder erweitern
Füge neue Konfigurationsoptionen in der Sidebar hinzu und erweitere den `create_persona_prompt()`.

### Styling anpassen
Modifiziere das Custom CSS im `st.markdown()` Block für eigene Design-Anpassungen.

## 📋 Workshop-Szenarien

### Beispiel-Personas
1. **Marketing Manager**: Sucht nach Automatisierungstools
2. **HR-Spezialist**: Benötigt bessere Recruiting-Software
3. **Startup-Gründer**: Braucht kostengünstige All-in-One-Lösung

### Demo-Flows
1. **Problem Discovery**: Finde heraus, was die Persona wirklich stört
2. **Solution Fit**: Teste, ob das Produkt die Probleme löst
3. **Pricing Sensitivity**: Erkunde Zahlungsbereitschaft
4. **Feature Prioritization**: Welche Features sind am wichtigsten?

## 🤝 Beitragen

Verbesserungen und Erweiterungen sind willkommen! Besonders interessant:
- Integration echter KI-APIs (OpenAI, Anthropic, etc.)
- Erweiterte Insight-Algorithmen
- Neue Visualisierungen
- Export-Formate (PDF, Excel)
- Multi-Language Support

## 📄 Lizenz

Dieses Projekt ist für Workshop- und Demonstrationszwecke erstellt. Fühle dich frei, es für deine eigenen User Research Aktivitäten zu verwenden und anzupassen.

---

**Viel Spaß beim Erkunden der synthetischen User Research! 🎭✨**
