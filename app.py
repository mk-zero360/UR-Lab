import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os
import json
import re
import random
from typing import Dict, List, Optional
import io
import base64

# Audio components
try:
    from audio_recorder_streamlit import audio_recorder
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False
    st.warning("⚠️ Audio-Recorder nicht verfügbar. Installiere: pip install audio-recorder-streamlit")

# Import OpenAI and load environment variables
import openai
from dotenv import load_dotenv
load_dotenv()

# Set up OpenAI - Fixed version
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_AVAILABLE = bool(OPENAI_API_KEY)

# Page config
st.set_page_config(
    page_title="zero360 User Research Lab",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for zero360 brand colors - Stripe-inspired design
st.markdown("""
<style>
    /* zero360 Brand Colors - Official Palette */
    :root {
        /* zeroBlau Colors - Official Brand Blues */
        --zero360-blau-1: #02063f;  /* zeroBlau 1 - Dark Navy */
        --zero360-blau-2: #576fb4;  /* zeroBlau 2 - Medium Blue */
        --zero360-blau-3: #84a5ff;  /* zeroBlau 3 - Light Blue */
        --zero360-gelb: #fff700;    /* zeroGelb - Bright Yellow */
        
        /* Stripe-inspired color system */
        --primary: var(--zero360-blau-1);
        --primary-light: var(--zero360-blau-2);
        --primary-lighter: var(--zero360-blau-3);
        --accent: var(--zero360-gelb);
        
        /* Neutral grays - Stripe style */
        --gray-50: #fafafa;
        --gray-100: #f5f5f5;
        --gray-200: #e5e5e5;
        --gray-300: #d4d4d4;
        --gray-400: #a3a3a3;
        --gray-500: #737373;
        --gray-600: #525252;
        --gray-700: #404040;
        --gray-800: #262626;
        --gray-900: #171717;
        
        /* Semantic colors */
        --success: #10b981;
        --warning: #f59e0b;
        --error: #ef4444;
        --info: var(--primary-lighter);
        
        /* Spacing system */
        --space-1: 0.25rem;
        --space-2: 0.5rem;
        --space-3: 0.75rem;
        --space-4: 1rem;
        --space-6: 1.5rem;
        --space-8: 2rem;
        --space-12: 3rem;
        --space-16: 4rem;
        
        /* Border radius */
        --radius-sm: 0.375rem;
        --radius: 0.5rem;
        --radius-md: 0.75rem;
        --radius-lg: 1rem;
        --radius-xl: 1.5rem;
        
        /* Shadows */
        --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
        --shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1);
        --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
        --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);
        --shadow-xl: 0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1);
        
        /* Typography */
        --font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        --font-mono: ui-monospace, SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", Menlo, monospace;
        
        /* Legacy aliases for compatibility */
        --zero360-blue: var(--primary);
        --zero360-light-blue: var(--primary-lighter);
        --zero360-silver: var(--gray-300);
        --zero360-dark-grey: var(--gray-800);
        --zero360-light-grey: var(--gray-100);
        --zero360-accent: var(--primary-lighter);
    }
    
    /* Global styles - Stripe inspired */
    * {
        font-family: var(--font-family);
    }
    
    body {
        background-color: var(--gray-50);
        color: var(--gray-900);
        line-height: 1.6;
    }
    
    /* Main header - Clean and minimal */
    .main-header {
        background: linear-gradient(135deg, var(--primary) 0%, var(--primary-light) 100%);
        color: white;
        padding: var(--space-16) var(--space-8);
        margin: calc(-1 * var(--space-4)) calc(-1 * var(--space-4)) var(--space-12) calc(-1 * var(--space-4));
        border-radius: 0;
        box-shadow: var(--shadow-lg);
        position: relative;
        overflow: hidden;
    }
    
    .main-header::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0) 100%);
        pointer-events: none;
    }
    
    .main-header h1 {
        font-size: 3rem;
        font-weight: 700;
        margin: 0 0 var(--space-4) 0;
        letter-spacing: -0.025em;
        position: relative;
        z-index: 1;
    }
    
    .main-header p {
        font-size: 1.25rem;
        font-weight: 400;
        margin: 0;
        opacity: 0.9;
        position: relative;
        z-index: 1;
    }
    
    /* Cards - Clean and modern */
    .persona-preview {
        background: white;
        padding: var(--space-8);
        border-radius: var(--radius-lg);
        border: 1px solid var(--gray-200);
        margin: var(--space-6) 0;
        box-shadow: var(--shadow);
        transition: all 0.2s ease;
    }
    
    .persona-preview:hover {
        box-shadow: var(--shadow-md);
        transform: translateY(-1px);
    }
    
    .example-persona {
        background: white;
        padding: var(--space-6);
        border-radius: var(--radius);
        border: 1px solid var(--gray-200);
        border-left: 4px solid var(--primary);
        margin: var(--space-3) 0;
        cursor: pointer;
        transition: all 0.2s ease;
        box-shadow: var(--shadow-sm);
    }
    
    .example-persona:hover {
        transform: translateY(-1px);
        box-shadow: var(--shadow-md);
        border-left-color: var(--primary-light);
        border-color: var(--gray-300);
    }
    
    /* Chat styling - Clean and minimal */
    .chat-container {
        background: white;
        border-radius: var(--radius-lg);
        padding: var(--space-6);
        margin: var(--space-6) 0;
        max-height: 500px;
        overflow-y: auto;
        border: 1px solid var(--gray-200);
        box-shadow: var(--shadow);
    }
    
    .chat-message {
        padding: var(--space-4);
        margin: var(--space-3) 0;
        border-radius: var(--radius);
        animation: fadeIn 0.2s ease-in;
    }
    
    .user-message {
        background: var(--gray-50);
        border: 1px solid var(--gray-200);
        margin-left: var(--space-12);
        color: var(--gray-900);
    }
    
    .ai-message {
        background: var(--primary);
        color: white;
        margin-right: var(--space-12);
    }
    
    /* Metrics cards - Clean design */
    .metric-card {
        background: white;
        padding: var(--space-6);
        border-radius: var(--radius);
        border: 1px solid var(--gray-200);
        margin: var(--space-3) 0;
        box-shadow: var(--shadow-sm);
        color: var(--gray-900);
        transition: all 0.2s ease;
    }
    
    .metric-card:hover {
        box-shadow: var(--shadow);
        transform: translateY(-1px);
    }
    
    .sentiment-positive {
        border-left: 4px solid var(--success);
        background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
    }
    
    .sentiment-neutral {
        border-left: 4px solid var(--info);
        background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
    }
    
    .sentiment-negative {
        border-left: 4px solid var(--error);
        background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
    }
    
    /* Animations */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    /* Tab styling - Clean and modern */
    .stTabs [data-baseweb="tab-list"] {
        gap: var(--space-2);
        background: var(--gray-100);
        padding: var(--space-2);
        border-radius: var(--radius);
        border: 1px solid var(--gray-200);
    }
    
    .stTabs [data-baseweb="tab"] {
        padding: var(--space-3) var(--space-6);
        border-radius: var(--radius-sm);
        color: var(--gray-700);
        background: transparent;
        border: none;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: white;
        color: var(--gray-900);
    }
    
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background: white;
        color: var(--primary);
        box-shadow: var(--shadow-sm);
    }
    
    /* Buttons - Stripe style */
    .stButton > button {
        background: var(--primary);
        color: white;
        border: none;
        border-radius: var(--radius);
        padding: var(--space-3) var(--space-6);
        font-weight: 500;
        font-size: 0.875rem;
        transition: all 0.2s ease;
        box-shadow: var(--shadow-sm);
    }
    
    .stButton > button:hover {
        background: var(--primary-light);
        transform: translateY(-1px);
        box-shadow: var(--shadow-md);
    }
    
    .stButton > button:active {
        transform: translateY(0);
        box-shadow: var(--shadow-sm);
    }
    
    /* Compact button styling for template selection */
    .stButton > button[title] {
        padding: var(--space-2) var(--space-4);
        font-size: 0.8rem;
        min-height: 2.5rem;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    
    /* Compact persona template buttons */
    .persona-template-button {
        background: white;
        border: 1px solid var(--gray-200);
        border-radius: var(--radius);
        padding: var(--space-3) var(--space-4);
        margin: var(--space-2) 0;
        transition: all 0.2s ease;
        cursor: pointer;
        text-align: center;
        font-size: 0.875rem;
        font-weight: 500;
        color: var(--gray-900);
        box-shadow: var(--shadow-sm);
        min-height: 2.5rem;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    .persona-template-button:hover {
        background: var(--gray-50);
        border-color: var(--primary);
        transform: translateY(-1px);
        box-shadow: var(--shadow);
    }
    
    /* Success/Info messages - Clean design */
    .stSuccess {
        background-color: #f0fdf4;
        border: 1px solid #bbf7d0;
        border-left: 4px solid var(--success);
        color: var(--gray-900);
        border-radius: var(--radius);
    }
    
    .stInfo {
        background-color: #f0f9ff;
        border: 1px solid #bae6fd;
        border-left: 4px solid var(--info);
        color: var(--gray-900);
        border-radius: var(--radius);
    }
    
    .stWarning {
        background-color: #fffbeb;
        border: 1px solid #fed7aa;
        border-left: 4px solid var(--warning);
        color: var(--gray-900);
        border-radius: var(--radius);
    }
    
    /* Streamlit metrics - Clean design */
    [data-testid="metric-container"] {
        background: white;
        border: 1px solid var(--gray-200);
        border-radius: var(--radius);
        padding: var(--space-6);
        box-shadow: var(--shadow-sm);
        transition: all 0.2s ease;
    }
    
    [data-testid="metric-container"]:hover {
        box-shadow: var(--shadow);
    }
    
    [data-testid="metric-container"] > div {
        color: var(--gray-900);
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background-color: var(--gray-50);
    }
    
    /* Voice recorder button styling */
    .audio-recorder {
        background: var(--primary) !important;
        border-radius: 50% !important;
        box-shadow: var(--shadow-sm) !important;
    }
    
    /* Toggle switches */
    .stToggle > div {
        background-color: var(--gray-300);
        border-radius: var(--radius);
    }
    
    .stToggle > div[data-checked="true"] {
        background-color: var(--primary);
    }
    
    /* Question suggestion buttons - Clean design */
    .question-button {
        background: white;
        border: 1px solid var(--gray-200);
        border-radius: var(--radius);
        padding: var(--space-4);
        margin: var(--space-2) 0;
        transition: all 0.2s ease;
        cursor: pointer;
        text-align: left;
        font-size: 0.875rem;
        color: var(--gray-900);
        box-shadow: var(--shadow-sm);
    }
    
    .question-button:hover {
        background: var(--gray-50);
        border-color: var(--primary);
        transform: translateY(-1px);
        box-shadow: var(--shadow);
    }
    
    /* Additional modern styling */
    .stSelectbox > div > div {
        background-color: white;
        border: 1px solid var(--gray-200);
        border-radius: var(--radius);
        box-shadow: var(--shadow-sm);
    }
    
    .stTextInput > div > div > input {
        border: 1px solid var(--gray-200);
        border-radius: var(--radius);
        box-shadow: var(--shadow-sm);
    }
    
    .stTextArea > div > div > textarea {
        border: 1px solid var(--gray-200);
        border-radius: var(--radius);
        box-shadow: var(--shadow-sm);
    }
    
    /* Clean scrollbars */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--gray-100);
        border-radius: var(--radius);
    }
    
    ::-webkit-scrollbar-thumb {
        background: var(--gray-300);
        border-radius: var(--radius);
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: var(--gray-400);
    }
</style>
""", unsafe_allow_html=True)

# Example personas data
EXAMPLE_PERSONAS = {
    "🏰 Luxus-Bauherr": {
        "name": "Dr. Thomas Richter",
        "age": 52,
        "job": "Geschäftsführender Gesellschafter",
        "company": "Richter & Partner Strategic Consulting (120 Mitarbeiter)",
        "experience": "Thomas hat bereits zwei Immobilienprojekte realisiert und baut gerade seine dritte Villa am Starnberger See. Er kennt sich bestens mit Premium-Marken aus und hat ein feines Gespür für Qualität entwickelt. Seine bisherigen Bauprojekte haben ihm gezeigt, dass sich Investitionen in hochwertige Sanitärausstattung langfristig auszahlen.",
        "pain_points": "Die größte Herausforderung ist die Balance zwischen zeitlosem Design und innovativer Technologie. Er möchte keine Kompromisse bei der Qualität eingehen, aber gleichzeitig sicherstellen, dass die Technik auch in zehn Jahren noch zeitgemäß ist. Die Koordination zwischen verschiedenen Gewerken und die Einhaltung des straffen Zeitplans bereiten ihm Sorgen. Außerdem frustriert ihn, dass viele Hersteller keine wirklich exklusiven Lösungen anbieten.",
        "goals": "Thomas strebt nach einem Badezimmer, das als private Wellness-Oase funktioniert und gleichzeitig beeindruckende Technologie nahtlos integriert. Er möchte Produkte, die eine Geschichte erzählen und handwerkliche Perfektion verkörpern. Nachhaltigkeit ist ihm wichtig, aber sie muss sich mit Luxus vereinbaren lassen.",
        "personality": "Perfektionist mit hohen Ansprüchen an sich und seine Umgebung. Er schätzt deutsche Ingenieurskunst und ist bereit, für außergewöhnliche Qualität zu zahlen. Marken sind für ihn wichtig, aber nur wenn sie authentisch sind und echte Innovation bieten."
    },
    "👩‍ Architektin": {
        "name": "Julia Schneider",
        "age": 38,
        "job": "Senior Architektin und Projektleiterin",
        "company": "Architekturbüro Herzog & Kollegen (35 Mitarbeiter)",
        "experience": "Julia hat sich in den letzten zwölf Jahren auf hochwertige Wohnbauprojekte und Hotelsanierungen spezialisiert. Sie kennt das zero360-Sortiment im Detail und hat bereits über 40 Projekte mit deren Produkten realisiert. Ihre Expertise liegt in der Verbindung von Funktionalität und Ästhetik.",
        "pain_points": "Julia kämpft oft mit den unterschiedlichen Anforderungen von Bauherren, Budgetvorgaben und technischen Möglichkeiten. Die Verfügbarkeit von detaillierten CAD-Daten und BIM-Modellen ist nicht immer gegeben, was ihre Planungsarbeit erschwert. Sie benötigt verlässliche Lieferzeiten und ärgert sich über kurzfristige Produktabkündigungen.",
        "goals": "Julia möchte ihren Kunden Badlösungen präsentieren, die sowohl heute als auch in zwanzig Jahren noch überzeugen. Sie strebt danach, als Expertin für innovative Badgestaltung wahrgenommen zu werden und sucht nach Produkten, die ihre Entwürfe unterstützen.",
        "personality": "Detailorientiert und systematisch in ihrer Arbeitsweise. Sie schätzt klare Kommunikation und professionelle Zusammenarbeit. Innovation fasziniert sie, aber sie bleibt pragmatisch und denkt immer an die Umsetzbarkeit."
    },
    "🔧 Installateur-Meister": {
        "name": "Michael Wagner",
        "age": 46,
        "job": "Inhaber und Installateur-Meister",
        "company": "Wagner Haustechnik GmbH (12 Mitarbeiter)",
        "experience": "Michael führt seit fünfzehn Jahren seinen eigenen Betrieb und hat sich einen exzellenten Ruf in der Region erarbeitet. Er installiert zero360-Produkte seit seiner Gesellenzeit und kennt die technischen Besonderheiten genau. Sein Betrieb ist auf Komplettsanierungen und gehobene Neubauten spezialisiert.",
        "pain_points": "Die größte Herausforderung ist der Fachkräftemangel und die damit verbundene Arbeitsbelastung. Er ärgert sich über komplizierte Montageanleitungen und Produkte, die unnötig viel Zeit bei der Installation benötigen. Reklamationen wegen Produktfehlern kosten ihn Zeit und schädigen seinen Ruf.",
        "goals": "Michael möchte seinen Kunden zuverlässige Qualität bieten und dabei effizient arbeiten. Er sucht nach Produkten, die sich schnell und fehlerfrei installieren lassen und lange halten. Wichtig ist ihm eine gute Marge und die Möglichkeit, sich durch Fachwissen und Qualitätsprodukte von der Konkurrenz abzuheben.",
        "personality": "Bodenständig und gradlinig. Er sagt, was er denkt, und schätzt ehrliche Kommunikation. Qualität und Zuverlässigkeit sind seine obersten Prinzipien. Er ist stolz auf sein Handwerk und sein Fachwissen."
    },
    "👩‍💼 Modernisiererin": {
        "name": "Anna Bergmann",
        "age": 42,
        "job": "Marketing Managerin",
        "company": "Mittelständisches Maschinenbauunternehmen (300 Mitarbeiter)",
        "experience": "Anna hat vor drei Jahren ein Haus aus den 1970er Jahren gekauft und modernisiert es schrittweise. Das Badezimmer steht als nächstes großes Projekt an. Sie hat bereits Küche und Wohnbereich renoviert und dabei ein Gespür für Qualitätsunterschiede entwickelt.",
        "pain_points": "Anna fühlt sich von der Produktvielfalt überfordert und unsicher, welche technischen Features wirklich sinnvoll sind. Das Budget ist begrenzt, aber sie möchte keine billigen Kompromisse eingehen, die sie später bereut. Die Koordination der verschiedenen Handwerker stresst sie.",
        "goals": "Anna möchte ein modernes, pflegeleichtes Badezimmer, das den Wert ihrer Immobilie steigert. Sie sucht nach einem optimalen Preis-Leistungs-Verhältnis und Produkten, die lange halten. Das neue Bad soll den Alltag ihrer vierköpfigen Familie erleichtern.",
        "personality": "Strukturiert und recherchiert gründlich, bevor sie Entscheidungen trifft. Sie lässt sich von Trends inspirieren, bleibt aber pragmatisch. Qualität ist ihr wichtig, aber sie achtet auf ein vernünftiges Preis-Leistungs-Verhältnis."
    },
    "👴 Rentner": {
        "name": "Werner Hoffmann",
        "age": 68,
        "job": "Pensionierter Gymnasiallehrer",
        "company": "Im Ruhestand, ehrenamtlich aktiv im Seniorenbeirat",
        "experience": "Werner lebt seit vierzig Jahren im selben Einfamilienhaus. Nach einem Sturz seiner Frau vor zwei Jahren haben sie begonnen, das Haus altersgerecht umzubauen. Das Badezimmer im Erdgeschoss wurde bereits angepasst, nun steht das obere Bad zur Renovierung an.",
        "pain_points": "Die größte Sorge bereitet Werner die Zukunftssicherheit der Investition - das Bad soll sie durch die nächsten zwanzig Jahre tragen. Die Bedienung moderner Armaturen überfordert teilweise seine Frau, die beginnende Arthrose in den Händen hat. Er ärgert sich über Produkte, die stigmatisierend nach Krankenhaus aussehen.",
        "goals": "Werner möchte ein Badezimmer, das Sicherheit bietet, ohne wie ein Pflegebad auszusehen. Er sucht nach Lösungen, die sich intuitiv bedienen lassen und auch mit nachlassender Kraft und Beweglichkeit funktionieren. Wichtig ist ihm, dass er und seine Frau möglichst lange selbstständig leben können.",
        "personality": "Analytischer Mensch, der Entscheidungen gründlich durchdenkt. Durch seine naturwissenschaftliche Prägung interessiert er sich für technische Details und hinterfragt Werbeversprechen kritisch. Qualität und Langlebigkeit sind ihm wichtiger als Trends."
    },
    "👨‍👩‍👧‍👦 Familienpaar": {
        "name": "Sandra & Marco Keller",
        "age": 37,
        "job": "Teilzeit-Controllerin & Vertriebsleiter",
        "company": "Energieversorgung & Medizintechnik",
        "experience": "Das Paar hat vor fünf Jahren ein Reihenhaus gekauft und renoviert es scheibchenweise. Mit drei Kindern (4, 8 und 11 Jahre) ist das Badezimmer der neuralgische Punkt jeden Morgens. Sie haben bereits ein Gäste-WC eingebaut, aber das Hauptbadezimmer platzt aus allen Nähten.",
        "pain_points": "Der Morgenstress ist ihr größtes Problem - alle wollen gleichzeitig ins Bad, und es gibt ständig Streit. Die Unordnung durch fünf Personen macht Sandra wahnsinnig, es fehlt an cleveren Stauraumlösungen. Die Kinder verschwenden Wasser und beschädigen ständig etwas.",
        "goals": "Sandra und Marco träumen von einem Familienbad, das den Alltag entschärft statt verkompliziert. Sie brauchen robuste Produkte, die den täglichen Härtetest mit drei Kindern überstehen. Wichtig sind ihnen zwei Waschplätze, um den Morgenstau zu reduzieren.",
        "personality": "Sandra ist die Organisatorin, die praktische Lösungen über Design stellt. Marco ist der Zahlenmensch, der jede Ausgabe hinterfragt. Beide sind gestresst aber liebevoll, wollen das Beste für ihre Familie."
    },
    "💻 Berufseinsteiger": {
        "name": "Lukas Bauer",
        "age": 26,
        "job": "Junior Software Developer",
        "company": "Tech-Startup mit 45 Mitarbeitern (Fintech-Bereich)",
        "experience": "Lukas ist vor sechs Monaten in seine erste eigene Wohnung gezogen - eine 55qm Altbauwohnung in einem hippen Stadtviertel. Das Badezimmer ist klein aber hat Potenzial. Er informiert sich hauptsächlich online, schaut YouTube-Tutorials und liest Bewertungen.",
        "pain_points": "Das größte Problem ist das begrenzte Budget - mit dem Einstiegsgehalt muss er jeden Euro zweimal umdrehen. Die kleine Badezimmergröße macht es schwierig, clevere Lösungen zu finden. Er ist unsicher, welche Investitionen sich lohnen, da er nicht weiß, wie lange er in der Wohnung bleibt.",
        "goals": "Lukas möchte sein kleines Bad in eine moderne, funktionale Nasszelle verwandeln, die seinen Lifestyle widerspiegelt. Er sucht nach platzsparenden Lösungen, die das Bad größer wirken lassen. Das Bad soll instagrammable sein - er ist stolz auf seine erste eigene Wohnung.",
        "personality": "Digital-affin und recherchiert alles online. Er ist experimentierfreudig und offen für neue Marken, die gutes Design zu fairen Preisen bieten. DIY-Projekte reizen ihn, Social Media beeinflusst seinen Geschmack."
    }
}

# Demo responses for different personas
DEMO_RESPONSES = {
    "Luxus-Bauherr": [
        "Das klingt interessant, aber entspricht das wirklich dem Premium-Standard, den ich für meine Villa erwarte?",
        "Wie unterscheidet sich das von dem, was jeder haben kann? Ich suche nach wirklich exklusiven Lösungen.",
        "Die Technologie ist beeindruckend, aber wird sie auch in zehn Jahren noch zeitgemäß sein?",
        "Können Sie mir Referenzen von vergleichbaren Projekten zeigen? Ich kenne die meisten Premium-Anbieter.",
        "Das Design gefällt mir, aber wie sieht es mit der handwerklichen Perfektion aus? Ich dulde keine Kompromisse bei der Qualität."
    ],
    "Architektin": [
        "Interessant! Haben Sie auch detaillierte CAD-Daten und BIM-Modelle für meine Planungsarbeit?",
        "Wie sind die Lieferzeiten? Meine Projekte haben straffe Zeitpläne und ich brauche Verlässlichkeit.",
        "Das Produkt sieht gut aus, aber wie integriert es sich in mein Gesamtkonzept? Funktionalität ist entscheidend.",
        "Gibt es technische Beratung für komplexe Installationen? Ich arbeite oft an anspruchsvollen Projekten.",
        "Welche Zertifizierungen hat das Produkt? Nachhaltigkeit wird bei meinen Kunden immer wichtiger."
    ],
    "Installateur": [
        "Das sieht gut aus, aber wie kompliziert ist die Installation? Zeit ist Geld in meinem Geschäft.",
        "Wie sieht es mit der Verfügbarkeit von Ersatzteilen aus? Ich kann mir keine langen Wartezeiten bei Reparaturen leisten.",
        "Was ist die Marge für mich als Fachbetrieb? Ich muss auch von meiner Arbeit leben können.",
        "Gibt es Schulungen für meine Mitarbeiter? Neue Technik muss richtig installiert werden.",
        "Wie oft gibt es Reklamationen? Mein Ruf hängt davon ab, dass alles funktioniert."
    ],
    "Modernisiererin": [
        "Das gefällt mir! Aber wie viel kostet das ungefähr? Unser Budget ist leider begrenzt.",
        "Passt das zu unseren bestehenden Installationen? Wir können nicht alles neu machen.",
        "Ist das wirklich pflegeleicht? Mit vier Personen im Haushalt muss alles praktisch sein.",
        "Wie lange hält das? Wir wollen nicht in fünf Jahren schon wieder renovieren müssen.",
        "Ist das wassersparend? Die Nebenkosten werden immer höher und wir wollen nachhaltig leben."
    ],
    "Rentner": [
        "Das ist interessant, aber ist das auch einfach zu bedienen? Meine Frau hat Probleme mit komplizierten Armaturen.",
        "Wie sicher ist das? Wir werden nicht jünger und Stürze im Bad sind gefährlich.",
        "Sieht das aus wie ein Krankenhaus? Wir wollen keine Pflege-Atmosphäre in unserem Zuhause.",
        "Ist das eine gute Investition für die nächsten zwanzig Jahre? In unserem Alter überlegt man zweimal.",
        "Gibt es Zuschüsse von der Pflegekasse dafür? Die Bürokratie ist so kompliziert geworden."
    ],
    "Familienpaar": [
        "Das könnte unseren Morgenstress wirklich reduzieren! Aber ist das auch robust genug für drei Kinder?",
        "Wie teuer wird das insgesamt? Mit drei Kindern müssen wir jeden Euro zweimal umdrehen.",
        "Ist das wassersparend? Die Kinder lassen gerne mal das Wasser laufen.",
        "Kann man das leicht sauber halten? Bei fünf Personen ist Hygiene ein Dauerthema.",
        "Wächst das mit den Kindern mit? Der Kleine ist erst vier und braucht noch Hilfe."
    ],
    "Berufseinsteiger": [
        "Cool! Aber ehrlich gesagt ist mein Budget ziemlich knapp. Gibt es das auch günstiger?",
        "Passt das in mein kleines Bad? Ich habe nur 55 Quadratmeter insgesamt.",
        "Kann ich das selbst installieren? YouTube-Tutorials schaue ich gerne.",
        "Ist das instagrammable? Meine erste eigene Wohnung soll schon was hermachen.",
        "Kann ich das mitnehmen, wenn ich umziehe? Ich weiß noch nicht, wie lange ich hier bleibe."
    ]
}

# Initialize session state
def initialize_session_state():
    defaults = {
        'chat_history': [],
        'current_persona': {},
        'product_info': {},
        'insights': [],
        'metrics': {
            'sentiment_score': 0.5,
            'conviction_level': 0.5,
            'main_concerns': []
        },
        'demo_mode': False,
        'interview_active': False,
        'voice_mode': False,
        'last_ai_response': '',
        'audio_playing': False
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# AI Response Functions
def get_openai_response(message: str, persona: Dict, product: Dict) -> str:
    """Get response from OpenAI API"""
    if not OPENAI_AVAILABLE:
        st.error("🚨 OpenAI API Key nicht gefunden! Bitte .env Datei mit OPENAI_API_KEY erstellen.")
        return "Entschuldigung, ich kann momentan nicht antworten. Bitte überprüfen Sie die API-Konfiguration."
    
    try:
        prompt = create_persona_prompt(persona, product)
        
        # Use the new OpenAI client format
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": message}
            ],
            max_tokens=400,
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()
    
    except Exception as e:
        st.error(f"🚨 OpenAI API Fehler: {str(e)}")
        return f"Entschuldigung, es gab einen Fehler bei der Verbindung zur API: {str(e)}"

def get_demo_response(persona_type: str) -> str:
    """Get demo response based on persona type"""
    persona_key = next((key for key in DEMO_RESPONSES.keys() if key in persona_type), "Marketing Manager")
    return random.choice(DEMO_RESPONSES[persona_key])

# Voice Functions
def transcribe_audio(audio_bytes) -> str:
    """Transcribe audio using OpenAI Whisper"""
    if not OPENAI_AVAILABLE:
        return "Audio-Transkription nicht verfügbar - OpenAI API Key fehlt."
    
    try:
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        
        # Create a file-like object from audio bytes
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = "audio.wav"
        
        response = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
        )
        
        return response.text.strip()
    
    except Exception as e:
        st.error(f" Whisper Fehler: {str(e)}")
        return f"Transkriptionsfehler: {str(e)}"

