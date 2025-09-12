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

# Import OpenAI and load environment variables
import openai
from dotenv import load_dotenv
load_dotenv()

# Set up OpenAI - Compatible with both local .env and Streamlit Cloud secrets
try:
    # Try Streamlit secrets first (for cloud deployment)
    OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY")
except (AttributeError, FileNotFoundError, KeyError):
    # Fallback to environment variable (for local development)
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

OPENAI_AVAILABLE = bool(OPENAI_API_KEY)

# Page config
st.set_page_config(
    page_title="zero360 Autonomous Research Lab",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for 3-column layout with left navigation
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
    }
    
    /* Remove default Streamlit padding and margins */
    .main .block-container {
        padding-top: 0.5rem;
        padding-bottom: 1rem;
        max-width: none;
    }
    
    /* Hide the main header/hero banner */
    .main-header {
        display: none;
    }
    
    /* Compact Navigation Bar */
    .nav-bar {
        background: linear-gradient(135deg, var(--primary) 0%, var(--primary-light) 100%);
        color: white;
        padding: var(--space-3) var(--space-4);
        margin: calc(-1 * var(--space-4)) calc(-1 * var(--space-4)) var(--space-4) calc(-1 * var(--space-4));
        border-radius: 0;
        box-shadow: var(--shadow-md);
        position: relative;
        display: flex;
        align-items: center;
        justify-content: space-between;
        min-height: 60px;
    }
    
    /* Navigation buttons styling */
    .nav-buttons {
        display: flex;
        gap: var(--space-2);
        align-items: center;
    }
    
    /* Enhanced button styling for navigation */
    .stButton > button[data-testid="baseButton-primary"] {
        background: var(--primary) !important;
        border: 2px solid var(--accent) !important;
        color: white !important;
        font-weight: 600 !important;
    }
    
    .stButton > button[data-testid="baseButton-secondary"] {
        background: rgba(255, 255, 255, 0.1) !important;
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
        color: white !important;
    }
    
    .nav-bar h1 {
        font-size: 1.5rem;
        font-weight: 700;
        margin: 0;
        letter-spacing: -0.025em;
    }
    
    .nav-bar .status-indicator {
        display: flex;
        gap: var(--space-4);
        align-items: center;
        font-size: 0.875rem;
    }
    
    .status-badge {
        background: rgba(255, 255, 255, 0.2);
        padding: var(--space-1) var(--space-3);
        border-radius: var(--radius);
        backdrop-filter: blur(10px);
    }
    
    .status-badge.success {
        background: rgba(16, 185, 129, 0.9);
    }
    
    .status-badge.error {
        background: rgba(239, 68, 68, 0.9);
    }
    
    /* Sidebar Styling - Simplified */
    .css-1d391kg {
        background: linear-gradient(180deg, var(--gray-50) 0%, var(--gray-100) 100%);
        border-right: 1px solid var(--gray-200);
    }
    
    /* 3-Column Layout */
    .three-column-container {
        display: grid;
        grid-template-columns: 1fr 2fr 1fr;
        gap: var(--space-6);
        min-height: calc(100vh - 120px);
    }
    
    .column {
        background: white;
        border-radius: var(--radius-lg);
        padding: var(--space-6);
        box-shadow: var(--shadow);
        border: 1px solid var(--gray-200);
        overflow-y: auto;
        max-height: calc(100vh - 140px);
    }
    
    .column h3 {
        color: var(--primary);
        margin-top: 0;
        margin-bottom: var(--space-4);
        font-size: 1.25rem;
        font-weight: 600;
        border-bottom: 2px solid var(--gray-100);
        padding-bottom: var(--space-2);
    }
    
    /* Left Column - Configuration */
    .left-column {
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
    }
    
    /* Center Column - Main Content */
    .center-column {
        background: white;
    }
    
    /* Right Column - Analytics */
    .right-column {
        background: linear-gradient(135deg, #fefefe 0%, #f9fafb 100%);
    }
    
    /* Cards - Clean and modern */
    .persona-preview {
        background: white;
        padding: var(--space-6);
        border-radius: var(--radius);
        border: 1px solid var(--gray-200);
        margin: var(--space-3) 0;
        box-shadow: var(--shadow-sm);
        transition: all 0.2s ease;
    }
    
    .persona-preview:hover {
        box-shadow: var(--shadow);
        transform: translateY(-1px);
    }
    
    .example-persona {
        background: white;
        padding: var(--space-4);
        border-radius: var(--radius);
        border: 1px solid var(--gray-200);
        border-left: 4px solid var(--primary);
        margin: var(--space-2) 0;
        cursor: pointer;
        transition: all 0.2s ease;
        box-shadow: var(--shadow-sm);
        font-size: 0.875rem;
    }
    
    .example-persona:hover {
        transform: translateY(-1px);
        box-shadow: var(--shadow);
        border-left-color: var(--primary-light);
    }
    
    /* Chat styling - Compact */
    .chat-container {
        background: var(--gray-50);
        border-radius: var(--radius);
        padding: var(--space-4);
        margin: var(--space-4) 0;
        max-height: 400px;
        overflow-y: auto;
        border: 1px solid var(--gray-200);
    }
    
    .chat-message {
        padding: var(--space-3);
        margin: var(--space-2) 0;
        border-radius: var(--radius);
        font-size: 0.875rem;
    }
    
    .user-message {
        background: white;
        border: 1px solid var(--gray-200);
        margin-left: var(--space-6);
        color: var(--gray-900);
    }
    
    .ai-message {
        background: var(--primary);
        color: white;
        margin-right: var(--space-6);
    }
    
    /* Metrics cards - Compact */
    .metric-card {
        background: white;
        padding: var(--space-4);
        border-radius: var(--radius);
        border: 1px solid var(--gray-200);
        margin: var(--space-2) 0;
        box-shadow: var(--shadow-sm);
        color: var(--gray-900);
        transition: all 0.2s ease;
    }
    
    .metric-card h4 {
        margin: 0 0 var(--space-2) 0;
        font-size: 0.875rem;
        color: var(--gray-600);
    }
    
    .metric-card h2 {
        margin: 0;
        font-size: 1.5rem;
        font-weight: 700;
        color: var(--primary);
    }
    
    .metric-card p {
        margin: var(--space-1) 0 0 0;
        font-size: 0.75rem;
        color: var(--gray-500);
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
    
    /* Buttons - Compact */
    .stButton > button {
        background: var(--primary);
        color: white;
        border: none;
        border-radius: var(--radius);
        padding: var(--space-2) var(--space-4);
        font-weight: 500;
        font-size: 0.875rem;
        transition: all 0.2s ease;
        box-shadow: var(--shadow-sm);
        width: 100%;
    }
    
    .stButton > button:hover {
        background: var(--primary-light);
        transform: translateY(-1px);
        box-shadow: var(--shadow);
    }
    
    /* Form inputs - Compact */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div {
        font-size: 0.875rem;
        border: 1px solid var(--gray-200);
        border-radius: var(--radius);
        box-shadow: var(--shadow-sm);
    }
    
    /* Scrollbars */
    ::-webkit-scrollbar {
        width: 4px;
        height: 4px;
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
    
    /* Hide Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Make content fit without scrolling */
    .main {
        overflow: hidden;
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
    ]
}

# Initialize session state for autonomous research
def initialize_session_state():
    defaults = {
        # Autonomous interview system
        'autonomous_interviews': [],  # List of completed autonomous interviews
        'current_product': {},  # Single product to test across all interviews
        'research_active': False,
        'interviews_completed': 0,
        'max_interviews': 10,
        
        # Current single interview (for monitoring)
        'current_interview': None,
        'current_interview_id': None,
        
        # UI state
        'current_step': 0,  # 0: Demographics, 1: Define Product, 2: Generate Interviews, 3: Analyze Results
        'flow_completed': [False, False, False, False],
        
        # New: Target demographics and personas
        'target_demographics': {},
        'assembled_personas': [],
        
        # Legacy (for backward compatibility during transition)
        'demo_mode': False,
        'voice_mode': False
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# Autonomous Interview Generation
def generate_diverse_persona() -> Dict:
    """Generate a diverse persona using AI"""
    if not OPENAI_AVAILABLE:
        # Fallback to predefined personas
        personas = list(EXAMPLE_PERSONAS.values())
        return random.choice(personas)
    
    try:
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": """You are a persona generator for user research. Create diverse, realistic personas for bathroom/sanitary product research.

Generate a JSON object with these exact fields:
- name: Full name (German)
- age: Age between 25-70
- job: Job title
- company: Company description
- experience: Background and experience with bathroom products/renovations
- pain_points: Current challenges and frustrations
- goals: What they want to achieve
- personality: Communication style and decision-making approach

Make each persona unique with different demographics, life situations, and perspectives. Focus on realistic German customers."""},
                {"role": "user", "content": "Generate a unique persona for bathroom product research."}
            ],
            max_tokens=800,
            temperature=0.9  # High temperature for diversity
        )
        
        import json
        persona_text = response.choices[0].message.content.strip()
        # Extract JSON from response if wrapped in markdown
        if "```json" in persona_text:
            persona_text = persona_text.split("```json")[1].split("```")[0]
        elif "```" in persona_text:
            persona_text = persona_text.split("```")[1]
            
        persona = json.loads(persona_text)
        return persona
        
    except Exception as e:
        st.error(f"Error generating persona: {str(e)}")
        # Fallback to predefined personas
        personas = list(EXAMPLE_PERSONAS.values())
        return random.choice(personas)

def generate_interview_questions(persona: Dict, product: Dict, num_questions: int = 8) -> List[str]:
    """Generate diverse interview questions for a persona and product"""
    if not OPENAI_AVAILABLE:
        return [
            f"Was ist Ihr erster Eindruck vom {product.get('name', 'Produkt')}?",
            "Welche Bedenken hätten Sie bei der Anschaffung?",
            "Wie würde das Ihren Alltag verändern?",
            "Was ist Ihnen bei Badezimmerprodukten am wichtigsten?",
            "Haben Sie schon mal ähnliche Produkte verwendet?",
            "Welche Probleme soll das Produkt für Sie lösen?",
            "Würden Sie das weiterempfehlen?",
            "Was fehlt Ihnen noch für eine Kaufentscheidung?"
        ]
    
    try:
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": f"""You are a user research expert. Generate {num_questions} diverse, open-ended interview questions in German.

Persona: {persona.get('name', 'Person')} - {persona.get('job', 'Professional')}
Product: {product.get('name', 'Product')}

Questions should:
1. Explore different aspects (needs, concerns, usage, decision-making)
2. Be open-ended and conversational
3. Uncover deep insights about the persona's perspective
4. Be appropriate for this specific persona's background
5. Be in German

Return ONLY a JSON array of question strings, no other text."""},
                {"role": "user", "content": f"Generate {num_questions} interview questions for this persona and product combination."}
            ],
            max_tokens=600,
            temperature=0.8
        )
        
        import json
        questions_text = response.choices[0].message.content.strip()
        # Extract JSON from response if wrapped in markdown
        if "```json" in questions_text:
            questions_text = questions_text.split("```json")[1].split("```")[0]
        elif "```" in questions_text:
            questions_text = questions_text.split("```")[1]
            
        questions = json.loads(questions_text)
        return questions
        
    except Exception as e:
        st.error(f"Error generating questions: {str(e)}")
        return [
            f"Was ist Ihr erster Eindruck vom {product.get('name', 'Produkt')}?",
            "Welche Bedenken hätten Sie bei der Anschaffung?",
            "Wie würde das Ihren Alltag verändern?"
        ]

def conduct_autonomous_interview(persona: Dict, product: Dict, questions: List[str]) -> Dict:
    """Conduct a full autonomous interview with a persona"""
    interview_data = {
        'id': f"interview_{len(st.session_state.autonomous_interviews) + 1}",
        'persona': persona,
        'product': product,
        'timestamp': datetime.now(),
        'conversation': [],
        'metrics': {
            'sentiment_score': 0.5,
            'conviction_level': 0.5,
            'main_concerns': []
        },
        'status': 'running'
    }
    
    # Simulate conversation
    for i, question in enumerate(questions):
        # Add question
        interview_data['conversation'].append({
            'role': 'user',
            'content': question,
            'timestamp': datetime.now()
        })
        
        # Get AI response
        ai_response = get_openai_response(question, persona, product)
        interview_data['conversation'].append({
            'role': 'assistant',
            'content': ai_response,
            'timestamp': datetime.now()
        })
        
        # Update progress
        progress = (i + 1) / len(questions)
        if 'progress_placeholder' in st.session_state:
            st.session_state.progress_placeholder.progress(progress, f"Question {i+1}/{len(questions)}")
    
    # Calculate final metrics
    interview_data['metrics'] = calculate_interview_metrics(interview_data['conversation'])
    interview_data['status'] = 'completed'
    
    return interview_data

def calculate_interview_metrics(conversation: List[Dict]) -> Dict:
    """Calculate metrics for a completed interview"""
    ai_messages = [msg['content'] for msg in conversation if msg['role'] == 'assistant']
    
    if not ai_messages:
        return {
            'sentiment_score': 0.5,
            'conviction_level': 0.5,
            'main_concerns': []
        }
    
    # Calculate average sentiment
    sentiments = [analyze_sentiment(msg) for msg in ai_messages]
    avg_sentiment = sum(sentiments) / len(sentiments)
    
    # Calculate conviction level
    conviction = calculate_conviction(conversation)
    
    # Extract concerns from all messages
    all_concerns = []
    for msg in ai_messages:
        all_concerns.extend(extract_concerns(msg))
    
    return {
        'sentiment_score': avg_sentiment,
        'conviction_level': conviction,
        'main_concerns': list(set(all_concerns))
    }

# AI Response Functions
def get_openai_response(message: str, persona: Dict, product: Dict) -> str:
    """Get response from OpenAI API"""
    if not OPENAI_AVAILABLE:
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
        return f"Entschuldigung, es gab einen Fehler bei der Verbindung zur API: {str(e)}"

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

# Removed old question generation functions - now using AI-generated questions in autonomous research

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

# Removed old manual interview functions - now using autonomous research

# New: Autonomous Research Navigation Bar
def render_nav_bar():
    """Render navigation bar for autonomous research flow"""
    st.markdown(f"""
    <div class="nav-bar">
        <h1>🤖 zero360 Autonomous Research Lab</h1>
        <div class="status-indicator">
            <div class="status-badge {'success' if OPENAI_AVAILABLE else 'error'}">
                {'✅ AI Ready' if OPENAI_AVAILABLE else '⚠️ API Key Missing'}
            </div>
            <div class="status-badge">
                🎯 {st.session_state.interviews_completed}/{st.session_state.max_interviews} Interviews
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Step-based navigation with progress indicator
    st.markdown("### 🚀 Autonomous Research Flow")
    
    # Progress indicator using Streamlit columns instead of HTML
    st.markdown("**Progress:**")
    
    steps = [
        ("👥 Demographics", st.session_state.flow_completed[0]),
        ("🚀 Product", st.session_state.flow_completed[1]),
        ("🤖 Generate", st.session_state.flow_completed[2]),
        ("📊 Analyze", st.session_state.flow_completed[3])
    ]
    
    progress_cols = st.columns(4)
    
    for i, (step_name, completed) in enumerate(steps):
        with progress_cols[i]:
            is_current = st.session_state.current_step == i
            
            if completed:
                status_icon = "✅"
                status_text = "Complete"
            elif is_current:
                status_icon = "🔵"
                status_text = "Current"
            else:
                status_icon = "⚪"
                status_text = "Pending"
            
            st.markdown(f"""
            <div style="text-align: center; padding: 10px; border-radius: 8px; background: {'#f0f9ff' if is_current else '#f8fafc'};">
                <div style="font-size: 24px;">{status_icon}</div>
                <div style="font-size: 12px; font-weight: 600; margin: 5px 0;">Step {i}</div>
                <div style="font-size: 10px; color: #64748b;">{step_name}</div>
                <div style="font-size: 9px; color: #9ca3af;">{status_text}</div>
            </div>
            """, unsafe_allow_html=True)
    
    # Step navigation buttons
    step_cols = st.columns(4)
    
    step_buttons = [
        ("Step 0: Target Demographics", 0, "👥"),
        ("Step 1: Define Product", 1, "🚀"),
        ("Step 2: Generate Interviews", 2, "🤖"),
        ("Step 3: Analyze Results", 3, "📊")
    ]
    
    for i, (label, step_num, emoji) in enumerate(step_buttons):
        with step_cols[i]:
            is_current = st.session_state.current_step == step_num
            is_completed = st.session_state.flow_completed[step_num]
            
            # Determine button type and availability
            if is_completed:
                button_type = "secondary"
                disabled = False
            elif is_current:
                button_type = "primary"
                disabled = False
            elif step_num == 0:  # Step 0 is always available
                button_type = "secondary"
                disabled = False
            elif step_num > 0 and st.session_state.flow_completed[step_num - 1]:  # Previous step completed
                button_type = "secondary"
                disabled = False
            else:
                button_type = "secondary"
                disabled = True
            
            if st.button(f"{emoji} {label}", 
                        key=f"step_{step_num}", 
                        use_container_width=True,
                        type=button_type,
                        disabled=disabled):
                st.session_state.current_step = step_num
                st.rerun()
    
    st.markdown("---")

# Sidebar for Autonomous Research Stats
def render_sidebar_stats():
    """Render sidebar with autonomous research stats"""
    with st.sidebar:
        st.markdown("### 🤖 Autonomous Research")
        
        # Current demographics info
        if st.session_state.target_demographics:
            st.markdown("#### 👥 Target Demographics")
            demographics = st.session_state.target_demographics
            st.info(f"**{demographics.get('segment_name', 'Custom Segment')}**")
            st.write(f"Age: {demographics.get('age_range', 'Not defined')}")
            st.write(f"Personas: {len(st.session_state.assembled_personas)}")
        
        # Current product info
        if st.session_state.current_product:
            st.markdown("#### 🚀 Current Product")
            product = st.session_state.current_product
            st.info(f"**{product.get('name', 'Unnamed Product')}**")
            st.write(f"Target: {product.get('target_market', 'Not defined')}")
        
        # Interview progress
        if st.session_state.autonomous_interviews:
            st.markdown("#### 📊 Interview Progress")
            completed = len([i for i in st.session_state.autonomous_interviews if i['status'] == 'completed'])
            st.metric("Completed Interviews", completed)
            st.metric("Total Interviews", len(st.session_state.autonomous_interviews))
            
            # Quick stats from completed interviews
            if completed > 0:
                completed_interviews = [i for i in st.session_state.autonomous_interviews if i['status'] == 'completed']
                avg_sentiment = sum(i['metrics']['sentiment_score'] for i in completed_interviews) / len(completed_interviews)
                avg_conviction = sum(i['metrics']['conviction_level'] for i in completed_interviews) / len(completed_interviews)
                
                st.metric("Avg Sentiment", f"{avg_sentiment:.1%}")
                st.metric("Avg Conviction", f"{avg_conviction:.1%}")
        else:
            st.markdown("#### ℹ️ Getting Started")
            st.info("Define your target demographics in Step 0 to begin autonomous research.")
        
        # Current interview status
        if st.session_state.research_active:
            st.markdown("#### ⚡ Status")
            st.warning("🔄 Research in progress...")
            if st.session_state.current_interview:
                current = st.session_state.current_interview
                st.write(f"**Current:** {current['persona']['name']}")
                st.write(f"**Status:** {current['status']}")
        
        # Quick actions
        st.markdown("#### 🔧 Quick Actions")
        if st.button("🔄 Reset All", use_container_width=True):
            st.session_state.autonomous_interviews = []
            st.session_state.current_product = {}
            st.session_state.target_demographics = {}
            st.session_state.assembled_personas = []
            st.session_state.research_active = False
            st.session_state.interviews_completed = 0
            st.session_state.current_step = 0
            st.session_state.flow_completed = [False, False, False, False]
            st.rerun()

# Removed old column rendering functions - now using autonomous research flow

def render_main_content():
    """Render main content based on current autonomous research step"""
    step = st.session_state.current_step
    
    if step == 0:
        render_step0_define_demographics()
    elif step == 1:
        render_step1_define_product()
    elif step == 2:
        render_step2_generate_interviews()
    elif step == 3:
        render_step3_analyze_results()
    else:
        # Default to step 0 if no valid step is set
        st.session_state.current_step = 0
        render_step0_define_demographics()


def render_step0_define_demographics():
    """Step 0: Define Target Demographics and Assemble Personas"""
    st.markdown("## Step 0: Define Target Demographics & Segment 👥")
    st.markdown("Define your target user demographics and segment. AI will assemble a representative group of personas based on your specifications.")
    
    # Demographics Definition
    st.markdown("### 🎯 Target Demographics")
    
    # Option 1: Quick Demographic Templates
    st.markdown("#### 🚀 Quick Demographic Templates")
    st.markdown("Select from pre-defined demographic segments:")
    
    DEMOGRAPHIC_TEMPLATES = {
        "🏠 Premium Homeowners": {
            "age_range": "35-65",
            "income_level": "High (€80k+)",
            "location": "Urban/Suburban premium areas",
            "lifestyle": "Quality-focused, design-conscious",
            "tech_comfort": "Medium to High",
            "renovation_experience": "Some to Extensive",
            "key_motivations": ["Quality", "Status", "Long-term value", "Innovation"],
            "segment_description": "Affluent homeowners who value premium quality and are willing to invest in high-end solutions. They appreciate craftsmanship, innovation, and products that reflect their status."
        },
        "👨‍👩‍👧‍👦 Growing Families": {
            "age_range": "28-45",
            "income_level": "Medium to High (€50k-100k)",
            "location": "Suburban family neighborhoods",
            "lifestyle": "Family-focused, practical, busy",
            "tech_comfort": "Medium",
            "renovation_experience": "Limited to Some",
            "key_motivations": ["Functionality", "Safety", "Durability", "Value for money"],
            "segment_description": "Young to middle-aged families with children who prioritize practical solutions that make daily life easier. They need robust, safe products that can handle family use."
        },
        "🌱 Eco-Conscious Millennials": {
            "age_range": "25-40",
            "income_level": "Medium (€40k-80k)",
            "location": "Urban areas, eco-friendly communities",
            "lifestyle": "Sustainability-focused, tech-savvy",
            "tech_comfort": "High",
            "renovation_experience": "DIY-friendly, research-heavy",
            "key_motivations": ["Sustainability", "Innovation", "Cost savings", "Environmental impact"],
            "segment_description": "Environmentally conscious millennials who research extensively and prefer sustainable, innovative solutions. They're willing to invest in eco-friendly technology."
        },
        "🏢 Commercial Decision Makers": {
            "age_range": "35-55",
            "income_level": "Business/Corporate",
            "location": "Commercial properties, hotels, offices",
            "lifestyle": "Professional, efficiency-focused",
            "tech_comfort": "Medium to High",
            "renovation_experience": "Extensive (professional)",
            "key_motivations": ["ROI", "Reliability", "Maintenance costs", "Guest satisfaction"],
            "segment_description": "Professional decision makers in hospitality, real estate, or facilities management who focus on operational efficiency, cost-effectiveness, and customer satisfaction."
        },
        "👴 Active Seniors": {
            "age_range": "55-75",
            "income_level": "Medium to High (established wealth)",
            "location": "Established neighborhoods, retirement communities",
            "lifestyle": "Comfort-focused, accessibility-aware",
            "tech_comfort": "Low to Medium",
            "renovation_experience": "Extensive life experience",
            "key_motivations": ["Comfort", "Accessibility", "Reliability", "Ease of use"],
            "segment_description": "Active seniors who are planning for aging in place. They value comfort, accessibility, and reliable products that are easy to use and maintain."
        }
    }
    
    # Display demographic templates in grid
    demo_cols = st.columns(2)
    demo_list = list(DEMOGRAPHIC_TEMPLATES.items())
    
    for i, (demo_name, demo_data) in enumerate(demo_list):
        col = demo_cols[i % 2]
        
        with col:
            with st.container():
                st.markdown(f"**{demo_name}**")
                st.markdown(f"**Age:** {demo_data['age_range']} | **Income:** {demo_data['income_level']}")
                st.markdown(f"_{demo_data['segment_description'][:120]}..._")
                st.markdown(f"**Key Motivations:** {', '.join(demo_data['key_motivations'][:3])}")
                
                if st.button(f"Select {demo_name}", key=f"demo_select_{i}", use_container_width=True):
                    st.session_state.target_demographics = demo_data.copy()
                    st.session_state.target_demographics['segment_name'] = demo_name
                    st.success(f"✅ {demo_name} demographics selected!")
                    # Auto-generate personas for this demographic
                    generate_personas_for_demographic(demo_data, demo_name)
                    st.rerun()
    
    # Option 2: Custom Demographics
    st.markdown("#### ✏️ Or Define Custom Demographics")
    
    with st.expander("🎨 Create Custom Demographics", expanded=False):
        with st.form("custom_demographics_form"):
            st.markdown("Define your target demographics and segment characteristics:")
            
            col1, col2 = st.columns(2)
            
            with col1:
                segment_name = st.text_input("Segment Name*", placeholder="e.g., Tech-Savvy Renovators")
                age_range = st.text_input("Age Range*", placeholder="e.g., 30-50")
                income_level = st.selectbox("Income Level", 
                                          ["Low (< €30k)", "Medium (€30k-60k)", "Medium-High (€60k-100k)", 
                                           "High (€100k+)", "Business/Corporate", "Varied"])
                location = st.text_input("Geographic Location", placeholder="e.g., Urban Germany, Suburban areas")
            
            with col2:
                lifestyle = st.text_area("Lifestyle & Characteristics", 
                                       placeholder="Describe their lifestyle, values, and characteristics...")
                tech_comfort = st.selectbox("Technology Comfort", ["Low", "Medium", "High", "Varied"])
                renovation_experience = st.selectbox("Renovation Experience", 
                                                   ["None", "Limited", "Some", "Extensive", "Professional", "Varied"])
            
            motivations = st.text_area("Key Motivations (one per line)", 
                                     placeholder="Quality\nInnovation\nValue for money\nConvenience")
            segment_description = st.text_area("Segment Description*", 
                                             placeholder="Detailed description of this demographic segment...")
            
            persona_count = st.slider("Number of Personas to Generate", min_value=3, max_value=8, value=5,
                                    help="How many representative personas should AI create for this demographic?")
            
            if st.form_submit_button("🤖 Create Demographics & Generate Personas", type="primary"):
                if segment_name and age_range and segment_description:
                    motivations_list = [m.strip() for m in motivations.split('\n') if m.strip()] if motivations else []
                    
                    custom_demographics = {
                        'segment_name': segment_name,
                        'age_range': age_range,
                        'income_level': income_level,
                        'location': location,
                        'lifestyle': lifestyle,
                        'tech_comfort': tech_comfort,
                        'renovation_experience': renovation_experience,
                        'key_motivations': motivations_list,
                        'segment_description': segment_description,
                        'persona_count': persona_count
                    }
                    
                    st.session_state.target_demographics = custom_demographics
                    st.success(f"✅ Custom demographics '{segment_name}' created!")
                    # Auto-generate personas
                    generate_personas_for_demographic(custom_demographics, segment_name)
                    st.rerun()
                else:
                    st.error("Please fill in all required fields marked with *")
    
    # Show current demographics and assembled personas
    if st.session_state.target_demographics:
        st.markdown("### ✅ Current Target Demographics")
        demographics = st.session_state.target_demographics
        
        st.success(f"👥 **{demographics.get('segment_name', 'Custom Segment')}**")
        
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Age Range:** {demographics.get('age_range', 'Not specified')}")
            st.write(f"**Income Level:** {demographics.get('income_level', 'Not specified')}")
            st.write(f"**Location:** {demographics.get('location', 'Not specified')}")
            st.write(f"**Tech Comfort:** {demographics.get('tech_comfort', 'Not specified')}")
        with col2:
            st.write(f"**Lifestyle:** {demographics.get('lifestyle', 'Not specified')}")
            st.write(f"**Experience:** {demographics.get('renovation_experience', 'Not specified')}")
            if demographics.get('key_motivations'):
                st.write(f"**Key Motivations:** {', '.join(demographics['key_motivations'])}")
        
        st.write("**Segment Description:**")
        st.write(demographics.get('segment_description', 'No description provided'))
        
        # Show assembled personas
        if st.session_state.assembled_personas:
            st.markdown("### 🤖 AI-Assembled Personas")
            st.info(f"Generated {len(st.session_state.assembled_personas)} representative personas for this demographic segment:")
            
            persona_cols = st.columns(min(3, len(st.session_state.assembled_personas)))
            
            for i, persona in enumerate(st.session_state.assembled_personas):
                col = persona_cols[i % len(persona_cols)]
                
                with col:
                    with st.expander(f"👤 {persona.get('name', 'Persona')} ({persona.get('age', '?')})", expanded=False):
                        st.write(f"**Job:** {persona.get('job', 'Not specified')}")
                        st.write(f"**Company:** {persona.get('company', 'Not specified')}")
                        st.write("**Background:**")
                        experience = persona.get('experience', 'No background provided')
                        if isinstance(experience, str):
                            st.write(experience[:200] + ("..." if len(experience) > 200 else ""))
                        else:
                            st.write(str(experience)[:200] + "...")
                        
                        st.write("**Key Concerns:**")
                        pain_points = persona.get('pain_points', 'No concerns listed')
                        if isinstance(pain_points, str):
                            st.write(pain_points[:150] + ("..." if len(pain_points) > 150 else ""))
                        elif isinstance(pain_points, list):
                            st.write('; '.join(pain_points)[:150] + ("..." if len('; '.join(pain_points)) > 150 else ""))
                        else:
                            st.write(str(pain_points)[:150] + "...")
            
            # Regenerate personas button
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                if st.button("🔄 Regenerate Personas", use_container_width=True):
                    generate_personas_for_demographic(demographics, demographics.get('segment_name', 'Custom'))
                    st.rerun()
        
        # Navigation buttons
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 1, 1])
        with col3:
            if st.session_state.assembled_personas:
                if st.button("➡️ Continue to Step 1: Define Product", type="primary", use_container_width=True):
                    st.session_state.flow_completed[0] = True
                    st.session_state.current_step = 1
                    st.rerun()
            else:
                st.button("➡️ Generate personas first", disabled=True, use_container_width=True)

def generate_personas_for_demographic(demographics: Dict, segment_name: str):
    """Generate representative personas based on demographic data using AI"""
    if not OPENAI_AVAILABLE:
        st.error("OpenAI API not available. Using fallback personas.")
        # Use fallback personas from existing examples
        fallback_personas = list(EXAMPLE_PERSONAS.values())[:demographics.get('persona_count', 5)]
        st.session_state.assembled_personas = fallback_personas
        return
    
    try:
        with st.spinner(f"🤖 Assembling {demographics.get('persona_count', 5)} representative personas for {segment_name}..."):
            client = openai.OpenAI(api_key=OPENAI_API_KEY)
            
            personas = []
            persona_count = demographics.get('persona_count', 5)
            
            for i in range(persona_count):
                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": f"""You are a persona generator for user research. Create realistic, diverse personas that represent the target demographic segment.

TARGET DEMOGRAPHIC SEGMENT: {segment_name}
- Age Range: {demographics.get('age_range', 'Not specified')}
- Income Level: {demographics.get('income_level', 'Not specified')}
- Location: {demographics.get('location', 'Not specified')}
- Lifestyle: {demographics.get('lifestyle', 'Not specified')}
- Tech Comfort: {demographics.get('tech_comfort', 'Not specified')}
- Renovation Experience: {demographics.get('renovation_experience', 'Not specified')}
- Key Motivations: {', '.join(demographics.get('key_motivations', []))}
- Segment Description: {demographics.get('segment_description', 'Not specified')}

Generate a JSON object with these exact fields (all values must be STRINGS):
- name: Full German name appropriate for the demographic (STRING)
- age: Specific age within the range (NUMBER as INTEGER)
- job: Job title that fits the income/lifestyle profile (STRING)
- company: Company description that matches the profile (STRING)  
- experience: Background with bathroom products/renovations fitting their experience level (STRING - paragraph format)
- pain_points: Current challenges and frustrations relevant to this demographic (STRING - paragraph format, not a list)
- goals: What they want to achieve, aligned with key motivations (STRING - paragraph format)
- personality: Communication style and decision-making approach fitting the segment (STRING - paragraph format)

IMPORTANT: All fields except 'age' must be strings. Do not use arrays/lists for any field. Write pain_points, goals, etc. as coherent paragraphs.

Make each persona unique while staying within the demographic parameters. Focus on realistic German customers that truly represent this segment."""},
                        {"role": "user", "content": f"Generate persona {i+1} of {persona_count} for the {segment_name} demographic segment. Make it distinct from previous personas while staying within the demographic parameters."}
                    ],
                    max_tokens=800,
                    temperature=0.8
                )
                
                persona_text = response.choices[0].message.content.strip()
                # Extract JSON from response if wrapped in markdown
                if "```json" in persona_text:
                    persona_text = persona_text.split("```json")[1].split("```")[0]
                elif "```" in persona_text:
                    persona_text = persona_text.split("```")[1]
                
                import json
                try:
                    persona = json.loads(persona_text)
                    # Ensure all fields are proper types
                    if isinstance(persona.get('pain_points'), list):
                        persona['pain_points'] = '; '.join(persona['pain_points'])
                    if isinstance(persona.get('goals'), list):
                        persona['goals'] = '; '.join(persona['goals'])
                    if isinstance(persona.get('experience'), list):
                        persona['experience'] = '; '.join(persona['experience'])
                    personas.append(persona)
                except json.JSONDecodeError as e:
                    st.warning(f"Failed to parse persona {i+1}, using fallback")
                    # Use a fallback persona from examples
                    if EXAMPLE_PERSONAS:
                        fallback_persona = list(EXAMPLE_PERSONAS.values())[i % len(EXAMPLE_PERSONAS)]
                        personas.append(fallback_persona)
            
            st.session_state.assembled_personas = personas
            st.success(f"✅ Successfully generated {len(personas)} personas for {segment_name}!")
            
    except Exception as e:
        st.error(f"Error generating personas: {str(e)}")
        # Fallback to example personas
        fallback_personas = list(EXAMPLE_PERSONAS.values())[:demographics.get('persona_count', 5)]
        st.session_state.assembled_personas = fallback_personas

def render_step1_define_product():
    """Step 1: Define Product for Autonomous Research"""
    st.markdown("## Step 1: Define Product to Test 🚀")
    st.markdown("Define the product you want to test with autonomous AI-generated interviews. The system will create diverse personas and conduct interviews automatically.")
    
    # Option 1: Quick Products
    st.markdown("### 🚀 Quick Product Templates")
    st.markdown("Select from pre-defined zero360 products:")
    
    DEFAULT_PRODUCTS = {
        "🏠 FlexSpace System": {
            "name": "zero360 FlexSpace System",
            "description": "Modulares Duschsystem mit magnetischer Wandschiene, das sich an verändernde Lebenssituationen anpasst. Komponenten können werkzeuglos angebracht werden - von Handbrausen auf Kinderhöhe bis zu Duschsitzen mit Haltegriffen.",
            "value_prop": "Maximale Flexibilität durch modularen Aufbau. Passt sich an alle Lebensphasen an - von der ersten Wohnung bis zum altersgerechten Bad.",
            "target_market": "Mieter, junge Familien, Menschen in Veränderungsphasen",
            "key_features": ["Magnetische Wandschiene", "Werkzeuglose Montage", "Modulare Komponenten", "Höhenverstellbar"]
        },
        "🤖 AIR System": {
            "name": "zero360 AIR (Adaptive Intelligent Room)",
            "description": "Intelligentes Badezimmersystem mit dezenten Sensoren in den Armaturen. Erfasst Nutzungsmuster, analysiert Wasserqualität in Echtzeit und optimiert selbstständig.",
            "value_prop": "KI-gesteuerte Optimierung des gesamten Badezimmers. Automatische Anpassung an Nutzergewohnheiten, präventive Wartung und professionelle Datenanalyse.",
            "target_market": "Luxussegment, Hotels, technikaffine Haushalte",
            "key_features": ["KI-gesteuerte Optimierung", "Echtzeitanalyse", "Präventive Wartung", "Personalisierte Einstellungen"]
        },
        "🔗 Connect Hub": {
            "name": "zero360 Connect Hub",
            "description": "Zentrale Steuereinheit, die alle Wasseranwendungen im Haus intelligent vernetzt. Überwacht Verbrauch, erkennt Leckagen und optimiert Wassertemperatur.",
            "value_prop": "Ein Gerät revolutioniert das gesamte Wassermanagement. Intelligente Vernetzung aller Geräte mit präventiver Wartung.",
            "target_market": "Hausmodernisierer, Smart Home Enthusiasten",
            "key_features": ["Zentrale Steuerung", "Leckage-Erkennung", "Verbrauchsoptimierung", "Smart Home Integration"]
        },
        "🌱 PureFlow System": {
            "name": "zero360 PureFlow System",
            "description": "Revolutionäres Dreifachsystem für nachhaltiges Wassermanagement mit Recycling. Filtert, reinigt und bereitet Wasser für verschiedene Anwendungen auf.",
            "value_prop": "Nachhaltigkeit ohne Verzicht. Massive Kosteneinsparungen bei reduziertem CO2-Fußabdruck.",
            "target_market": "Umweltbewusste Familien, Nachhaltigkeits-orientierte Haushalte",
            "key_features": ["Wasser-Recycling", "Dreifach-Filtersystem", "CO2-Reduktion", "Kosteneinsparung"]
        }
    }
    
    # Display products in grid
    product_cols = st.columns(2)
    products_list = list(DEFAULT_PRODUCTS.items())
    
    for i, (emoji_name, product_data) in enumerate(products_list):
        col = product_cols[i % 2]
        
        with col:
            with st.container():
                st.markdown(f"**{emoji_name}**")
                st.markdown(f"**{product_data['name']}**")
                st.markdown(f"{product_data['value_prop']}")
                st.markdown(f"_Target: {product_data['target_market']}_")
                
                if st.button(f"Select {emoji_name}", key=f"prod_select_{i}", use_container_width=True):
                    st.session_state.current_product = product_data.copy()
                    st.session_state.flow_completed[0] = True
                    st.success(f"✅ {product_data['name']} selected!")
                    st.balloons()
                    st.rerun()
    
    # Option 2: Custom Product
    st.markdown("### ✏️ Or Define Custom Product")
    
    with st.expander("🎨 Create Custom Product", expanded=False):
        with st.form("custom_product_form"):
            st.markdown("Define your own product or concept for autonomous testing:")
            
            col1, col2 = st.columns(2)
            
            with col1:
                product_name = st.text_input("Product Name*", placeholder="e.g., zero360 SmartFlow Pro")
                product_category = st.selectbox("Category", 
                                              ["Shower System", "Faucet/Tap", "Smart Home", "Water Management", "Accessories", "Other"])
                target_market = st.text_input("Target Market*", placeholder="e.g., Premium homeowners, Hotels")
            
            with col2:
                product_description = st.text_area("Product Description*", 
                                                 placeholder="Describe what the product does, how it works, key technologies...")
                value_proposition = st.text_area("Value Proposition*", 
                                                placeholder="What's the main benefit? Why should customers choose this?")
            
            key_features = st.text_area("Key Features (one per line)", 
                                      placeholder="Feature 1\nFeature 2\nFeature 3...")
            price_range = st.selectbox("Price Range", 
                                     ["Budget (< 500€)", "Mid-range (500-2000€)", "Premium (2000-5000€)", "Luxury (> 5000€)", "Not defined"])
            
            if st.form_submit_button("🚀 Create Product", type="primary"):
                if product_name and product_description and value_proposition and target_market:
                    features_list = [f.strip() for f in key_features.split('\n') if f.strip()] if key_features else []
                    
                    custom_product = {
                        'name': product_name,
                        'category': product_category,
                        'description': product_description,
                        'value_prop': value_proposition,
                        'target_market': target_market,
                        'key_features': features_list,
                        'price_range': price_range
                    }
                    
                    st.session_state.current_product = custom_product
                    st.session_state.flow_completed[0] = True
                    st.success(f"✅ Custom product '{product_name}' created successfully!")
                    st.balloons()
                    st.rerun()
                else:
                    st.error("Please fill in all required fields marked with *")
    
    # Show current selection
    if st.session_state.current_product:
        st.markdown("### ✅ Current Product")
        product = st.session_state.current_product
        
        st.success(f"🚀 **{product.get('name', 'Unnamed Product')}**")
        
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Target Market:** {product.get('target_market', 'Not defined')}")
            st.write(f"**Category:** {product.get('category', 'Not specified')}")
        with col2:
            st.write("**Value Proposition:**")
            st.write(product.get('value_prop', 'No value proposition defined')[:150] + "...")
        
        st.write("**Description:**")
        st.write(product.get('description', 'No description provided')[:200] + "...")
        
        # Navigation buttons
        col1, col2, col3 = st.columns([1, 1, 1])
        with col3:
            if st.button("➡️ Continue to Step 2: Generate Interviews", type="primary", use_container_width=True):
                st.session_state.current_step = 2
                st.rerun()

def render_step2_generate_interviews():
    """Step 2: Generate Autonomous Interviews"""
    st.markdown("## Step 2: Generate Autonomous Interviews 🤖")
    st.markdown("Generate and run up to 10 autonomous interviews with AI-created personas. Each interview will test your product with different user types.")
    
    # Check prerequisites
    if not st.session_state.target_demographics:
        st.error("⚠️ Please complete Step 0 first - define target demographics.")
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button("⬅️ Back to Step 0", use_container_width=True, type="primary"):
                st.session_state.current_step = 0
                st.rerun()
        return
    
    if not st.session_state.current_product:
        st.error("⚠️ Please complete Step 1 first - define a product to test.")
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button("⬅️ Back to Step 1", use_container_width=True, type="primary"):
                st.session_state.current_step = 1
                st.rerun()
        return
    
    product = st.session_state.current_product
    st.info(f"🚀 **Testing Product:** {product.get('name', 'Unnamed Product')}")
    
    # Interview Configuration
    st.markdown("### ⚙️ Interview Configuration")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        num_interviews = st.slider(
            "Number of Interviews", 
            min_value=1, 
            max_value=10, 
            value=min(5, st.session_state.max_interviews),
            help="How many autonomous interviews to generate"
        )
    
    with col2:
        questions_per_interview = st.slider(
            "Questions per Interview", 
            min_value=5, 
            max_value=15, 
            value=8,
            help="Number of questions in each interview"
        )
    
    with col3:
        interview_focus = st.selectbox(
            "Interview Focus",
            ["Balanced", "Pain Points", "Value Proposition", "Pricing", "Features", "Competition"],
            help="What aspect should the interviews focus on?"
        )
    
    # Current Status
    st.markdown("### 📊 Current Status")
    
    completed_interviews = len([i for i in st.session_state.autonomous_interviews if i['status'] == 'completed'])
    running_interviews = len([i for i in st.session_state.autonomous_interviews if i['status'] == 'running'])
    
    status_col1, status_col2, status_col3 = st.columns(3)
    
    with status_col1:
        st.metric("Completed", completed_interviews)
    with status_col2:
        st.metric("Running", running_interviews)
    with status_col3:
        st.metric("Remaining", max(0, num_interviews - len(st.session_state.autonomous_interviews)))
    
    # Generation Controls
    st.markdown("### 🎬 Interview Generation")
    
    # Check if we can generate more interviews
    can_generate = len(st.session_state.autonomous_interviews) < num_interviews and not st.session_state.research_active
    
    if can_generate:
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🚀 Generate Single Interview", use_container_width=True):
                generate_single_interview(product, questions_per_interview, interview_focus)
        
        with col2:
            if st.button("🤖 Generate All Interviews", use_container_width=True, type="primary"):
                generate_all_interviews(product, num_interviews, questions_per_interview, interview_focus)
    else:
        if st.session_state.research_active:
            st.warning("🔄 Research is currently running...")
            if st.button("⏹️ Stop Research", use_container_width=True):
                st.session_state.research_active = False
                st.rerun()
        else:
            st.info("✅ Maximum number of interviews reached or research completed.")
    
    # Interview Results Preview
    if st.session_state.autonomous_interviews:
        st.markdown("### 📋 Interview Results Preview")
        
        for i, interview in enumerate(st.session_state.autonomous_interviews[-3:]):  # Show last 3
            with st.expander(f"Interview {interview['id']} - {interview['persona']['name']} ({interview['status']})", expanded=False):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Persona:** {interview['persona']['name']}")
                    st.write(f"**Job:** {interview['persona']['job']}")
                    st.write(f"**Age:** {interview['persona']['age']}")
                
                with col2:
                    if interview['status'] == 'completed':
                        metrics = interview['metrics']
                        st.write(f"**Sentiment:** {metrics['sentiment_score']:.1%}")
                        st.write(f"**Conviction:** {metrics['conviction_level']:.1%}")
                        st.write(f"**Concerns:** {len(metrics['main_concerns'])}")
                    else:
                        st.write("**Status:** In progress...")
                
                if interview['status'] == 'completed' and interview['conversation']:
                    st.write("**Sample Response:**")
                    first_response = next((msg['content'] for msg in interview['conversation'] if msg['role'] == 'assistant'), "No response yet")
                    st.write(f"_{first_response[:200]}..._")
    
    # Navigation
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("⬅️ Back to Step 1", use_container_width=True):
            st.session_state.current_step = 1
            st.rerun()
    
    with col3:
        # Only allow proceeding if we have at least one completed interview
        if completed_interviews > 0:
            if st.button("➡️ Continue to Step 3: Analyze", type="primary", use_container_width=True):
                st.session_state.current_step = 3
                st.session_state.flow_completed[1] = True
                st.rerun()
        else:
            st.button("➡️ Generate interviews first", disabled=True, use_container_width=True)

def generate_single_interview(product: Dict, num_questions: int, focus: str):
    """Generate and run a single autonomous interview"""
    if not OPENAI_AVAILABLE:
        st.error("OpenAI API not available. Please check your API key configuration.")
        return
    
    st.session_state.research_active = True
    
    # Show progress
    progress_placeholder = st.empty()
    status_placeholder = st.empty()
    
    try:
        with status_placeholder.container():
            st.info("🤖 Generating persona...")
        
        # Use assembled persona if available, otherwise generate diverse persona
        if st.session_state.assembled_personas:
            # Select a random persona from the assembled ones
            import random
            persona = random.choice(st.session_state.assembled_personas)
        else:
            # Fallback to generating diverse persona
            persona = generate_diverse_persona()
        
        with status_placeholder.container():
            st.info(f"👤 Created persona: {persona.get('name', 'Unknown')}")
            st.info("❓ Generating interview questions...")
        
        # Generate questions
        questions = generate_interview_questions(persona, product, num_questions)
        
        with status_placeholder.container():
            st.info(f"💬 Conducting interview with {len(questions)} questions...")
        
        # Set up progress tracking
        st.session_state.progress_placeholder = progress_placeholder
        
        # Conduct interview
        interview_data = conduct_autonomous_interview(persona, product, questions)
        
        # Add to session state
        st.session_state.autonomous_interviews.append(interview_data)
        st.session_state.interviews_completed += 1
        
        with status_placeholder.container():
            st.success(f"✅ Interview completed with {persona.get('name', 'Unknown')}!")
            st.balloons()
        
    except Exception as e:
        with status_placeholder.container():
            st.error(f"❌ Error generating interview: {str(e)}")
    
    finally:
        st.session_state.research_active = False
        progress_placeholder.empty()
        # Keep status for a moment, then clear
        import time
        time.sleep(2)
        status_placeholder.empty()
        st.rerun()

def generate_all_interviews(product: Dict, num_interviews: int, questions_per_interview: int, focus: str):
    """Generate all remaining interviews"""
    if not OPENAI_AVAILABLE:
        st.error("OpenAI API not available. Please check your API key configuration.")
        return
    
    st.session_state.research_active = True
    
    # Calculate how many we need to generate
    current_count = len(st.session_state.autonomous_interviews)
    remaining = num_interviews - current_count
    
    # Show overall progress
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        for i in range(remaining):
            current_progress = i / remaining
            progress_bar.progress(current_progress, f"Generating interview {i+1}/{remaining}")
            
            with status_text.container():
                st.info(f"🤖 Generating interview {current_count + i + 1}...")
            
            # Use assembled persona if available, otherwise generate diverse persona
            if st.session_state.assembled_personas and i < len(st.session_state.assembled_personas):
                # Use specific persona from assembled list
                persona = st.session_state.assembled_personas[i]
            elif st.session_state.assembled_personas:
                # If we have more interviews than personas, cycle through them
                import random
                persona = random.choice(st.session_state.assembled_personas)
            else:
                # Fallback to generating diverse persona
                persona = generate_diverse_persona()
            
            with status_text.container():
                st.info(f"👤 Interview {current_count + i + 1}: {persona.get('name', 'Unknown')}")
            
            # Generate questions
            questions = generate_interview_questions(persona, product, questions_per_interview)
            
            # Conduct interview
            interview_data = conduct_autonomous_interview(persona, product, questions)
            
            # Add to session state
            st.session_state.autonomous_interviews.append(interview_data)
            st.session_state.interviews_completed += 1
        
        # Final progress
        progress_bar.progress(1.0, f"✅ Generated {remaining} interviews successfully!")
        
        with status_text.container():
            st.success(f"🎉 All {remaining} interviews completed!")
            st.balloons()
        
    except Exception as e:
        with status_text.container():
            st.error(f"❌ Error during batch generation: {str(e)}")
    
    finally:
        st.session_state.research_active = False
        # Clean up UI elements
        import time
        time.sleep(3)
        progress_bar.empty()
        status_text.empty()
        st.rerun()

def render_step3_analyze_results():
    """Step 3: Analyze Autonomous Interview Results"""
    st.markdown("## Step 3: Analyze Interview Results 📊")
    st.markdown("Analyze and compare results from your autonomous interviews to gain comprehensive insights about your product.")
    
    # Check if we have any interviews
    if not st.session_state.autonomous_interviews:
        st.error("⚠️ No interviews found. Please complete Step 2 first.")
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button("⬅️ Back to Step 2", use_container_width=True, type="primary"):
                st.session_state.current_step = 2
                st.rerun()
        return
    
    # Filter completed interviews
    completed_interviews = [i for i in st.session_state.autonomous_interviews if i['status'] == 'completed']
    
    if not completed_interviews:
        st.warning("⚠️ No completed interviews yet. Please wait for interviews to finish or go back to Step 2.")
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button("⬅️ Back to Step 2", use_container_width=True, type="primary"):
                st.session_state.current_step = 2
                st.rerun()
        return
    
    # Overall Summary
    st.markdown("### 📋 Research Summary")
    
    product = st.session_state.current_product
    st.info(f"🚀 **Product Tested:** {product.get('name', 'Unnamed Product')}")
    
    summary_col1, summary_col2, summary_col3, summary_col4 = st.columns(4)
    
    with summary_col1:
        st.metric("Total Interviews", len(completed_interviews))
    with summary_col2:
        avg_sentiment = sum(i['metrics']['sentiment_score'] for i in completed_interviews) / len(completed_interviews)
        st.metric("Avg Sentiment", f"{avg_sentiment:.1%}")
    with summary_col3:
        avg_conviction = sum(i['metrics']['conviction_level'] for i in completed_interviews) / len(completed_interviews)
        st.metric("Avg Purchase Intent", f"{avg_conviction:.1%}")
    with summary_col4:
        all_concerns = []
        for i in completed_interviews:
            all_concerns.extend(i['metrics']['main_concerns'])
        unique_concerns = len(set(all_concerns))
        st.metric("Unique Concerns", unique_concerns)
    
    # Detailed Analytics
    st.markdown("### 📈 Detailed Analytics")
    
    # Create tabs for different analysis views
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "👥 Personas", "💬 Conversations", "📄 Export"])
    
    with tab1:
        render_overview_analysis(completed_interviews)
    
    with tab2:
        render_persona_analysis(completed_interviews)
    
    with tab3:
        render_conversation_analysis(completed_interviews)
    
    with tab4:
        render_export_analysis(completed_interviews, product)
    
    # Navigation
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("⬅️ Back to Step 2", use_container_width=True):
            st.session_state.current_step = 2
            st.rerun()
    
    with col2:
        if st.button("🔄 Start New Research", use_container_width=True, type="primary"):
            # Reset for new research
            st.session_state.autonomous_interviews = []
            st.session_state.current_product = {}
            st.session_state.target_demographics = {}
            st.session_state.assembled_personas = []
            st.session_state.research_active = False
            st.session_state.interviews_completed = 0
            st.session_state.current_step = 0
            st.session_state.flow_completed = [False, False, False, False]
            st.rerun()
    
    with col3:
        st.session_state.flow_completed[3] = True  # Mark step 3 as completed

# Analysis Helper Functions
def render_overview_analysis(completed_interviews):
    """Render overview analysis tab"""
    st.markdown("#### 🎯 Key Insights")
    
    # Calculate insights
    sentiments = [i['metrics']['sentiment_score'] for i in completed_interviews]
    convictions = [i['metrics']['conviction_level'] for i in completed_interviews]
    
    avg_sentiment = sum(sentiments) / len(sentiments)
    avg_conviction = sum(convictions) / len(convictions)
    
    # Sentiment distribution
    positive_count = len([s for s in sentiments if s > 0.6])
    neutral_count = len([s for s in sentiments if 0.4 <= s <= 0.6])
    negative_count = len([s for s in sentiments if s < 0.4])
    
    # Display insights
    insights = []
    if avg_sentiment > 0.7:
        insights.append("✅ **Very Positive Reception** - Strong overall sentiment across interviews")
    elif avg_sentiment < 0.3:
        insights.append("⚠️ **Negative Reception** - Significant concerns raised across interviews")
    else:
        insights.append("🤔 **Mixed Reception** - Varied opinions across different personas")
    
    if avg_conviction > 0.8:
        insights.append("🎯 **High Purchase Intent** - Strong buying signals from most personas")
    elif avg_conviction < 0.3:
        insights.append("📈 **Low Purchase Intent** - Need to strengthen value proposition")
    
    if positive_count > len(completed_interviews) * 0.7:
        insights.append("🌟 **Broad Appeal** - Product resonates with diverse audience")
    
    for insight in insights:
        st.markdown(f"- {insight}")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 😊 Sentiment Distribution")
        sentiment_data = pd.DataFrame({
            'Sentiment': ['Positive', 'Neutral', 'Negative'],
            'Count': [positive_count, neutral_count, negative_count]
        })
        fig = px.pie(sentiment_data, values='Count', names='Sentiment', 
                    color_discrete_map={'Positive': '#10b981', 'Neutral': '#6b7280', 'Negative': '#ef4444'})
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("#### 📊 Interview Metrics")
        metrics_data = pd.DataFrame({
            'Interview': [f"Interview {i+1}" for i in range(len(completed_interviews))],
            'Sentiment': sentiments,
            'Conviction': convictions
        })
        fig = px.scatter(metrics_data, x='Sentiment', y='Conviction', hover_name='Interview',
                        title="Sentiment vs Purchase Intent")
        fig.add_hline(y=0.5, line_dash="dash", line_color="gray", annotation_text="Medium Conviction")
        fig.add_vline(x=0.5, line_dash="dash", line_color="gray", annotation_text="Neutral Sentiment")
        st.plotly_chart(fig, use_container_width=True)

def render_persona_analysis(completed_interviews):
    """Render persona analysis tab"""
    st.markdown("#### 👥 Persona Breakdown")
    
    # Group by job/persona type
    persona_groups = {}
    for interview in completed_interviews:
        job = interview['persona']['job']
        if job not in persona_groups:
            persona_groups[job] = []
        persona_groups[job].append(interview)
    
    # Display each persona group
    for job, interviews in persona_groups.items():
        with st.expander(f"{job} ({len(interviews)} interview{'s' if len(interviews) > 1 else ''})", expanded=True):
            for interview in interviews:
                persona = interview['persona']
                metrics = interview['metrics']
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write(f"**{persona['name']}**")
                    st.write(f"Age: {persona['age']}")
                    st.write(f"Company: {persona.get('company', 'N/A')}")
                
                with col2:
                    st.write(f"**Sentiment:** {metrics['sentiment_score']:.1%}")
                    st.write(f"**Conviction:** {metrics['conviction_level']:.1%}")
                    st.write(f"**Concerns:** {len(metrics['main_concerns'])}")
                
                with col3:
                    if metrics['main_concerns']:
                        st.write("**Key Concerns:**")
                        for concern in metrics['main_concerns'][:3]:
                            st.write(f"• {concern}")
                    else:
                        st.write("**No major concerns**")
                
                # Sample quote
                if interview['conversation']:
                    first_response = next((msg['content'] for msg in interview['conversation'] if msg['role'] == 'assistant'), "")
                    if first_response:
                        st.write(f"💬 *\"{first_response[:150]}...\"*")
                
                st.markdown("---")

def render_conversation_analysis(completed_interviews):
    """Render conversation analysis tab"""
    st.markdown("#### 💬 Conversation Insights")
    
    # Select interview to view
    interview_options = [f"{i['persona']['name']} - {i['persona']['job']}" for i in completed_interviews]
    selected_idx = st.selectbox("Select Interview to View:", range(len(interview_options)), 
                               format_func=lambda x: interview_options[x])
    
    selected_interview = completed_interviews[selected_idx]
    
    # Display interview details
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("##### 👤 Persona Details")
        persona = selected_interview['persona']
        st.write(f"**Name:** {persona['name']}")
        st.write(f"**Age:** {persona['age']}")
        st.write(f"**Job:** {persona['job']}")
        st.write(f"**Company:** {persona.get('company', 'N/A')}")
    
    with col2:
        st.markdown("##### 📊 Interview Metrics")
        metrics = selected_interview['metrics']
        st.write(f"**Sentiment:** {metrics['sentiment_score']:.1%}")
        st.write(f"**Conviction:** {metrics['conviction_level']:.1%}")
        st.write(f"**Concerns:** {len(metrics['main_concerns'])}")
    
    # Display conversation
    st.markdown("##### 💬 Full Conversation")
    
    conversation = selected_interview['conversation']
    for i, message in enumerate(conversation):
        if message['role'] == 'user':
            st.chat_message("user").write(f"**Researcher:** {message['content']}")
        else:
            st.chat_message("assistant").write(f"**{persona['name']}:** {message['content']}")

def render_export_analysis(completed_interviews, product):
    """Render export analysis tab"""
    st.markdown("#### 📄 Export Research Results")
    st.markdown("Download your autonomous research results in various formats:")
    
    # Prepare comprehensive export data
    export_data = {
        'research_session': {
            'timestamp': datetime.now().isoformat(),
            'product': product,
            'total_interviews': len(completed_interviews)
        },
        'summary_metrics': {
            'avg_sentiment': sum(i['metrics']['sentiment_score'] for i in completed_interviews) / len(completed_interviews),
            'avg_conviction': sum(i['metrics']['conviction_level'] for i in completed_interviews) / len(completed_interviews),
            'sentiment_distribution': {
                'positive': len([i for i in completed_interviews if i['metrics']['sentiment_score'] > 0.6]),
                'neutral': len([i for i in completed_interviews if 0.4 <= i['metrics']['sentiment_score'] <= 0.6]),
                'negative': len([i for i in completed_interviews if i['metrics']['sentiment_score'] < 0.4])
            }
        },
        'interviews': [
            {
                'id': interview['id'],
                'persona': interview['persona'],
                'metrics': interview['metrics'],
                'conversation': [
                    {
                        'role': msg['role'],
                        'content': msg['content'],
                        'timestamp': msg['timestamp'].isoformat()
                    } for msg in interview['conversation']
                ]
            } for interview in completed_interviews
        ]
    }
    
    export_col1, export_col2, export_col3 = st.columns(3)
    
    with export_col1:
        # JSON Export
        json_data = json.dumps(export_data, indent=2, ensure_ascii=False)
        st.download_button(
            label="📄 Export Full Data (JSON)",
            data=json_data,
            file_name=f"autonomous_research_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True
        )
    
    with export_col2:
        # CSV Export (Summary)
        summary_data = []
        for interview in completed_interviews:
            summary_data.append({
                'Interview_ID': interview['id'],
                'Persona_Name': interview['persona']['name'],
                'Persona_Job': interview['persona']['job'],
                'Persona_Age': interview['persona']['age'],
                'Sentiment_Score': interview['metrics']['sentiment_score'],
                'Conviction_Level': interview['metrics']['conviction_level'],
                'Concerns_Count': len(interview['metrics']['main_concerns']),
                'Main_Concerns': '; '.join(interview['metrics']['main_concerns'])
            })
        
        df = pd.DataFrame(summary_data)
        csv_string = df.to_csv(index=False)
        
        st.download_button(
            label="📊 Export Summary (CSV)",
            data=csv_string,
            file_name=f"research_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with export_col3:
        # Report Export
        avg_sentiment = export_data['summary_metrics']['avg_sentiment']
        avg_conviction = export_data['summary_metrics']['avg_conviction']
        
        report = f"""
# Autonomous User Research Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Product Tested
**Name:** {product.get('name', 'Unknown')}
**Description:** {product.get('description', 'No description')}
**Target Market:** {product.get('target_market', 'Not specified')}

## Research Summary
- **Total Interviews:** {len(completed_interviews)}
- **Average Sentiment:** {avg_sentiment:.1%}
- **Average Purchase Intent:** {avg_conviction:.1%}

## Key Findings
### Sentiment Distribution
- Positive: {export_data['summary_metrics']['sentiment_distribution']['positive']} interviews
- Neutral: {export_data['summary_metrics']['sentiment_distribution']['neutral']} interviews  
- Negative: {export_data['summary_metrics']['sentiment_distribution']['negative']} interviews

### Recommendations
{"1. Leverage positive sentiment in marketing materials" if avg_sentiment > 0.6 else "1. Address negative feedback before market launch"}
{"2. Focus on conversion optimization" if avg_conviction > 0.7 else "2. Strengthen value proposition"}
3. Consider feedback from diverse persona types

## Interview Details
"""
        
        for interview in completed_interviews:
            report += f"""
### {interview['persona']['name']} - {interview['persona']['job']}
- **Sentiment:** {interview['metrics']['sentiment_score']:.1%}
- **Purchase Intent:** {interview['metrics']['conviction_level']:.1%}
- **Key Concerns:** {', '.join(interview['metrics']['main_concerns']) if interview['metrics']['main_concerns'] else 'None'}
"""
        
        st.download_button(
            label="📋 Export Report (MD)",
            data=report,
            file_name=f"research_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
            mime="text/markdown",
            use_container_width=True
        )

# Removed old step 4 function and analytics column - now using autonomous research analysis

# Main Application with Step-based Flow
def main():
    # Initialize session state
    initialize_session_state()
    
    # Render navigation bar
    render_nav_bar()
    
    # Render sidebar stats
    render_sidebar_stats()
    
    # Main content area - full width for step-based flow
    st.markdown('<div class="main-content-area">', unsafe_allow_html=True)
    render_main_content()
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()