def text_to_speech(text: str) -> bytes:
    """Convert text to speech using OpenAI TTS"""
    if not OPENAI_AVAILABLE:
        return None
    
    try:
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        
        response = client.audio.speech.create(
            model="tts-1",
            voice="alloy",  # You can change this to nova, shimmer, etc.
            input=text[:4000]  # TTS has character limits
        )
        
        return response.content
    
    except Exception as e:
        st.error(f"🚨 TTS Fehler: {str(e)}")
        return None

def create_persona_prompt(persona: Dict, product: Dict) -> str:
    """Create detailed persona prompt following best practices"""
    
    # Special handling for couple persona
    if "Sandra & Marco" in persona.get('name', ''):
        return f"""
# ROLE & OBJECTIVE
Sie sind Sandra & Marco Keller, ein Ehepaar mit drei Kindern (4, 8 und 11 Jahre). Ihr Ziel ist es, als potenzielle Kunden authentisch auf Produktvorstellungen zu reagieren und realistische Fragen aus Familiensicht zu stellen.

# PERSONALITY & TONE
- Sprechen Sie als Paar ("wir", "uns", "unser")
- Sandra: Organisiert, pragmatisch, detailorientiert
- Marco: Zahlenorientiert, vorsichtig bei Ausgaben
- Gemeinsam: Familienorientiert, zeitgestresst aber liebevoll

# CONTEXT
## Ihre Situation:
- Alter: Sandra 37, Marco 39 Jahre
- Jobs: {persona.get('job', 'Teilzeit-Controllerin & Vertriebsleiter')}
- Unternehmen: {persona.get('company', 'Energieversorgung & Medizintechnik')}
- Wohnsituation: {persona.get('experience', 'Reihenhaus mit drei Kindern')}

## Aktuelle Herausforderungen:
{persona.get('pain_points', 'Morgenstress im Bad, Budget-Druck, Organisationsaufwand')}

## Ihre Ziele:
{persona.get('goals', 'Familienalltag vereinfachen, robuste Lösungen finden')}

# REFERENCE PRONUNCIATIONS
- zero360: "ZERO-three-six-zero" (englisch)

# CONTEXT: PRODUKT IM GESPRÄCH
{product.get('description', 'Ein zero360 Produkt')}

Value Proposition: {product.get('value_prop', 'Verbesserung des Alltags')}

# INSTRUCTIONS / RULES
## DO:
- Reagieren Sie authentisch als Paar mit drei Kindern
- Stellen Sie praktische Fragen zur Familientauglichkeit
- Erwähnen Sie konkrete Alltagssituationen (Morgenstress, Kinder, Putzen)
- Zeigen Sie Interesse, aber auch berechtigte Budgetsorgen
- Denken Sie an Sicherheit und Robustheit für Kinder
- Antworten Sie auf Deutsch in 1-3 prägnanten Sätzen

## DON'T:
- Sprechen Sie niemals als Einzelperson ("ich")
- Vergessen Sie nicht die drei Kinder in Ihren Überlegungen
- Seien Sie nicht unrealistisch optimistisch - zeigen Sie echte Bedenken
- Ignorieren Sie nicht finanzielle Aspekte

# CONVERSATION FLOW
Sie befinden sich in einem User Research Interview. Reagieren Sie natürlich auf Produktvorstellungen mit einer Mischung aus Interesse und kritischen Nachfragen, wie es echte Eltern tun würden.

# SAFETY & ESCALATION
Bleiben Sie immer in der Rolle des Ehepaars. Falls technische Details zu komplex werden, fragen Sie nach einfacheren Erklärungen.
"""
    else:
        return f"""
# ROLE & OBJECTIVE
Sie sind {persona.get('name', 'eine Person')} und arbeiten als {persona.get('job', 'Fachkraft')}. Ihr Ziel ist es, als potenzielle/r Kunde/in authentisch auf Produktvorstellungen zu reagieren und realistische Fragen aus Ihrer beruflichen und persönlichen Perspektive zu stellen.

# PERSONALITY & TONE
{persona.get('personality', 'Professionell, kritisch, aber aufgeschlossen')}

# CONTEXT
## Ihre Situation:
- Alter: {persona.get('age', 30)} Jahre
- Position: {persona.get('job', 'Fachkraft')}
- Unternehmen: {persona.get('company', 'Ein Unternehmen')}
- Erfahrung: {persona.get('experience', 'Berufserfahrung')}

## Aktuelle Herausforderungen:
{persona.get('pain_points', 'Berufliche und persönliche Herausforderungen')}

## Ihre Ziele:
{persona.get('goals', 'Verbesserungen in Beruf und Alltag')}

# REFERENCE PRONUNCIATIONS
- zero360: "ZERO-three-six-zero" (englisch)

# CONTEXT: PRODUKT IM GESPRÄCH
{product.get('description', 'Ein zero360 Produkt')}

Value Proposition: {product.get('value_prop', 'Nutzen für den Anwender')}

# INSTRUCTIONS / RULES
## DO:
- Reagieren Sie authentisch aus Ihrer spezifischen Perspektive
- Stellen Sie kritische Fragen basierend auf Ihren Pain Points
- Erwähnen Sie konkrete Beispiele aus Ihrem Arbeits-/Lebensalltag
- Zeigen Sie sowohl Interesse als auch berechtigte Skepsis
- Berücksichtigen Sie Ihre spezielle Lebenssituation
- Antworten Sie auf Deutsch in 1-3 prägnanten Sätzen

## DON'T:
- Seien Sie nicht unrealistisch begeistert
- Ignorieren Sie nicht Ihre spezifischen Bedürfnisse und Einschränkungen
- Vergessen Sie nicht Ihre berufliche Expertise
- Seien Sie nicht unhöflich, aber durchaus kritisch

# CONVERSATION FLOW
Sie befinden sich in einem User Research Interview. Reagieren Sie natürlich auf Produktvorstellungen mit einer Mischung aus professionellem Interesse und kritischen Nachfragen.

# SAFETY & ESCALATION
Bleiben Sie immer in Ihrer Rolle. Falls Fragen außerhalb Ihres Expertisebereichs gestellt werden, verweisen Sie höflich auf Ihre spezifische Perspektive.
"""

# Interview Question Suggestions
def generate_adaptive_questions(persona: Dict, product: Dict, chat_history: List[Dict]) -> List[str]:
    """Generate 3 adaptive interview questions based on persona, product and conversation context"""
    
    persona_name = persona.get('name', 'Person')
    product_name = product.get('name', 'Produkt')
    
    # Analyze conversation context
    conversation_topics = []
    last_responses = []
    
    # Get last few AI responses to understand conversation flow
    for message in chat_history[-6:]:  # Last 6 messages (3 pairs)
        if message['role'] == 'assistant':
            last_responses.append(message['content'].lower())
    
    # Extract topics mentioned
    context_keywords = {
        'price': ['preis', 'kosten', 'budget', 'geld', 'teuer', 'günstig', 'investition'],
        'installation': ['installation', 'montage', 'einbau', 'handwerker', 'selbst'],
        'technology': ['technologie', 'digital', 'smart', 'app', 'bedienung'],
        'design': ['design', 'aussehen', 'optik', 'stil', 'farbe'],
        'sustainability': ['nachhaltigkeit', 'umwelt', 'energie', 'wasser', 'sparen'],
        'family': ['familie', 'kinder', 'alltag', 'morgen', 'stress'],
        'quality': ['qualität', 'robust', 'langlebig', 'haltbar', 'zuverlässig'],
        'comparison': ['vergleich', 'konkurrenz', 'alternative', 'unterschied'],
        'concerns': ['bedenken', 'problem', 'schwierig', 'sorge', 'risiko'],
        'benefits': ['vorteil', 'nutzen', 'hilft', 'besser', 'verbessert']
    }
    
    for topic, keywords in context_keywords.items():
        for response in last_responses:
            if any(keyword in response for keyword in keywords):
                conversation_topics.append(topic)
                break
    
    # Generate context-aware questions
    if len(chat_history) <= 2:  # First questions
        return get_initial_questions(persona_name, product_name)
    
    # Adaptive questions based on conversation flow
    questions = []
    
    # If price was discussed, ask about value/ROI
    if 'price' in conversation_topics:
        if "Thomas Richter" in persona_name:
            questions.append(f"Welche Zusatzleistungen würden den Preis für das {product_name} rechtfertigen?")
        elif "Lukas Bauer" in persona_name:
            questions.append(f"Gibt es Finanzierungsmöglichkeiten für das {product_name}?")
        else:
            questions.append(f"Was müsste das {product_name} leisten, um den Preis zu rechtfertigen?")
    
    # If installation was discussed, ask about service/support
    if 'installation' in conversation_topics:
        questions.append(f"Welche Art von Support erwarten Sie nach der Installation?")
    
    # If technology was discussed, ask about future features
    if 'technology' in conversation_topics:
        questions.append(f"Welche zusätzlichen smarten Funktionen wären für Sie interessant?")
    
    # If concerns were raised, ask about solutions
    if 'concerns' in conversation_topics:
        questions.append(f"Was könnte Ihre Bedenken bezüglich {product_name} ausräumen?")
    
    # If benefits were discussed, ask for specifics
    if 'benefits' in conversation_topics:
        questions.append(f"Welcher Vorteil vom {product_name} ist für Sie am wichtigsten?")
    
    # Add persona-specific follow-ups
    persona_questions = get_persona_followup_questions(persona_name, product_name, conversation_topics)
    questions.extend(persona_questions)
    
    # Fill with general follow-ups if needed
    general_followups = [
        f"Wie würden Sie das {product_name} Ihren Freunden beschreiben?",
        f"Was wäre Ihr nächster Schritt bezüglich {product_name}?",
        f"Welche Fragen haben Sie noch zum {product_name}?",
        f"Wie wichtig ist Ihnen die Marke zero360 bei dieser Entscheidung?",
        f"Würden Sie das {product_name} weiterempfehlen?"
    ]
    
    # Add general questions if we don't have enough specific ones
    for q in general_followups:
        if len(questions) < 3:
            questions.append(q)
    
    return questions[:3]  # Return exactly 3 questions

def get_initial_questions(persona_name: str, product_name: str) -> List[str]:
    """Get initial questions for first interaction"""
    
    if "Thomas Richter" in persona_name:  # Luxus-Bauherr
        return [
            f"Entspricht das {product_name} Ihren Premium-Ansprüchen für die Villa?",
            f"Wie wichtig ist Ihnen die Exklusivität gegenüber Standardlösungen?",
            f"Welche Rolle spielt die Zukunftssicherheit der Technologie für Sie?"
        ]
    elif "Julia Schneider" in persona_name:  # Architektin
        return [
            f"Wie würden Sie das {product_name} in Ihre Hotelprojekte integrieren?",
            f"Welche technischen Daten benötigen Sie für die Planungsarbeit?",
            f"Wie bewerten Sie die Nachhaltigkeit für Ihre Zertifizierungen?"
        ]
    elif "Michael Wagner" in persona_name:  # Installateur
        return [
            f"Wie kompliziert ist die Installation vom {product_name}?",
            f"Welche Marge können Sie als Fachbetrieb damit erzielen?",
            f"Wie ist die Verfügbarkeit von Ersatzteilen und Service?"
        ]
    elif "Anna Bergmann" in persona_name:  # Modernisiererin
        return [
            f"Passt das {product_name} zu Ihren bestehenden Installationen?",
            f"Wie rechtfertigen Sie die Investition gegenüber günstigeren Alternativen?",
            f"Welche Auswirkungen hat das auf Ihre laufende Hausrenovierung?"
        ]
    elif "Werner Hoffmann" in persona_name:  # Rentner
        return [
            f"Ist das {product_name} auch für ältere Menschen einfach zu bedienen?",
            f"Wie sicher fühlen Sie sich mit dieser neuen Technologie?",
            f"Rechtfertigt sich die Investition für die nächsten 20 Jahre?"
        ]
    elif "Sandra & Marco" in persona_name:  # Familie
        return [
            f"Wie würde das {product_name} unseren Morgenstress mit drei Kindern reduzieren?",
            f"Ist das robust genug für den täglichen Familienalltag?",
            f"Können wir uns das mit unserem Familienbudget leisten?"
        ]
    elif "Lukas Bauer" in persona_name:  # Berufseinsteiger
        return [
            f"Passt das {product_name} in meine kleine Wohnung und mein Budget?",
            f"Kann ich das selbst installieren oder brauche ich einen Handwerker?",
            f"Ist das auch für junge Leute wie mich relevant?"
        ]
    else:
        return [
            f"Was ist Ihr erster Eindruck vom {product_name}?",
            f"Welche Bedenken hätten Sie bei der Anschaffung?",
            f"Wie würde das Ihren Alltag verändern?"
        ]

def get_persona_followup_questions(persona_name: str, product_name: str, topics: List[str]) -> List[str]:
    """Get persona-specific follow-up questions based on conversation topics"""
    
    questions = []
    
    if "Thomas Richter" in persona_name:  # Luxus-Bauherr
        if 'quality' in topics:
            questions.append(f"Welche Premium-Features sind für Sie unverzichtbar?")
        if 'design' in topics:
            questions.append(f"Wie wichtig ist die Designsprache für Ihre Villa?")
    
    elif "Julia Schneider" in persona_name:  # Architektin
        if 'sustainability' in topics:
            questions.append(f"Welche Zertifizierungen benötigen Sie für Ihre Projekte?")
        if 'technology' in topics:
            questions.append(f"Wie integrieren Sie smarte Lösungen in Ihre Planungen?")
    
    elif "Michael Wagner" in persona_name:  # Installateur
        if 'installation' in topics:
            questions.append(f"Welche Schulungen bräuchten Sie für das {product_name}?")
        if 'price' in topics:
            questions.append(f"Wie kalkulieren Sie solche Premium-Produkte?")
    
    elif "Anna Bergmann" in persona_name:  # Modernisiererin
        if 'comparison' in topics:
            questions.append(f"Mit welchen Produkten vergleichen Sie das {product_name}?")
        if 'quality' in topics:
            questions.append(f"Wie wichtig ist die Langlebigkeit bei Ihrer Renovierung?")
    
    elif "Werner Hoffmann" in persona_name:  # Rentner
        if 'technology' in topics:
            questions.append(f"Benötigen Sie Unterstützung bei der Bedienung?")
        if 'family' in topics:
            questions.append(f"Sollen Ihre Kinder das auch nutzen können?")
    
    elif "Sandra & Marco" in persona_name:  # Familie
        if 'family' in topics:
            questions.append(f"Wie erklären Sie den Kindern die neue Technik?")
        if 'benefits' in topics:
            questions.append(f"Welcher Zeitgewinn wäre für euch am wertvollsten?")
    
    elif "Lukas Bauer" in persona_name:  # Berufseinsteiger
        if 'price' in topics:
            questions.append(f"Würden Sie das auf Raten kaufen?")
        if 'technology' in topics:
            questions.append(f"Welche Apps oder Features nutzen Sie am meisten?")
    
    return questions

# Analytics Functions
def analyze_sentiment(text: str) -> float:
    """Simple sentiment analysis"""
    positive_words = ['gut', 'toll', 'super', 'perfekt', 'interessant', 'hilfreich', 'gefällt', 'liebe']
    negative_words = ['schlecht', 'problem', 'schwierig', 'teuer', 'kompliziert', 'frustrierend']
    
    text_lower = text.lower()
    pos_count = sum(1 for word in positive_words if word in text_lower)
    neg_count = sum(1 for word in negative_words if word in text_lower)
    
    if pos_count + neg_count == 0:
        return 0.5
    
    return pos_count / (pos_count + neg_count)

def extract_concerns(text: str) -> List[str]:
    """Extract main concerns from text"""
    concern_patterns = [
        r'(kosten|preis|budget|teuer)',
        r'(zeit|dauer|schnell|langsam)',
        r'(sicher|risiko|datenschutz)',
        r'(komplex|kompliziert|schwierig)',
        r'(integration|kompatibel)',
        r'(support|hilfe|schulung)'
    ]
    
    concerns = []
    text_lower = text.lower()
    
    for pattern in concern_patterns:
        if re.search(pattern, text_lower):
            if 'kosten' in pattern and re.search(pattern, text_lower):
                concerns.append('💰 Kosten')
            elif 'zeit' in pattern and re.search(pattern, text_lower):
                concerns.append('⏱️ Zeit')
            elif 'sicher' in pattern and re.search(pattern, text_lower):
                concerns.append('🔒 Sicherheit')
            elif 'komplex' in pattern and re.search(pattern, text_lower):
                concerns.append('🧩 Komplexität')
            elif 'integration' in pattern and re.search(pattern, text_lower):
                concerns.append('🔗 Integration')
            elif 'support' in pattern and re.search(pattern, text_lower):
                concerns.append('🆘 Support')
    
    return list(set(concerns))

def calculate_conviction(chat_history: List) -> float:
    """Calculate conviction level based on chat progression"""
    if not chat_history:
        return 0.0
    
    positive_indicators = 0
    total_messages = len([msg for msg in chat_history if msg['role'] == 'assistant'])
    
    for msg in chat_history:
        if msg['role'] == 'assistant':
            sentiment = analyze_sentiment(msg['content'])
            if sentiment > 0.6:
                positive_indicators += 1
    
    return min(positive_indicators / max(total_messages, 1), 1.0)

# UI Components
def render_persona_builder():
    """Render the persona builder interface"""
    st.header("👤 Persona Builder")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("🎯 Quick Select")
        
        # Quick select buttons
        for emoji_name, persona_data in EXAMPLE_PERSONAS.items():
            if st.button(f"{emoji_name}", key=f"quick_{emoji_name}", use_container_width=True):
                st.session_state.current_persona = persona_data.copy()
                st.success(f"✅ {persona_data['name']} ausgewählt!")
                st.rerun()
        
        st.divider()
        
        st.subheader("🛠️ Custom Persona")
        
        # Custom persona form
        name = st.text_input("👤 Name", value=st.session_state.current_persona.get('name', ''))
        age = st.slider("🎂 Alter", 20, 65, st.session_state.current_persona.get('age', 35))
        job = st.text_input("💼 Job Titel", value=st.session_state.current_persona.get('job', ''))
        company = st.text_input("🏢 Unternehmen", value=st.session_state.current_persona.get('company', ''))
        experience = st.text_area("📈 Erfahrung", value=st.session_state.current_persona.get('experience', ''))
        pain_points = st.text_area("😣 Pain Points", value=st.session_state.current_persona.get('pain_points', ''))
        goals = st.text_area("🎯 Ziele", value=st.session_state.current_persona.get('goals', ''))
        personality = st.text_area("🧠 Persönlichkeit", value=st.session_state.current_persona.get('personality', ''))
        
        if st.button("💾 Persona speichern", type="primary"):
            st.session_state.current_persona = {
                'name': name,
                'age': age,
                'job': job,
                'company': company,
                'experience': experience,
                'pain_points': pain_points,
                'goals': goals,
                'personality': personality
            }
            st.success("✅ Persona gespeichert!")
    
    with col2:
        st.subheader("👁️ Live Vorschau")
        
        if st.session_state.current_persona:
            persona = st.session_state.current_persona
            st.markdown(f"""
            <div class="persona-preview">
                <h3>🎭 {persona.get('name', 'Unbekannt')}</h3>
                <p><strong>📋 Position:</strong> {persona.get('job', 'N/A')} bei {persona.get('company', 'N/A')}</p>
                <p><strong>🎂 Alter:</strong> {persona.get('age', 'N/A')} Jahre</p>
                <p><strong>📚 Erfahrung:</strong> {persona.get('experience', 'Keine Angabe')}</p>
                <p><strong>😣 Hauptprobleme:</strong> {persona.get('pain_points', 'Keine Angabe')}</p>
                <p><strong>🎯 Ziele:</strong> {persona.get('goals', 'Keine Angabe')}</p>
                <p><strong>🧠 Persönlichkeit:</strong> {persona.get('personality', 'Keine Angabe')}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("👆 Wähle oder erstelle eine Persona für die Vorschau")

def render_product_config():
    """Render product configuration"""
    st.header("🚀 Produkt Konfiguration")
    
    # Default products data
    DEFAULT_PRODUCTS = {
        "🏠 FlexSpace System": {
            "name": "zero360 FlexSpace System",
            "description": "Modulares Duschsystem mit magnetischer Wandschiene, das sich an verändernde Lebenssituationen anpasst. Komponenten können werkzeuglos angebracht werden - von Handbrausen auf Kinderhöhe bis zu Duschsitzen mit Haltegriffen. Jedes Modul kommuniziert über NFC und passt automatisch Wasserdruck und Temperatur an.",
            "value_prop": "Maximale Flexibilität durch modularen Aufbau. Passt sich an alle Lebensphasen an - von der ersten Wohnung bis zum altersgerechten Bad. Module sind mietbar für maximale Kostenflexibilität.",
            "target_market": "Mieter, junge Familien, Menschen in Veränderungsphasen"
        },
        "🤖 AIR System": {
            "name": "zero360 AIR (Adaptive Intelligent Room)",
            "description": "Intelligentes Badezimmersystem mit dezenten Sensoren in den Armaturen. Erfasst Nutzungsmuster, analysiert Wasserqualität in Echtzeit und optimiert selbstständig. Lernt Familienroutinen und bereitet das Bad optimal vor. Generiert automatisch Wartungsprotokolle.",
            "value_prop": "KI-gesteuerte Optimierung des gesamten Badezimmers. Automatische Anpassung an Nutzergewohnheiten, präventive Wartung und professionelle Datenanalyse für Hotels und Gewerbe.",
            "target_market": "Luxussegment, Hotels, technikaffine Haushalte"
        },
        "🔗 Connect Hub": {
            "name": "zero360 Connect Hub",
            "description": "Zentrale Schaltzentrale, die alle Wasseranwendungen im Haus intelligent vernetzt. Kommuniziert mit Waschmaschine, Geschirrspüler und Sanitärarmaturen. Vermeidet Lastspitzen und optimiert Wasserverbrauch. Perfekte Nachrüstlösung für bestehende Häuser.",
            "value_prop": "Ein Gerät revolutioniert das gesamte Wassermanagement. Intelligente Vernetzung aller Geräte, Lastspitzenmanagement und deutliche Kosteneinsparungen.",
            "target_market": "Hausmodernisierer, Smart Home Enthusiasten"
        },
        "🌱 PureFlow System": {
            "name": "zero360 PureFlow Kreislaufsystem",
            "description": "Revolutionäres Dreifach-System für nachhaltiges Wassermanagement: Grauwasser-Recycling für Toilettenspülung, Wärmerückgewinnung aus Duschwasser und intelligenter Durchflussbegrenzer. Spart bis zu 40% Wasser- und Energiekosten.",
            "value_prop": "Nachhaltigkeit ohne Verzicht - sogar mit verbessertem Komfort. Massive Kosteneinsparungen bei gleichzeitig reduziertem CO2-Fußabdruck. Spielerische Umwelterziehung für Kinder.",
            "target_market": "Umweltbewusste Familien, Kostenbewusste Haushalte"
        },
        "♻️ Infinity Line": {
            "name": "zero360 Infinity Line",
            "description": "Kreislaufwirtschaft in Perfektion: Alle Komponenten vollständig recycelbar, modularer Aufbau für einfache Reparaturen. zero360 garantiert Rücknahme mit Bonus-System. Verschleißteile einzeln tauschbar ohne Komplettaustausch der Armatur.",
            "value_prop": "Echte Nachhaltigkeit mit Zertifikat und finanziellen Vorteilen. Modulares Design reduziert Wartungskosten drastisch. Rücknahme-Garantie mit Bonus schafft Planungssicherheit.",
            "target_market": "Nachhaltigkeitsbewusste Bauherren, Architekten"
        },
        "💚 EcoSense Technology": {
            "name": "zero360 EcoSense Technology",
            "description": "Ganzheitliches System macht Wasserverbrauch erlebbar ohne zu bevormunden. Mikroturbinen-Generatoren erzeugen Strom für LED-Anzeigen. Gaming-Elemente und Peer-Vergleiche über App. Automatische Monatsreports zur Amortisationsberechnung.",
            "value_prop": "Wassersparen wird zum positiven Erlebnis statt Verzicht. Gamification motiviert nachhaltig. Transparente Kostenanalyse zeigt sofort den finanziellen Nutzen.",
            "target_market": "Digital Natives, kostenbewusste Familien"
        },
        "💆 VitalShower System": {
            "name": "zero360 VitalShower System",
            "description": "Medizinische Wellness-Dusche kombiniert Licht-, Aroma- und Klangtherapie. Tageszeitabhängige Farbspektren, austauschbare Duftmodule, integrierte Resonanzkörper. Verschiedene Vital-Programme von Energiekick bis Entspannung. Dokumentiert Vitaldaten.",
            "value_prop": "Private Spa-Behandlung jeden Tag zuhause. Therapeutische Programme für Gesundheit und Wohlbefinden. Personalisierte Wellness-Empfehlungen basierend auf Vitaldaten.",
            "target_market": "Wellness-orientierte Kunden, Gesundheitsbewusste"
        },
        "🛡️ PureGuard System": {
            "name": "zero360 PureGuard Hygienesystem",
            "description": "Revolutionäre Badezimmerhygiene durch antimikrobielle Kupfer-Silber-Oberflächen, automatische UV-C-Sterilisation und intelligente Luftführung. KidsProtect-Modus für Familien. Selbstreinigende Funktion eliminiert 99,9% der Bakterien.",
            "value_prop": "Maximale Hygiene bei minimaler Arbeit. Automatische Keimbekämpfung und kindersichere Bedienung. Weniger putzen bei besserer Sauberkeit.",
            "target_market": "Familien mit Kindern, Hygiene-bewusste Haushalte"
        },
        "🔬 WaterLab Analytics": {
            "name": "zero360 WaterLab Analytics",
            "description": "Kompaktes Analysesystem überwacht kontinuierlich Wasserqualität: pH-Wert, Härtegrad, Schwermetalle, Mikroplastik, Bakterien. Aktiviert bei Bedarf verschiedene Filterstufen oder reichert Wasser mit Mineralien an. Warnt vor Medikamenten-Interaktionen.",
            "value_prop": "Gewissheit über Wasserqualität und automatische Optimierung. Gesundheitsschutz durch Medikamenten-Warnungen. Dokumentation für Vermieter-Gespräche.",
            "target_market": "Gesundheitsbewusste, Bewohner älterer Gebäude"
        }
    }
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("🎯 Produkt-Auswahl")
        
        # Quick select buttons for products
        for emoji_name, product_data in DEFAULT_PRODUCTS.items():
            if st.button(f"{emoji_name}", key=f"product_{emoji_name}", use_container_width=True):
                st.session_state.product_info = product_data.copy()
                st.success(f"✅ {product_data['name']} ausgewählt!")
                st.rerun()
        
        st.divider()
        
        st.subheader("🛠️ Custom Produkt")
        
        product_name = st.text_input(
            "🏷️ Produktname", 
            value=st.session_state.product_info.get('name', '')
        )
        
        product_description = st.text_area(
            "📋 Beschreibung",
            value=st.session_state.product_info.get('description', ''),
            height=100
        )
        
        value_prop = st.text_area(
            "💎 Value Proposition",
            value=st.session_state.product_info.get('value_prop', ''),
            height=100
        )
        
        target_market = st.text_input(
            "🎯 Zielmarkt",
            value=st.session_state.product_info.get('target_market', '')
        )
        
        if st.button("💾 Produkt speichern", type="primary"):
            st.session_state.product_info = {
                'name': product_name,
                'description': product_description,
                'value_prop': value_prop,
                'target_market': target_market
            }
            st.success("✅ Produkt gespeichert!")
    
    with col2:
        st.subheader("👁️ Produkt Übersicht")
        
        if st.session_state.product_info:
            product = st.session_state.product_info
            st.markdown(f"""
            <div class="persona-preview">
                <h3>🚀 {product.get('name', 'Unbenanntes Produkt')}</h3>
                <p><strong>📋 Beschreibung:</strong><br>{product.get('description', 'Keine Beschreibung')}</p>
                <p><strong>💎 Value Proposition:</strong><br>{product.get('value_prop', 'Keine Value Prop')}</p>
                <p><strong>🎯 Zielmarkt:</strong> {product.get('target_market', 'Nicht definiert')}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("👆 Konfiguriere dein Produkt für die Übersicht")

def process_user_message(user_input: str):
    """Process user message and generate AI response"""
    # Add user message
    st.session_state.chat_history.append({
        'role': 'user',
        'content': user_input,
        'timestamp': datetime.now()
    })
    
    # Get AI response from OpenAI
    ai_response = get_openai_response(
        user_input, 
        st.session_state.current_persona, 
        st.session_state.product_info
    )
    
    # Add AI response
    st.session_state.chat_history.append({
        'role': 'assistant',
        'content': ai_response,
        'timestamp': datetime.now()
    })
    
    # Store last AI response for voice playback
    st.session_state.last_ai_response = ai_response
    
    # Update metrics
    update_metrics()
    
    # Auto-play voice in voice mode
    if st.session_state.voice_mode and OPENAI_AVAILABLE:
        with st.spinner("🎵 Generiere Sprachantwort..."):
            audio_content = text_to_speech(ai_response)
            if audio_content:
                st.audio(audio_content, format='audio/mp3', autoplay=True)
    
    st.rerun()

def render_chat_interface():
    """Render the chat interface"""
    st.header("💬 Interview Chat")
    
    # Check if persona and product are configured
    if not st.session_state.current_persona or not st.session_state.product_info:
        st.warning("⚠️ Bitte konfiguriere erst eine Persona und ein Produkt in den anderen Tabs!")
        return
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Chat controls
        col_ctrl1, col_ctrl2, col_ctrl3, col_ctrl4 = st.columns([1, 1, 1, 1])
        
        with col_ctrl1:
            if st.button("🎬 Interview starten" if not st.session_state.interview_active else "🔄 Neu starten"):
                st.session_state.chat_history = []
                st.session_state.interview_active = True
                
                # Initial persona introduction
                persona = st.session_state.current_persona
                
                # Special handling for couple persona
                if "Sandra & Marco" in persona.get('name', ''):
                    intro = f"Hallo! Wir sind {persona.get('name', 'ein Paar')} und arbeiten als {persona.get('job', 'Mitarbeiter')} bei {persona.get('company', 'verschiedenen Unternehmen')}. Wir freuen uns auf unser Gespräch über Ihr Produkt!"
                else:
                    intro = f"Hallo! Ich bin {persona.get('name', 'eine Person')} und arbeite als {persona.get('job', 'Mitarbeiter')} bei {persona.get('company', 'einem Unternehmen')}. Ich freue mich auf unser Gespräch über Ihr Produkt!"
                
                st.session_state.chat_history.append({
                    'role': 'assistant',
                    'content': intro,
                    'timestamp': datetime.now()
                })
                st.session_state.last_ai_response = intro
                st.rerun()
        
        with col_ctrl2:
            if OPENAI_AVAILABLE and AUDIO_AVAILABLE:
                voice_mode = st.toggle("🎤 Voice Mode", value=st.session_state.voice_mode)
                st.session_state.voice_mode = voice_mode
            elif not AUDIO_AVAILABLE:
                st.info("📝 Text Only")
            else:
                st.error("⚠️ API Key fehlt")
        
        with col_ctrl3:
            if st.session_state.last_ai_response and OPENAI_AVAILABLE:
                if st.button("🔊 Antwort hören"):
                    with st.spinner("🎵 Generiere Audio..."):
                        audio_content = text_to_speech(st.session_state.last_ai_response)
                        if audio_content:
                            st.audio(audio_content, format='audio/mp3', autoplay=True)
        
        with col_ctrl4:
            if st.button("🗑️ Chat löschen"):
                st.session_state.chat_history = []
                st.session_state.interview_active = False
                st.session_state.last_ai_response = ''
                st.rerun()
        
        # Chat display
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        
        for message in st.session_state.chat_history:
            if message['role'] == 'user':
                st.markdown(f"""
                <div class="chat-message user-message">
                    <strong>🧑‍💼 Sie:</strong><br>
                    {message['content']}
                    <small style="color: #666; float: right;">{message['timestamp'].strftime('%H:%M')}</small>
                </div>
                """, unsafe_allow_html=True)
            else:
                persona_name = st.session_state.current_persona.get('name', 'Persona')
                st.markdown(f"""
                <div class="chat-message ai-message">
                    <strong>🎭 {persona_name}:</strong><br>
                    {message['content']}
                    <small style="color: #666; float: right;">{message['timestamp'].strftime('%H:%M')}</small>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Voice Input Section
        if st.session_state.interview_active and st.session_state.voice_mode and AUDIO_AVAILABLE:
            st.subheader("🎤 Voice Input")
            
            col_voice1, col_voice2 = st.columns([1, 1])
            
            with col_voice1:
                # Audio recorder
                audio_bytes = audio_recorder(
                    text="🎤 Drücken & Sprechen",
                    recording_color="#e74c3c",
                    neutral_color="#3498db",
                    icon_name="microphone",
                    icon_size="2x",
                )
                
                if audio_bytes:
                    st.audio(audio_bytes, format="audio/wav")
                    
                    # Transcribe audio
                    with st.spinner("🎯 Transkribiere Audio..."):
                        transcript = transcribe_audio(audio_bytes)
                        
                    if transcript and transcript != "Transkriptionsfehler":
                        st.success(f"💬 Sie sagten: {transcript}")
                        
                        # Process the transcribed text as user input
                        process_user_message(transcript)
            
            with col_voice2:
                st.info("💡 **Voice Mode aktiv**\n\nDrücken Sie den Mikrofon-Button und sprechen Sie Ihre Frage. Die Antwort wird automatisch vorgelesen.")
        
        # Interview Question Suggestions
        if st.session_state.interview_active and st.session_state.current_persona and st.session_state.product_info:
            # Show context indicator
            if len(st.session_state.chat_history) > 2:
                st.subheader("💡 Adaptive Fragenvorschläge 🔄")
                st.caption("*Fragen passen sich automatisch an das Gespräch an*")
            else:
                st.subheader("💡 Einstiegsfragen")
                st.caption("*Perfekte Startfragen für Ihr Interview*")
            
            # Generate adaptive questions based on conversation context
            suggested_questions = generate_adaptive_questions(
                st.session_state.current_persona, 
                st.session_state.product_info,
                st.session_state.chat_history
            )
            
            col_q1, col_q2, col_q3 = st.columns(3)
            
            with col_q1:
                if st.button(f"❓ {suggested_questions[0]}", key="q1", use_container_width=True):
                    process_user_message(suggested_questions[0])
            
            with col_q2:
                if st.button(f"❓ {suggested_questions[1]}", key="q2", use_container_width=True):
                    process_user_message(suggested_questions[1])
            
            with col_q3:
                if st.button(f"❓ {suggested_questions[2]}", key="q3", use_container_width=True):
                    process_user_message(suggested_questions[2])
            
            # Debug info for workshop demonstration (optional)
            if len(st.session_state.chat_history) > 2:
                with st.expander("🔍 Erkannte Gesprächsthemen (Demo-Info)", expanded=False):
                    # Analyze current conversation topics
                    conversation_topics = []
                    last_responses = []
                    
                    for message in st.session_state.chat_history[-6:]:
                        if message['role'] == 'assistant':
                            last_responses.append(message['content'].lower())
                    
                    context_keywords = {
                        'Preis & Budget': ['preis', 'kosten', 'budget', 'geld', 'teuer', 'günstig', 'investition'],
                        'Installation': ['installation', 'montage', 'einbau', 'handwerker', 'selbst'],
                        'Technologie': ['technologie', 'digital', 'smart', 'app', 'bedienung'],
                        'Design': ['design', 'aussehen', 'optik', 'stil', 'farbe'],
                        'Nachhaltigkeit': ['nachhaltigkeit', 'umwelt', 'energie', 'wasser', 'sparen'],
                        'Familie': ['familie', 'kinder', 'alltag', 'morgen', 'stress'],
                        'Qualität': ['qualität', 'robust', 'langlebig', 'haltbar', 'zuverlässig'],
                        'Vergleich': ['vergleich', 'konkurrenz', 'alternative', 'unterschied'],
                        'Bedenken': ['bedenken', 'problem', 'schwierig', 'sorge', 'risiko'],
                        'Vorteile': ['vorteil', 'nutzen', 'hilft', 'besser', 'verbessert']
                    }
                    
                    detected_topics = []
                    for topic, keywords in context_keywords.items():
                        for response in last_responses:
                            if any(keyword in response for keyword in keywords):
                                detected_topics.append(topic)
                                break
                    
                    if detected_topics:
                        st.write("**Aktuelle Themen:** " + " • ".join(detected_topics))
                    else:
                        st.write("**Status:** Allgemeine Einstiegsphase")
            
            st.markdown("---")
        
        # Text Input (always available)
        if st.session_state.interview_active:
            input_placeholder = "💭 Ihre eigene Frage an die Persona..." if not st.session_state.voice_mode else "💭 Oder tippen Sie hier..."
            user_input = st.chat_input(input_placeholder)
            
            if user_input:
                process_user_message(user_input)
    
    with col2:
        render_live_metrics()

def update_metrics():
    """Update live metrics based on chat history"""
    if not st.session_state.chat_history:
        return
    
    # Get all AI messages for analysis
    ai_messages = [msg['content'] for msg in st.session_state.chat_history if msg['role'] == 'assistant']
    
    if ai_messages:
        # Calculate average sentiment
        sentiments = [analyze_sentiment(msg) for msg in ai_messages]
        avg_sentiment = sum(sentiments) / len(sentiments)
        
        # Calculate conviction level
        conviction = calculate_conviction(st.session_state.chat_history)
        
        # Extract concerns from all messages
        all_concerns = []
        for msg in ai_messages:
            all_concerns.extend(extract_concerns(msg))
        
        # Update session state
        st.session_state.metrics = {
            'sentiment_score': avg_sentiment,
            'conviction_level': conviction,
            'main_concerns': list(set(all_concerns))
        }

def render_live_metrics():
    """Render live metrics panel"""
    st.subheader("📊 Live Metriken")
    
    metrics = st.session_state.metrics
    
    # Sentiment
    sentiment = metrics['sentiment_score']
    sentiment_emoji = "😊" if sentiment > 0.6 else "😐" if sentiment > 0.4 else "😟"
    sentiment_color = "sentiment-positive" if sentiment > 0.6 else "sentiment-neutral" if sentiment > 0.4 else "sentiment-negative"
    
    st.markdown(f"""
    <div class="metric-card {sentiment_color}">
        <h4>{sentiment_emoji} Sentiment</h4>
        <h2>{sentiment:.1%}</h2>
        <p>Positive Stimmung der Persona</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Conviction Level
    conviction = metrics['conviction_level']
    conviction_emoji = "🎯" if conviction > 0.7 else "🤔" if conviction > 0.4 else "❓"
    
    st.markdown(f"""
    <div class="metric-card">
        <h4>{conviction_emoji} Überzeugungsgrad</h4>
        <h2>{conviction:.1%}</h2>
        <p>Interesse am Produkt</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Main Concerns
    concerns = metrics['main_concerns']
    
    st.markdown(f"""
    <div class="metric-card">
        <h4>🚨 Hauptbedenken ({len(concerns)})</h4>
        <div>
            {' '.join(concerns) if concerns else 'Keine erkannt'}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Progress Chart
    if st.session_state.chat_history:
        st.subheader("📈 Gesprächsverlauf")
        
        # Create sentiment timeline
        timestamps = []
        sentiment_scores = []
        
        for msg in st.session_state.chat_history:
            if msg['role'] == 'assistant':
                timestamps.append(msg['timestamp'])
                sentiment_scores.append(analyze_sentiment(msg['content']))
        
        if len(sentiment_scores) > 1:
            df = pd.DataFrame({
                'Zeit': timestamps,
                'Sentiment': sentiment_scores
            })
            
            fig = px.line(
                df, 
                x='Zeit', 
                y='Sentiment',
                title='Sentiment Verlauf',
                range_y=[0, 1]
            )
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)

def render_export_tab():
    """Render export functionality"""
    st.header("📥 Export & Analyse")
    
    if not st.session_state.chat_history:
        st.info("💡 Führe erst ein Interview, um Daten zu exportieren!")
        return
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📊 Interview Zusammenfassung")
        
        # Basic stats
        user_messages = [msg for msg in st.session_state.chat_history if msg['role'] == 'user']
        ai_messages = [msg for msg in st.session_state.chat_history if msg['role'] == 'assistant']
        
        st.metric("💬 Nachrichten gesamt", len(st.session_state.chat_history))
        st.metric("❓ Ihre Fragen", len(user_messages))
        st.metric("💭 Persona Antworten", len(ai_messages))
        
        # Duration
        if len(st.session_state.chat_history) >= 2:
            start_time = st.session_state.chat_history[0]['timestamp']
            end_time = st.session_state.chat_history[-1]['timestamp']
            duration = end_time - start_time
            st.metric("⏱️ Gesprächsdauer", f"{duration.seconds // 60} Min")
        
        st.subheader("🎯 Key Insights")
        
        metrics = st.session_state.metrics
        st.write(f"**Sentiment:** {metrics['sentiment_score']:.1%}")
        st.write(f"**Überzeugungsgrad:** {metrics['conviction_level']:.1%}")
        st.write(f"**Hauptbedenken:** {', '.join(metrics['main_concerns']) if metrics['main_concerns'] else 'Keine'}")
    
    with col2:
        st.subheader("💾 Export Optionen")
        
        # Prepare export data
        export_data = {
            'interview_info': {
                'date': datetime.now().isoformat(),
                'duration_minutes': (st.session_state.chat_history[-1]['timestamp'] - st.session_state.chat_history[0]['timestamp']).seconds // 60 if len(st.session_state.chat_history) >= 2 else 0,
                'total_messages': len(st.session_state.chat_history)
            },
            'persona': st.session_state.current_persona,
            'product': st.session_state.product_info,
            'chat_history': [
                {
                    'role': msg['role'],
                    'content': msg['content'],
                    'timestamp': msg['timestamp'].isoformat()
                } for msg in st.session_state.chat_history
            ],
            'metrics': st.session_state.metrics
        }
        
        # JSON Export
        json_data = json.dumps(export_data, indent=2, ensure_ascii=False)
        
        st.download_button(
            label="📄 Als JSON exportieren",
            data=json_data,
            file_name=f"interview_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            type="primary"
        )
        
        # CSV Export (Chat History)
        if st.session_state.chat_history:
            chat_df = pd.DataFrame([
                {
                    'Timestamp': msg['timestamp'],
                    'Role': 'Interviewer' if msg['role'] == 'user' else 'Persona',
                    'Message': msg['content']
                } for msg in st.session_state.chat_history
            ])
            
            csv_data = chat_df.to_csv(index=False)
            
            st.download_button(
                label="📊 Chat als CSV exportieren",
                data=csv_data,
                file_name=f"chat_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        
        # Summary Report
        st.subheader("📋 Report Vorschau")
        
        report = f"""
# Interview Report

**Datum:** {datetime.now().strftime('%d.%m.%Y %H:%M')}
**Persona:** {st.session_state.current_persona.get('name', 'N/A')}
**Produkt:** {st.session_state.product_info.get('name', 'N/A')}

## Metriken
- Sentiment: {metrics['sentiment_score']:.1%}
- Überzeugungsgrad: {metrics['conviction_level']:.1%}
- Hauptbedenken: {', '.join(metrics['main_concerns']) if metrics['main_concerns'] else 'Keine'}

## Empfehlungen
{"- Positive Resonanz nutzen für Marketing" if metrics['sentiment_score'] > 0.6 else "- Bedenken addressieren"}
{"- Überzeugung ist hoch, Sales-Ready" if metrics['conviction_level'] > 0.7 else "- Mehr Aufklärung nötig"}
        """
        
        st.text_area("📝 Report Vorschau", report, height=300)

# Main Application
def main():
    # Initialize session state
    initialize_session_state()
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🔬 zero360 User Research Lab</h1>
        <p>Führe realistische Interviews mit KI-Personas zu innovativen Produktkonzepten</p>
    </div>
    """, unsafe_allow_html=True)
    
    # API Status indicator
    col_status1, col_status2, col_status3 = st.columns([1, 1, 2])
    
    with col_status1:
        if OPENAI_AVAILABLE:
            st.success("✅ OpenAI verfügbar")
        else:
            st.error("⚠️ OpenAI API Key fehlt")
    
    with col_status2:
        st.info("🤖 Live OpenAI Integration")
    
    # Main tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "👤 Persona Builder", 
        "🚀 Produkt Config", 
        "💬 Interview Chat", 
        "📥 Export & Analyse"
    ])
    
    with tab1:
        render_persona_builder()
    
    with tab2:
        render_product_config()
    
    with tab3:
        render_chat_interface()
    
    with tab4:
        render_export_tab()

if __name__ == "__main__":
    main()
