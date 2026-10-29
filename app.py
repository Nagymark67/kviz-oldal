import streamlit as st
import random
import sqlite3
from pathlib import Path
from urllib.parse import quote

st.set_page_config(page_title="balekvizsgára", layout="centered")
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@500;600&display=swap');

    .stApp {
        font-family: 'DM Sans', sans-serif;
    }
    .stApp .block-container {
        max-width: 760px;
        padding-top: 2rem;
    }
    .stApp h1, .stApp h2, .stApp h3,
    .stApp [data-testid="stMarkdownContainer"],
    .stApp label {
        font-family: 'DM Sans', sans-serif;
    }
    .quiz-counter,
    [data-testid="stMetricValue"] {
        font-family: 'JetBrains Mono', monospace !important;
        font-variant-numeric: tabular-nums;
        color: #00ffaa;
    }
    @keyframes question-enter {
        from { opacity: 0; transform: translateX(24px); }
        to { opacity: 1; transform: translateX(0); }
    }
    [class*="st-key-question-slide-"] {
        box-sizing: border-box;
        width: 100%;
        max-width: 600px;
        margin: 0 auto;
        padding: 1.35rem 1.5rem;
        border: 1px solid rgba(0, 255, 170, 0.18);
        border-radius: 12px;
        background: rgba(18, 18, 18, 0.72);
        box-shadow: 0 0 30px rgba(0, 255, 170, 0.05);
        backdrop-filter: blur(10px);
        animation: question-enter 320ms cubic-bezier(0.2, 0.8, 0.2, 1) both;
    }
    [data-testid="stProgress"] > [role="progressbar"] {
        height: 0.65rem;
        overflow: hidden;
        border-radius: 999px;
        background: rgba(0, 255, 170, 0.1);
    }
    [data-testid="stProgressBarTrack"] {
        height: 100%;
        border-radius: inherit;
        background: transparent;
    }
    [data-testid="stProgressBarTrack"] > div {
        height: 100%;
        border-radius: inherit;
    }
    @keyframes answer-burst {
        0% { opacity: 0; transform: scale(0.96); }
        18% { opacity: 1; transform: scale(1); }
        100% { opacity: 0; transform: scale(1.06); }
    }
    .answer-burst {
        position: fixed;
        inset: 0;
        z-index: 9999;
        pointer-events: none;
        animation: answer-burst 760ms ease-out both;
    }
    .answer-burst--correct {
        background: radial-gradient(ellipse at 50% 45%, rgba(0, 255, 170, 0.32), rgba(0, 255, 170, 0.12) 36%, transparent 76%);
    }
    .answer-burst--wrong {
        background: radial-gradient(ellipse at 50% 45%, rgba(255, 55, 75, 0.3), rgba(255, 55, 75, 0.11) 36%, transparent 76%);
    }
    [class*="st-key-question-report-"] {
        margin: 0.15rem 0 0.35rem;
    }
    [class*="st-key-question-report-"] button {
        border-color: rgba(255, 180, 90, 0.8);
        color: #ffc078;
        width: 100%;
        min-height: 2.35rem;
        padding: 0.45rem 0.55rem;
        font-size: 0.76rem;
        line-height: 1.2;
        white-space: nowrap;
        overflow: visible;
    }
    [class*="st-key-question-report-"] button:hover:enabled {
        background-color: rgba(255, 180, 90, 0.12);
        color: #ffe0b2;
        box-shadow: 0 0 12px rgba(255, 180, 90, 0.25);
    }
    @media (prefers-reduced-motion: reduce) {
        [class*="st-key-question-slide-"], .answer-burst { animation: none; }
    }
    .stButton>button {
        border: 1px solid #00ffaa;
        color: #00ffaa;
        background-color: transparent;
        border-radius: 8px;
        padding: 0.8rem 1rem;
        font-family: 'DM Sans', sans-serif;
        font-weight: 600;
        text-transform: none;
        letter-spacing: 0;
        transition: all 0.2s ease-in-out;
    }
    .stButton>button:hover:enabled {
        background-color: rgba(0, 255, 170, 0.15);
        color: #e7fff7;
        box-shadow: 0 0 15px rgba(0, 255, 170, 0.32);
        transform: translateY(-1px);
    }
    [class*="st-key-answer-"] button {
        min-height: 3.5rem;
        padding: 0.9rem 1rem;
        line-height: 1.35;
        text-align: left;
        white-space: normal;
        justify-content: flex-start;
    }
    [class*="st-key-answer-"] button[kind="primary"],
    [class*="st-key-answer-"] button[kind="primary"]:disabled {
        border-color: #00ffaa;
        background-color: rgba(0, 255, 170, 0.15);
        color: #e7fff7;
        box-shadow: 0 0 16px rgba(0, 255, 170, 0.3), inset 0 0 12px rgba(0, 255, 170, 0.08);
        opacity: 1;
    }
    [class*="st-key-answer-choice-wrong-"] button[kind="secondary"],
    [class*="st-key-answer-choice-wrong-"] button[kind="secondary"]:disabled {
        border-color: #ff5267;
        background-color: rgba(255, 55, 75, 0.16);
        color: #fff0f2;
        box-shadow: 0 0 16px rgba(255, 55, 75, 0.3), inset 0 0 12px rgba(255, 55, 75, 0.08);
        opacity: 1;
    }
    #MainMenu, footer, header {visibility: hidden;}
    hr {border-color: #333333;}
</style>
""", unsafe_allow_html=True)

ALL_QUESTIONS = [
    # 1-15: Akadémiatörténet (Selmectől Sopronig)
    {
        "question": "Melyik napon adta ki III. Károly a Berg-Schola alapításáról szóló Instructiót?",
        "options": ["1735. június 22.", "1762. október 22.", "1770. április 1.", "1717. január 1."],
        "answer": "1735. június 22.",
        "explanation": "III. Károly 1735. június 22-én kelt rendeletében (Instructio) határozta meg a selmecbányai Berg-Schola működését."
    },
    {
        "question": "Hol indult meg az első bányászati tanintézeti oktatás 1717-ben négy hallgatóval, amely néhány év után megszűnt?",
        "options": ["Sankt Joachimsthal", "Freiberg", "Leoben", "Pribram"],
        "answer": "Sankt Joachimsthal",
        "explanation": "1717-ben a csehországi Sankt Joachimsthalban indult ilyen képzés, de hosszútávon életképtelennek bizonyult."
    },
    {
        "question": "Ki volt a Berg-Schola megszervezésével megbízott bányamérnök és első tanára?",
        "options": ["Mikoviny Sámuel", "Johann Peithner", "Nicolaus Jacquin", "Christof Traugott Delius"],
        "answer": "Mikoviny Sámuel",
        "explanation": "A kamara Mikoviny Sámuelt, az alsó-magyarországi bányavárosok bányamérnökét bízta meg a megszervezéssel."
    },
    {
        "question": "Hány évig tartott a tanulmányi idő a Berg-Scholában?",
        "options": ["2 év", "3 év", "4 év", "1 év"],
        "answer": "2 év",
        "explanation": "A tanulmányi idő a Berg-Scholában két év volt (január 1-től december 31-ig), téli elméleti és nyári gyakorlati oktatással."
    },
    {
        "question": "Melyik napon döntött Mária Terézia a Bányászati-Kohászati Akadémia létrehozásáról?",
        "options": ["1762. október 22.", "1735. június 22.", "1770. augusztus 15.", "1808. február 12."],
        "answer": "1762. október 22.",
        "explanation": "Johann Peithner javaslatára 1762. október 22-én döntöttek az akadémiai szintű képzés létrehozásáról."
    },
    {
        "question": "Ki volt az akadémia első tanszékének vezetője, aki 1764 szeptemberében kezdte meg előadásait a Krecsmáry-házban?",
        "options": ["Nicolaus Jacquin", "Nicolaus Poda", "Giovanni Antonio Scopoli", "Henrik David Wilckens"],
        "answer": "Nicolaus Jacquin",
        "explanation": "Az első tanszékre (Ásványtan-kémia-elméleti kohászat) Nicolaus Jacquint nevezték ki, aki honosította a kémiai laborgyakorlatot."
    },
    {
        "question": "Melyik évben adta ki Mária Terézia a 'Systema Academia Montanisticae' című tantervi utasítását, amellyel 3 évfolyamossá vált az oktatás?",
        "options": ["1770", "1762", "1808", "1846"],
        "answer": "1770",
        "explanation": "1770-ben került átszervezésre az oktatás a Systema Academia Montanisticae kiadásával."
    },
    {
        "question": "Melyik párizsi intézmény vette át a kémiaoktatás 'selmeci módszerét' (öntevékeny labormunka)?",
        "options": ["École Polytechnique", "Sorbonne", "École des Mines", "Collège de France"],
        "answer": "École Polytechnique",
        "explanation": "A világon elsőként Selmecbányán alkalmazott módszert 'selmeci módszerként' a párizsi École Polytechnique is átvette."
    },
    {
        "question": "Melyik évben hozták létre az Erdészeti Tanintézetet (Forstinstitut) Henrik David Wilckens vezetésével?",
        "options": ["1808", "1770", "1846", "1839"],
        "answer": "1808",
        "explanation": "1808-ban hozták létre az Erdészeti Tanintézetet, Wilckens első óráját 1809. február 12-én tartotta."
    },
    {
        "question": "Ki miatt robbantak ki a nemzeti ellentétek 1848 tavaszán, ami után ~133 külföldi hallgató elhagyta Selmecet?",
        "options": ["Jendrassik Miksa", "Christian Doppler", "Pettkó János", "Marschan József"],
        "answer": "Jendrassik Miksa",
        "explanation": "Jendrassik Miksa bányatanácsos az Aranybányamécs homlokzatán lévő zászlókra tett megjegyzése váltotta ki a viszályt."
    },
    {
        "question": "Melyik két városban szerveztek tanintézetet az 1848-ban Selmecről távozó osztrák és cseh-morva hallgatóknak?",
        "options": ["Leoben és Pribram", "Freiberg és Bécs", "Prága és Graz", "Joachimsthal és Körmöcbánya"],
        "answer": "Leoben és Pribram",
        "explanation": "A távozó hallgatók számára Leobenben és Pribramban szerveztek tanintézeteket, ezzel megszűnt Selmec birodalmi egyedülállósága."
    },
    {
        "question": "Melyik időszakban vezették be a magyar oktatási nyelvet a selmeci akadémián?",
        "options": ["1868 és 1872 között", "1848 és 1849 között", "1846 és 1850 között", "1904-ben"],
        "answer": "1868 és 1872 között",
        "explanation": "A kiegyezés után, 1868 és 1872 között vezették be a magyar oktatási nyelvet (az erdészeknél egyidejűleg 1868-ban)."
    },
    {
        "question": "Melyik évben vette fel az intézmény a 'Magyar Királyi Bányászati és Erdészeti Főiskola' nevet, amikortól vezetőjét rektori cím illette meg?",
        "options": ["1904", "1867", "1872", "1919"],
        "answer": "1904",
        "explanation": "1904-ben vette fel a főiskola nevet, választott vezetőjét ezután a rektori cím illette meg."
    },
    {
        "question": "Melyik napon hagyta el a hallgatók utolsó csoportja Selmecbányát a megszálló cseh csapatok elől?",
        "options": ["1918. december 14.", "1919. április 28.", "1918. november 11.", "1920. június 4."],
        "answer": "1918. december 14.",
        "explanation": "A hallgatók utolsó csoportja 1918. december 14-én hagyta el a várost, az oktatói gárda 1919 januárjában követte őket."
    },
    {
        "question": "Ki volt Sopron polgármestere, akinek nagy szerepe volt abban, hogy a főiskola 1919-ben Sopronba költözött?",
        "options": ["Dr. Thurner Mihály", "Winterstein Bernát", "Szechányi Elemér", "Machatsek Gyula"],
        "answer": "Dr. Thurner Mihály",
        "explanation": "Bár a tanári kar Gödöllőt támogatta, Dr. Thurner Mihály soproni polgármester közbenjárására Sopron lett az új otthon."
    },

    # 16-28: Sopron, Miskolc és utódintézmények
    {
        "question": "Kik haltak hősi halált a második ágfalvi csatában (1921. szeptember 8.) a nyugat-magyarországi felkelés során?",
        "options": ["Szechányi Elemér és Machatsek Gyula", "Kis Gábor és Kölber Gábor", "Ferenczy János és Neumann János", "Csaszlava Jenő és Ferenczy Sándor"],
        "answer": "Szechányi Elemér és Machatsek Gyula",
        "explanation": "A második ágfalvi csatában halt hősi halált Szechányi Elemér bányamérnök- és Machatsek Gyula erdőmérnök-hallgató."
    },
    {
        "question": "Mi történt 1945. március 30-án Brennbergbánya közelében?",
        "options": ["SS-katonák főiskolai tanárt és hallgatókat lőttek agyon", "Megkezdődött a soproni népszavazás", "Kimenekítették a könyvtárat Miskolcra", " megalakult az Ifjúsági Kör"],
        "answer": "SS-katonák főiskolai tanárt és hallgatókat lőttek agyon",
        "explanation": "SS-katonák agyonlőtték Ferenczy Sándor tanárt, Ferenczy János, Neumann János hallgatókat és Csaszlava Jenőnét (Csaszlava Jenő túlélte)."
    },
    {
        "question": "Melyik törvény rendelkezett a miskolci Nehézipari Műszaki Egyetem megalapításáról 1949. augusztus 19-én?",
        "options": ["1949. évi 23. törvény", "1952. évi 1. törvény", "1948. évi 15. törvény", "1934. évi 10. törvény"],
        "answer": "1949. évi 23. törvény",
        "explanation": "Az 1949. évi 23. törvény rendelkezett a Nehézipari Műszaki Egyetem miskolci létesítéséről."
    },
    {
        "question": "Mely évekre fejeződött be a kohász, illetve a bányász tanszékek teljes átköltözése Sopronból Miskolcra?",
        "options": ["Kohászok: 1952, Bányászok: 1959", "Kohászok: 1949, Bányászok: 1952", "Kohászok: 1955, Bányászok: 1962", "Mindkettő 1950-ben"],
        "answer": "Kohászok: 1952, Bányászok: 1959",
        "explanation": "A kohász tanszékek 1952-re, míg a bányászok csupán 1959-re költöztek át véglegesen Miskolcra."
    },
    {
        "question": "Kik vesztették életüket 1956. november 4-én, amikor a szovjet tankok lőni kezdték a miskolci E/1-es kollégiumot?",
        "options": ["Kis Gábor és Kölber Gábor", "Szechányi Elemér és Machatsek Gyula", "Ferenczy János és Neumann János", "Sályi István és Zambó János"],
        "answer": "Kis Gábor és Kölber Gábor",
        "explanation": "Az E/1-es kollégiumnál kibontakozó tűzharcban Kis Gábor elsőéves gépész- és Kölber Gábor elsőéves bányagépész-hallgató vesztette életét."
    },
    {
        "question": "Melyik évben vette fel a miskolci intézmény a 'Miskolci Egyetem' nevet?",
        "options": ["1990", "1981", "1989", "1997"],
        "answer": "1990",
        "explanation": "Az egyetem neve 1990-ben változott Nehézipari Műszaki Egyetemről Miskolci Egyetemre."
    },
    {
        "question": "Kinek a vezetésével kezdődött meg a miskolci Egyetemváros építése 1950-ben a Dudujka-völgyben?",
        "options": ["Janáky István", "Sályi István", "Terplán Zénó", "Zambó János"],
        "answer": "Janáky István",
        "explanation": "A ~82 hektáros campus építése 1950-ben kezdődött el Janáky István vezetésével."
    },
    {
        "question": "Mire utal a miskolci Egyetemvárosnak helyet adó 'Dudujka-völgy' elnevezése?",
        "options": ["Az UV-dombra, ami a helyieket női kebelre emlékeztette", "Egy középkori bányászszerszámra", "A Hejő-patak régi szláv nevére", "Egy 19. századi miskolci földbirtokosra"],
        "answer": "Az UV-dombra, ami a helyieket női kebelre emlékeztette",
        "explanation": "A völgy elnevezése a közepén álló UV-dombra utal, ami a helyieket női kebelre emlékeztette."
    },
    {
        "question": "Mikor esedékes a Miskolci Egyetem főbejárata mellé 2012-ben elhelyezett időkapszula felnyitása?",
        "options": ["2062. október 22.", "2035. június 22.", "2049. augusztus 19.", "2112. október 22."],
        "answer": "2062. október 22.",
        "explanation": "Az akadémiai rangra emelés 250. évfordulóján (2012) elhelyezett időkapszula felnyitása 2062. október 22-én esedékes."
    },
    {
        "question": "Melyik kanadai egyetemen hoztak létre erdőmérnöki képzést (Sopron Division) az 1956-ban emigrált soproni diákoknak?",
        "options": ["University of British Columbia (Vancouver)", "University of Toronto", "McGill University (Montreal)", "University of Alberta"],
        "answer": "University of British Columbia (Vancouver)",
        "explanation": "A Kanadába emigrált soproni hallgatók számára Vancouverben, a University of British Columbián hozták létre a Sopron Divisiont."
    },
    {
        "question": "Melyik évben csatolták a dunaújvárosi Felsőfokú Kohóipari Technikumot a Nehézipari Műszaki Egyetemhez főiskolai karként?",
        "options": ["1969", "1962", "1972", "2000"],
        "answer": "1969",
        "explanation": "Az 1962-ben alapított technikumot 1969-ben csatolták a NME-hez Kohó- és Fémipari Főiskola néven."
    },
    {
        "question": "Melyik egyetemhez tartozik 2014. július 1-je óta a Székesfehérvári GEO (Geoinformatikai Intézet)?",
        "options": ["Óbudai Egyetem", "Soproni Egyetem", "Miskolci Egyetem", "Budapesti Műszaki és Gazdaságtudományi Egyetem"],
        "answer": "Óbudai Egyetem",
        "explanation": "A kar 2014. július 1-én egyesült az Óbudai Egyetem Alba Regia Egyetemi Központjával."
    },
    {
        "question": "Melyik professzor volt Magyarországon az első kohómérnök, akit doktorrá avattak (1934), később pedig a miskolci Metallográfiai Tanszéket vezette?",
        "options": ["Verő József", "Cotel Ernő", "Geleji Sándor", "Faller Károly"],
        "answer": "Verő József",
        "explanation": "Verő József (1904-1985) volt az első kohómérnök Magyarországon, aki doktori fokozatot szerzett 1934-ben."
    },

    # 29-35: Jelentős professzorok
    {
        "question": "Ki alapította 1868-ban a Bányászati és Kohászati Lapokat (BKL) és szerkesztette meg az első magyar-német bányászati szótárt?",
        "options": ["Péch Antal", "Kerpely Antal", "Farbaky István", "Faller Gusztáv"],
        "answer": "Péch Antal",
        "explanation": "Péch Antal (1822-1895) alapította a BKL-t 1868-ban, és ő alkotta meg a 'Jó szerencsét!' köszöntést is 1879-ben."
    },
    {
        "question": "Ki alapította Divald Adolffal 1862-ben az Erdészeti Lapokat és alkotta meg az első erdészeti műszótárat?",
        "options": ["Wagner Károly", "Krippel Móricz", "Sébor János", "Henrik David Wilckens"],
        "answer": "Wagner Károly",
        "explanation": "Wagner Károly (1830-1879) Divald Adolffal alapította meg az Erdészeti Lapokat 1862-ben."
    },
    {
        "question": "Ki volt a Nehézipari Műszaki Egyetem Mechanika Tanszékének megszervezője és az egyetem rektora 1950 és 1961 között?",
        "options": ["Sályi István", "Terplán Zénó", "Zambó János", "Gyulay Zoltán"],
        "answer": "Sályi István",
        "explanation": "Sályi István (1901-1974) szervezte meg a Mechanika Tanszéket 1949-ben, majd 1950-től 1961-ig rektor volt."
    },
    {
        "question": "Ki volt a miskolci Gépészmérnöki Kar és a Gépelemek Tanszék egyik alapítója, aki 28 évesen lett tanszékvezető?",
        "options": ["Terplán Zénó", "Sályi István", "Geleji Sándor", "Szilas A. Pál"],
        "answer": "Terplán Zénó",
        "explanation": "Terplán Zénó (1921-2020) 28 évesen lett tanszékvezető, 31 évesen professzor, és a Gépelemek Tanszék alapítója."
    },
    {
        "question": "Ki volt a miskolci Állam- és Jogtudományi Kar első dékánja, akit 1980-ban miniszteri biztossá neveztek ki a jogászképzés megszervezésére?",
        "options": ["Kratochwill Ferenc", "Zambó János", "Finkey József", "Vitális István"],
        "answer": "Kratochwill Ferenc",
        "explanation": "Kratochwill Ferenc (1933-1993) szervezte meg a miskolci jogászképzést és lett az ÁJK első dékánja."
    },
    {
        "question": "Melyik professzor 1392 kötetből álló könyvgyűjteménye adta a Selmeci Akadémia könyvtárának alapját?",
        "options": ["Johann Peithner", "Giovanni Antonio Scopoli", "Nicolaus Jacquin", "Christian Doppler"],
        "answer": "Johann Peithner",
        "explanation": "Johann Peithner (1727-1792) 1392 kötetes gyűjteménye alapozta meg az akadémiai könyvtárat."
    },
    {
        "question": "Ki volt az első kohászati szakkönyv szerzője, aki az Ásványtan-kémia-elméleti kohászat Tanszék professzora volt Selmecen?",
        "options": ["Giovanni Antonio Scopoli", "Christof Traugott Delius", "Faller Károly", "Kerpely Antal"],
        "answer": "Giovanni Antonio Scopoli",
        "explanation": "Az olasz származású Giovanni Antonio Scopoli (1723-1788) volt az első kohászati szakkönyv szerzője."
    },

    # 36-50: Selmecbánya és Miskolc
    {
        "question": "Milyen néven említik legelőször Selmecbányát 1217-ben?",
        "options": ["Bana", "Schemnitz", "Sebenitz", "Štiavnica"],
        "answer": "Bana",
        "explanation": "A várost legelőször 1217-ben 'Bana' néven említik, utalva az ezüstbányászatra is."
    },
    {
        "question": "Melyik király emelte Selmecbányát szabad királyi bányavárosi rangra 1238-ban?",
        "options": ["IV. Béla", "Mátyás király", "Nagy Lajos", "III. Károly"],
        "answer": "IV. Béla",
        "explanation": "IV. Béla emelte szabad királyi bányavárosi rangra Selmecet 1238-ban."
    },
    {
        "question": "Meddig jutottak el a portyázó török csapatok Selmecbánya környékén?",
        "options": ["Csupán Kisiblyéig", "A Szélaknai-kapuig", "A Leányvárig", "Elfoglalták az Óvárat"],
        "answer": "Csupán Kisiblyéig",
        "explanation": "A török hódítások közvetlenül nem érintették a várost, a portyázók csupán Kisiblyéig jutottak."
    },
    {
        "question": "Hány stáció található a selmecbányai Kálvária-hegyen a három bevezető stáción felül?",
        "options": ["14 (7 Jézus, 7 Mária szenvedését ábrázolja)", "12 hagyományos stáció", "10 stáció", "16 stáció"],
        "answer": "14 (7 Jézus, 7 Mária szenvedését ábrázolja)",
        "explanation": "A megszokott 12 helyett 14 stáció található, ebből hét Jézus, hét pedig Mária szenvedését ábrázolja."
    },
    {
        "question": "Ki építette a monda szerint a selmeci Leányvárat (Újvárat), mert nem akarta látni a helyén lévő akasztófát?",
        "options": ["Rössel Borbála", "Szitnyai Borbála", "Krecsmáry Anna", "Hellenbach Katalin"],
        "answer": "Rössel Borbála",
        "explanation": "A monda szerint a gazdag Rössel Borbála építette, aki később elszegényedett és a temetésén kutyák falták fel a holttestét."
    },
    {
        "question": "Milyen fából készült a Klopacska (Lármafa) kopogtatója, amit a bakter hajnal kettőkor szólaltatott meg?",
        "options": ["Jávordeszkából", "Kocsányos tölgyből", "Bükkfából", "Fenyődeszkából"],
        "answer": "Jávordeszkából",
        "explanation": "A bakter a torony első emeletén lakott, és hajnal kettőkor a jávordeszkából készített kopogtatót szólaltatta meg."
    },
    {
        "question": "Melyik selmeci épület sarkánál található a 'maflasarok', ahol az akadémisták és a selmeci lányok találkoztak?",
        "options": ["Fritz-ház", "Krecsmáry-ház", "Szitnyai-ház", "Belházy-ház"],
        "answer": "Fritz-ház",
        "explanation": "A Fritz-ház ('A'-épület) Teraszhoz eső sarkánál volt a maflasarok, a földszintjén pedig a Molnár-féle kocsma."
    },
    {
        "question": "Melyik selmeci épület földszintjén működött az 'Arany Bányamécshez' (zum goldenen Grubenlicht) címzett fogadó, Stelz Flórián ('Flóris') kocsmája?",
        "options": ["Szitnyai-ház", "Zsembery-ház", "Hellenbach-ház", "Kamaraház"],
        "answer": "Szitnyai-ház",
        "explanation": "A Szitnyai-ház földszintjén volt az Arany Bányamécs fogadó, ahol a burschok 'aufra' (hitelre) is ihattak."
    },
    {
        "question": "Melyik épület udvarából nyílik a ~76 méter hosszú Mihály-táró, és szolgált egykor az akadémia halottainak ravatalozójaként?",
        "options": ["Hellenbach-ház (Berggericht)", "Belházy-ház", "Privitzky-ház", "Kamaraház"],
        "answer": "Hellenbach-ház (Berggericht)",
        "explanation": "A Hellenbach-ház adott otthont a Bányatörvényszéknek, innen indult a gyászmenet, és udvarából nyílik a Mihály-táró."
    },
    {
        "question": "Milyen sorrendben épültek fel az akadémia palotái Selmecbányán?",
        "options": ["Erdészeti (1890/92), Bányászati-Kohászati (1900), Kémiai (1912)", "Bányászati (1890), Erdészeti (1900), Kémiai (1912)", "Kémiai (1892), Bányászati (1900), Erdészeti (1912)", "Bányászati (1885), Kohászati (1895), Erdészeti (1905)"],
        "answer": "Erdészeti (1890/92), Bányászati-Kohászati (1900), Kémiai (1912)",
        "explanation": "Először az Erdészeti (1890, átadás 1892), majd a Bányászati és Kohászati (1900), végül a Kémiai palota (1912) épült fel."
    },
    {
        "question": "Miért mondják Selmec csodái között, hogy 'egyszer egy bika beleesett a kéménybe'?",
        "options": ["Egy bánya szellőzőaknájába esett bele", "A meredek hegyoldal miatt a háztetőre sétált", "A Klopacska kéményébe szorult be", "A kohó olvasztókéményébe ugrott"],
        "answer": "Egy bánya szellőzőaknájába esett bele",
        "explanation": "Nem hagyományos kéményről van szó, hanem egy bánya szellőzőaknájáról, ahonnan élve sikerült kiemelni a jószágot."
    },
    {
        "question": "Milyen színnel jelenítették meg az ördögöt a selmeci Kálvária ábrázolásain (a soproni/fehérvári csodák szerint)?",
        "options": ["Fehér színnel", "Zöld színnel", "Arany színnel", "Kék színnel"],
        "answer": "Fehér színnel",
        "explanation": "A megszokottól eltérően a selmeci Kálvária ábrázolásain fehér színnel jelenítették meg az ördögöt."
    },
    {
        "question": "Melyik két település lakói hívták egymást 'sóskazabálóknak', illetve 'lustabányászoknak'?",
        "options": ["A selmecbányaiak és a körmöcbányaiak", "A selmecbányaiak és a besztercebányaiak", "A miskolciak és a soproniak", "A selmecbányaiak és a bélabányaiak"],
        "answer": "A selmecbányaiak és a körmöcbányaiak",
        "explanation": "A körmöcbányaiak hívták sóskazabálóknak a selmecieket (a styavel=sóska szóból), míg a körmöciek a lustabányász címet viselték."
    },
    {
        "question": "Melyik király emelte Miskolcot mezővárosi rangra 1365-ben?",
        "options": ["Nagy Lajos", "IV. Béla", "Mátyás király", "Károly Róbert"],
        "answer": "Nagy Lajos",
        "explanation": "Miskolcot Nagy Lajos király emelte mezővárosi rangra 1365-ben."
    },
    {
        "question": "Melyik település hozzácsatolásával nyerte el Miskolc a mai kiterjedését 1981-ben?",
        "options": ["Bükkszentlászló", "Diósgyőr", "Görömböly", "Hámor"],
        "answer": "Bükkszentlászló",
        "explanation": "Diósgyőrt és Hejőcsabát 1945-ben, Görömbölyt, Szirmát és Hámort 1950-ben, Bükkszentlászlót pedig 1981-ben csatolták Miskolchoz."
    },

    # 51-60: Diáktársaságok és Ifjúsági Kör
    {
        "question": "Melyik volt a legkorábbi, 1810-től alapszabályzattal működő vidéki kör Selmecbányán?",
        "options": ["Erdélyi Kör", "Bánátia", "Dunántúli Kör", "Szepesi Társaság"],
        "answer": "Erdélyi Kör",
        "explanation": "A legkorábbi ismert, 1810-től alapszabályzattal működő vidéki kör az Erdélyi Kör volt."
    },
    {
        "question": "Melyik évben alakult meg a Verbindung Schacht (Schacht Egylet), és milyen néven adott ki saját diákújságot?",
        "options": ["1858, Deutsche Kneip-Zeitung", "1823, Steingrubeni Bakter-Kürt", "1879, Bástyánk", "1863, Bányászati Lapok"],
        "answer": "1858, Deutsche Kneip-Zeitung",
        "explanation": "A Schacht Egylet 1858-ban alakult meg, és Deutsche Kneip-Zeitung néven adott ki saját diákújságot."
    },
    {
        "question": "Hány szavazattöbbséggel oszlatta fel magát a Schacht Egylet 1876. december 3-án?",
        "options": ["Csupán egyetlen szavazattöbbséggel", "Egyhangú szavazással", "88%-os szavazattöbbséggel", "Kétharmados többséggel"],
        "answer": "Csupán egyetlen szavazattöbbséggel",
        "explanation": "A Schacht Egylet felsőbb nyomásra, csupán egyetlen szavazattöbbséggel oszlatta fel magát 1876. december 3-án."
    },
    {
        "question": "Melyik két társaság egyesülésével jött létre az Ifjúsági Kör 1879. május 22-én?",
        "options": ["Általános Társaság és Magyar Társaság", "Schacht Egylet és Akadémiai Olvasókör", "Concordia és Steingrube Nagyközség", "Burschenschaft és Erdélyi Kör"],
        "answer": "Általános Társaság és Magyar Társaság",
        "explanation": "Az egységes Ifjúsági Kör 1879-ben az Általános Társaság és a Magyar Társaság egyesülésével jött létre."
    },
    {
        "question": "Hogyan csúfolták a 'Corpus Juris' nevű szabályzatukat a Steingrube Nagyközség tagjai?",
        "options": ["Korpás Julis", "Bakter-Kürt", "Gyesznótor", "Kupaktanács"],
        "answer": "Korpás Julis",
        "explanation": "Írásba foglalt szokásaikat Corpus Juris (Korpás Julis, hisz a faluról jött ember nem tud latinul) néven adták közre."
    },
    {
        "question": "Melyik napon tartotta meg utolsó szakestélyét, majd oszlatta fel magát 88%-os többséggel az Ifjúsági Kör?",
        "options": ["1948. május 5. (szakestély) és május 7. (feloszlatás)", "1949. augusztus 19.", "1956. november 4.", "1945. március 30."],
        "answer": "1948. május 5. (szakestély) és május 7. (feloszlatás)",
        "explanation": "A MEFESZ politikai nyomására a Kör 1948. május 5-én tartotta utolsó szakestélyét, majd május 7-én feloszlatta magát."
    },
    {
        "question": "Melyik évben alakult meg Miskolcon a Dudujka-völgyi Rókák Baráti Társasága (DVR) és a Cantusok Köre?",
        "options": ["DVR: 1995, Cantusok Köre: 2007", "DVR: 1989, Cantusok Köre: 2001", "DVR: 1999, Cantusok Köre: 2006", "DVR: 2002, Cantusok Köre: 2011"],
        "answer": "DVR: 1995, Cantusok Köre: 2007",
        "explanation": "Miskolcon a DVR 1995-ben, míg a Cantusok Köre 2007-ben alakult meg."
    },
    {
        "question": "Hogyan hívták a balekot a legkorábbi selmeci időkben, mielőtt a 'fuchs', majd a 'balek' szó elterjedt volna?",
        "options": ["Fisch (hal)", "Kohlenbrenner", "Kammer", "expectans"],
        "answer": "Fisch (hal)",
        "explanation": "Firmaőseink fisch-nek (halnak) nevezték, mert a hal is bután néz, némán tátog és senki sem érti mit akar."
    },
    {
        "question": "Hogyan határozza meg a hagyomány tréfásan a 'balek' fogalmát?",
        "options": ["Zöldfülű, sárgacsőrű, büdös, poros hajú és értelem nélküli védtelen, aki a Firmák támogatására szorul", "Olyan végzett hallgató, aki már elhagyta az egyetemet", "A szakestélyt levezető, legmagasabb rangú tisztségviselő", "A másodéves hallgató, aki már Firmává keresztelkedett"],
        "answer": "Zöldfülű, sárgacsőrű, büdös, poros hajú és értelem nélküli védtelen, aki a Firmák támogatására szorul",
        "explanation": "A PDF a balekot humorosan így írja le: a Firmák támogatására szoruló, keresztelésen frissen átesett diák."
    },
    {
        "question": "Kit neveznek Firmának a selmeci hagyományban?",
        "options": ["A hagyomány szerint a harmadéves, megkeresztelkedett hallgatót", "Az elsőéves, még meg nem keresztelkedett hallgatót", "A szakestélyen a nótákat vezető tisztségviselőt", "A tanulmányait befejező, elvalétált hallgatót"],
        "answer": "A hagyomány szerint a harmadéves, megkeresztelkedett hallgatót",
        "explanation": "A selmeci akadémiai hierarchiában a harmadéveseket tekintették Firmának; a hagyomány ma is a keresztelkedést tekinti ennek feltételéül."
    },
    {
        "question": "Mi a balek tízparancsolatának 0., 6. és 9. pontja?",
        "options": ["0: Firmádnak mindig igaza van! 6: ne légy konfidens! 9: Firmák asztalához csakis engedéllyel ülj!", "0: kussch! 6: ne légy falánk! 9: válassz magadnak Firmát!", "0: mutatkozz be! 6: illedelmesen köszönj! 9: házi nyúlra nem lövünk!", "0: légy illedelmes! 6: kussch! 9: ne kívánd Firmád nőjét!"],
        "answer": "0: Firmádnak mindig igaza van! 6: ne légy konfidens! 9: Firmák asztalához csakis engedéllyel ülj!",
        "explanation": "A 0. parancsolat: Firmádnak mindig igaza van! A 6.: ne légy konfidens! A 9.: Firmák asztalához csakis engedéllyel ülj!"
    },
    {
        "question": "Honnan ered a másodévesek 'kohlenbrenner' (szénégető) elnevezése?",
        "options": ["A II. évben tanulták a vegytant és a mesterséges szénelőállítást", "Ők fűtötték a kollégiumi kazánokat", "A bányában csak szenet lapátolhattak", "Fekete korommal kenték be az arcukat"],
        "answer": "A II. évben tanulták a vegytant és a mesterséges szénelőállítást",
        "explanation": "Selmecbányán a II. évben tanulták a hallgatók a vegytant és ezzel együtt a mesterséges szénelőállítást."
    },

    # 61-75: balekság, Valétálás és Szakestélyek
    {
        "question": "Kit neveztek eredetileg Selmecen 'Filiszternek', és kit nevezünk így ma?",
        "options": ["Régen a diákság jókedve előtt értetlenül álló polgárt, ma az elvalétált (végzett) hallgatót", "Régen az elsőéves diákot, ma a professzorokat", "Régen a kocsmárost, ma a Valétaelnököt", "Régen a bukott diákot, ma a Veteránt"],
        "answer": "Régen a diákság jókedve előtt értetlenül álló polgárt, ma az elvalétált (végzett) hallgatót",
        "explanation": "Hajdanán a nyársat nyelt polgárokat hívták így, ma a diákéletet elhagyó, elvalétált egykori hallgatókat."
    },
    {
        "question": "Mi a balekjelölt életének három ballépése, amiért bal lábbal kell belépnie a balekvizsgára?",
        "options": ["1. Megszületett, 2. Beiratkozott az egyetemre, 3. Belép a balekvizsgára", "1. Érettségit tett, 2. Kollégista lett, 3. Megbukott a zh-n", "1. Pogány volt, 2. balek lett, 3. Kohlenbrenner lesz", "1. Ivott a szakestélyen, 2. Kiment nóta alatt, 3. Elfelejtette a tízparancsolatot"],
        "answer": "1. Megszületett, 2. Beiratkozott az egyetemre, 3. Belép a balekvizsgára",
        "explanation": "Az első ballépés, hogy megszületett, a második az egyetemre való beiratkozás, a harmadik a vizsgaterembe való belépés."
    },
    {
        "question": "Mi a legjobb megszerezhető érdemjegy a balekvizsgán, és mit kell leadnia annak, aki megbukik?",
        "options": ["Elégséges (2); bukás esetén UV-csekket (egy üveg/doboz sört)", "Jeles (5); bukás esetén 5 liter bort", "Megfelelt; bukás esetén egy krampampulit", "Közepes (3); bukás esetén a balekindexét"],
        "answer": "Elégséges (2); bukás esetén UV-csekket (egy üveg/doboz sört)",
        "explanation": "A legjobb érdemjegy az elégséges. Aki megbukik, egy UV-csekk (egy üveg vagy doboz sör) leadása után próbálkozhat újra."
    },
    {
        "question": "Kinek a szájából hangzott el a történet szerint a 'Téged pedig, balekok dísze, az Isten éltessen soká!' mondat?",
        "options": ["Az országos főerdőmester", "A főkamaragróf", "Mária Terézia", "Az akadémia rektora"],
        "answer": "Az országos főerdőmester",
        "explanation": "Az országos főerdőmester látogatásakor a Firmák szándékosan téves szakszavakkal tűzdelt beszédet írattak egy törtető balekkal."
    },
    {
        "question": "Mit mond a keresztapa és mit mond utána a keresztanya a balekkeresztelőn?",
        "options": ["A keresztapa 'vulgo'-t mond, a keresztanya utána 'avagy'-t mond", "A keresztapa 'avagy'-t mond, a keresztanya utána 'vulgo'-t mond", "Mindketten 'vulgo'-t mondanak", "A keresztapa 'cimbora'-t, a keresztanya 'fuchs'-ot mond"],
        "answer": "A keresztapa 'vulgo'-t mond, a keresztanya utána 'avagy'-t mond",
        "explanation": "A PDF szerint a keresztapa a vulgo nevet mondja ki, majd a keresztanya utána az 'avagy' formulával adja meg a második nevet."
    },
    {
        "question": "Mit jelent a latin eredetű 'Valete!' szó?",
        "options": ["Éljetek boldogul!", "Jó szerencsét!", "Igyunk fenékig!", "Örvendezzünk!"],
        "answer": "Éljetek boldogul!",
        "explanation": "A Valétálás a latin 'Valete' szóból ered, melynek jelentése: Éljetek Boldogul!"
    },
    {
        "question": "Meddig kötelesek viselni a valétálók a bal karjukra feltűzött Valétaszalagot Miskolcon, illetve Sopronban?",
        "options": ["Miskolcon a Gyűrűavatóig, Sopronban a Valétabálig", "Mindkét helyen a diplomaosztóig", "Miskolcon a Ballagásig, Sopronban a Gyűrűavatóig", "Csak a Szalagavató Szakestély ideje alatt"],
        "answer": "Miskolcon a Gyűrűavatóig, Sopronban a Valétabálig",
        "explanation": "A felavatott szalagot a valétálók Miskolcon a Gyűrűavatóig, míg Sopronban a Valétabálig (éjféli szalaglevételig) kötelesek viselni."
    },
    {
        "question": "Melyik év óta avatnak Valétagyűrűt Miskolcon, és melyik kar honosította meg a szokást?",
        "options": ["1963 óta, a gépész évfolyam", "1949 óta, a bányász évfolyam", "1952 óta, a kohász évfolyam", "1983 óta, a jogász évfolyam"],
        "answer": "1963 óta, a gépész évfolyam",
        "explanation": "Valétagyűrűt Miskolcon 1963 óta avatnak, az akkor végzős gépész évfolyam honosította meg."
    },
    {
        "question": "Honnan indul és hol ér véget a ballagási Szalamander menet Miskolcon?",
        "options": ["A Városháza előtti térről indul és a Petőfi téren ér véget", "Az Egyetemvárosból indul és a Városházánál ér véget", "A Petőfi térről indul és az E/1-es kollégiumnál ér véget", "A Népkertből indul és a Hősök terén ér véget"],
        "answer": "A Városháza előtti térről indul és a Petőfi téren ér véget",
        "explanation": "Miskolcon a menet sötétedéskor a városháza előtti térről indul és a Petőfi téren ér véget, ahol átadják a Valétaelnöki tisztséget."
    },
    {
        "question": "Melyik évben és milyen apropóból született meg a soproni Hattyútollazás valós története Nemky professzor leírása szerint?",
        "options": ["1932 júniusában, a 'filléres' gyorsvonattal érkező vendégek meglepésére", "1919 áprilisában, a Selmecről való megérkezés örömére", "1921-ben, a sikeres soproni népszavazás ünneplésére", "1945-ben, a háború végének megünneplésére"],
        "answer": "1932 júniusában, a 'filléres' gyorsvonattal érkező vendégek meglepésére",
        "explanation": "A legenda szerint egy bukott diák tollazta be a kettesért, a valóságban 1932 júniusában a filléres vonat utasait lepték meg vele."
    },
    {
        "question": "Melyik évhez és helyszínhez köthető az első szakestélyre szóló Invitáló cetli (Invit)?",
        "options": ["1971, Normafa vendéglő (Vadászati Világkiállítás)", "1879, Selmecbánya (Ifjúsági Kör alakulása)", "1922, Sopron (Honvéd Főreáliskola)", "1949, Miskolc (Első bányász szakestély)"],
        "answer": "1971, Normafa vendéglő (Vadászati Világkiállítás)",
        "explanation": "Az Invit cetli múltja az 1971-ben, a Normafa vendéglőben tartott szakestélyig nyúlik vissza, amin a Vadászati Világkiállításon dolgozó hallgatók vettek részt."
    },
    {
        "question": "Milyen színű szalagot viselnek a szakestély szalagos tisztségviselői?",
        "options": ["Praeses: fehér, Major Domus: kék, Fuchsmajor: fekete, Cantus Praeses: piros, Contrapunkt: sárga, Pater Krampampuli: fahéjbarna", "Praeses: piros, Major Domus: fehér, Fuchsmajor: fekete, Cantus Praeses: kék, Contrapunkt: zöld, Pater Krampampuli: barna", "Praeses: arany, Major Domus: ezüst, Fuchsmajor: fekete, Cantus Praeses: piros, Contrapunkt: sárga, Pater Krampampuli: lila", "Praeses: fehér, Major Domus: zöld, Fuchsmajor: barna, Cantus Praeses: sárga, Contrapunkt: kék, Pater Krampampuli: fekete"],
        "answer": "Praeses: fehér, Major Domus: kék, Fuchsmajor: fekete, Cantus Praeses: piros, Contrapunkt: sárga, Pater Krampampuli: fahéjbarna",
        "explanation": "A széles szalagok színei: Praeses - fehér, Major Domus - kék, Fuchsmajor - fekete, Cantus Praeses - piros, Contrapunkt - sárga, Pater Krampampuli - fahéjbarna."
    },
    {
        "question": "Mi a feladata a 'Konzekvencia' nevű szalag nélküli tisztségviselőnek a szakestélyen?",
        "options": ["Az Elnök tévedései után 'Vivát Praeses!' felkiáltással fenékig üríteni a korsóját", "Mindig teli korsót biztosítani az Elnök előtt", "Gyertyával világítani a felszólalók mellett", "Az asztalokon lévő ételt és italt pótolni"],
        "answer": "Az Elnök tévedései után 'Vivát Praeses!' felkiáltással fenékig üríteni a korsóját",
        "explanation": "Mivel a Praeses tévedhetetlen, a Konzekvencia vonja le a következtetést egy teli korsó fenékig ürítésével (a teli korsóról a Leibfuchs/Garatőr, a világításról a Kandeláber, a pótlásról a Fuhrwerk gondoskodik)."
    },
    {
        "question": "Mi a Major Domus (Háznagy) feladata a szakestélyen?",
        "options": ["Előkészíti és megszervezi a szakestélyt, valamint felolvassa a Házirendet", "Fogadja az érkezőket és rendet tart a balekok között", "A felszólalók mellett gondoskodik a megfelelő világításról", "Az asztalokon pótolja az ételt és az italt"],
        "answer": "Előkészíti és megszervezi a szakestélyt, valamint felolvassa a Házirendet",
        "explanation": "A Major Domus az Elnök jobbkeze: előkészíti és megszervezi az estét, megírja és felolvassa a Házirendet, szükség esetén pedig helyettesíti a Praesest."
    },
    {
        "question": "Mi a Fuchsmajor (Balekcsősz) feladata?",
        "options": ["Fogadja az érkezőket, fenntartja a rendet, és közvetít az Elnök és a balekok között", "A szakestély témáját adó első pohárbeszédet tartja", "Az Elnök tévedései után fenékig üríti a korsóját", "Megírja és felolvassa a szakestély Házirendjét"],
        "answer": "Fogadja az érkezőket, fenntartja a rendet, és közvetít az Elnök és a balekok között",
        "explanation": "A Fuchsmajor fogadja az érkezőket, gondoskodik a rendről, és rajta keresztül kommunikál az Elnök a balekokkal."
    },
    {
        "question": "Milyen feladatot lát el a Kandeláber a szakestélyen?",
        "options": ["Világítást biztosít a felszólalónak, hogy jól lássa a mondandóját", "Teli korsót biztosít a tisztségviselőknek", "Az asztalokon pótolja az ételt és az italt", "A szakestély nótáit intonálja"],
        "answer": "Világítást biztosít a felszólalónak, hogy jól lássa a mondandóját",
        "explanation": "Az Elnök jelöl ki egy-egy Kandelábert a felszólalók mellé, hogy azok lássák a mondandójukat, és mindenki jól láthassa őket."
    },
    {
        "question": "Mi történik a szakestély elején, mielőtt a megválasztott Elnök átveszi a Praesidiumot?",
        "options": ["A világítás lekapcsolása után a Cantus elkezdi a 'Sza-sza-szakestély' nótát, majd a jelenlévők megválasztják az Elnököt", "A Háznagy felolvassa a Házirendet, majd mindenki elénekli a Bányász himnuszt", "A Fuchsmajor kihirdeti a szünetet, majd a Cantus felolvassa a tisztségviselőket", "A Pater Krampampuli elkészíti italát, majd a Firmák kiosztják a szalagokat"],
        "answer": "A világítás lekapcsolása után a Cantus elkezdi a 'Sza-sza-szakestély' nótát, majd a jelenlévők megválasztják az Elnököt",
        "explanation": "Miután mindenki elfoglalta a helyét és a Háznagy jóváhagyta, lekapcsolják a világítást. A Cantus elkezdi a 'Sza-sza-szakestély' nótát; az Elnök megválasztásáig a dalban az 'Előnökünk' szerepel."
    },
    {
        "question": "Mi a szakestély első felszólalásának, a 'Komoly pohárnak' a szerepe?",
        "options": ["A szakestély témáját érintő felszólalás, amely megadja a komoly rész alaphangját", "A Házirend hitelesítése a legidősebb Firma által", "A nótaszünet végét jelző köszöntés", "A szakestély végén elhangzó Valete-beszéd"],
        "answer": "A szakestély témáját érintő felszólalás, amely megadja a komoly rész alaphangját",
        "explanation": "A Komoly pohár a szakestély témáját érintő első felszólalás; ezt további beszédek és nóták követik a szünet, vagyis a Silentium Eks előtt."
    },
    {
        "question": "Ki hitelesíti a Háznagy által felolvasott Házirendet a szakestélyen?",
        "options": ["A legidősebb Firma (keresztelkedés szerint) aláírásával és sörével", "A Praeses és a Contrapunkt", "A díszbalek és a Fuchsmajor", "Az egyetem rektora vagy dékánja"],
        "answer": "A legidősebb Firma (keresztelkedés szerint) aláírásával és sörével",
        "explanation": "A Házirendet a keresztelkedés szerint legidősebb jelenlévő Firma hitelesíti aláírásával és sörével."
    },
    {
        "question": "Melyik nóta jelzi a szakestély szünetének végét Miskolcon, illetve Sopronban?",
        "options": ["Miskolcon: Steingrubeni induló, Sopronban: Szerencse fel a tárna vár", "Miskolcon: Gaudeamus igitur, Sopronban: Steingrubeni induló", "Mindkét helyen a Sza-sza-szakestély", "Miskolcon: Ballag már a vén diák, Sopronban: Visszapillantás"],
        "answer": "Miskolcon: Steingrubeni induló, Sopronban: Szerencse fel a tárna vár",
        "explanation": "A szünet (Silentium Eks) végét általában a Steingrubeni induló ('Ha Steingrubéba óra vóna...'), míg Sopronban a 'Szerencse fel a tárna vár' jelzi."
    },

    # 76-90: Szakestély szabályok, Gyászszakestély, Köszöntések, Jelképek, Egyenruhák
    {
        "question": "Hogyan kell jeleznie a résztvevőnek, ha 'folyó ügyeit' szeretné elintézni a szakestélyen?",
        "options": ["Nóta alatt, 'Tempus helyemre és italomra' szavakkal, bal kéz ökölbe szorítva felemelve, jobb kéz a bal vállon", "Felszólalás alatt, 'Vocem preco!' felkiáltással", "Nóta alatt, jobb kéz feltartva, bal kéz a korsón", "Bármikor, a Fuchsmajor engedélyével"],
        "answer": "Nóta alatt, 'Tempus helyemre és italomra' szavakkal, bal kéz ökölbe szorítva felemelve, jobb kéz a bal vállon",
        "explanation": "Miskolcon csak nóta alatt lehet kimenni a 'Tempus helyemre és italomra' formulával és a megfelelő kéztartással (Sopronban felszólalás alatt is, ha nem zavaró)."
    },
    {
        "question": "Mit jelentenek az Elnök ivásra adott vezényszavai: Eks!, Tükrös!, Lefety!?",
        "options": ["Eks: fenékig, Tükrös: félig, Lefety: tetszés szerint", "Eks: félig, Tükrös: egy korty, Lefety: fenékig", "Eks: fenékig, Tükrös: az aljáig, Lefety: csak a habját", "Eks: csere a szomszéddal, Tükrös: félig, Lefety: tetszés szerint"],
        "answer": "Eks: fenékig, Tükrös: félig, Lefety: tetszés szerint",
        "explanation": "Az elnöki utasítások jelentése: Eks! - Fenékig!, Tükrös! - Félig!, Lefety! - Tetszés szerinti mértékben!"
    },
    {
        "question": "Milyen teljesítmény szükséges a 'Sördoktori' cím elnyeréséhez egy szakestélyen?",
        "options": ["A szakestély alatt 20 korsó sör, majd a végén még 5 liter Eks!-re", "A szakestély alatt 10 korsó sör és 1 liter krampampuli", "24 óra alatt 24 korsó sör", "A szakestély alatt 15 korsó sör sörpárbajokban"],
        "answer": "A szakestély alatt 20 korsó sör, majd a végén még 5 liter Eks!-re",
        "explanation": "A delikvensnek a szakestély ideje alatt 20 korsó sört kell elfogyasztania, majd ennek végeztével még 5 litert Eks!-re."
    },
    {
        "question": "Mi volt a 'reibolás' a Gyászszakestélyen?",
        "options": ["A korsó kopogtatása (2 hosszú, 3 rövid), asztalhoz dörzsölése (6-7-szer), majd az asztal széléhez vágva összetörése", "A fehér gyászszalagok elégetése a krampampulis tálban", "A bányászlámpák egyszerre történő elfújása", "A koporsó háromszori megemelése a sírgödörnél"],
        "answer": "A korsó kopogtatása (2 hosszú, 3 rövid), asztalhoz dörzsölése (6-7-szer), majd az asztal széléhez vágva összetörése",
        "explanation": "A reibolás során az üres korsót kopogtatták, az asztalhoz dörzsölték, majd összetörték, a fülét pedig fekete szalaggal átkötve emlékül hazavitték."
    },
    {
        "question": "Melyik évben fogadták el hivatalosan az OMBKE választmányi ülésén a Péch Antal által 1879-ben megalkotott 'Jó szerencsét!' köszöntést?",
        "options": ["1894-ben", "1879-ben", "1868-ban", "1904-ben"],
        "answer": "1894-ben",
        "explanation": "Péch Antal 1879-ben alkotta meg a 'Glück auf!' magyarításaként, és 1894-ben fogadta el hivatalosan az OMBKE."
    },
    {
        "question": "Melyik kar/szak köszöntése a 'Legyen Fényes Sikere a Kohásznak!' és a 'Világost a Geósnak!'?",
        "options": ["A kohászoké, illetve a székesfehérvári geodétáké", "A kohászoké, illetve a miskolci földtudományisoké", "A gépészeké, illetve a soproni erdészeké", "A dunaújvárosi tanároké, illetve a geodétáké"],
        "answer": "A kohászoké, illetve a székesfehérvári geodétáké",
        "explanation": "A kohászok köszöntése a 'Legyen Fényes Sikere a Kohásznak!', míg a székesfehérvári geodétáké a 'Világost a Geósnak!'."
    },
    {
        "question": "Melyik évből származik a bányász címer (Schlägel und Eisen - kalapács és nyeles ék) első ismert, illetve mai formában (keresztezve) való ábrázolása?",
        "options": ["Első: 1275, Keresztezve: 1347", "Első: 1217, Keresztezve: 1238", "Első: 1347, Keresztezve: 1735", "Első: 1544, Keresztezve: 1762"],
        "answer": "Első: 1275, Keresztezve: 1347",
        "explanation": "Első ismert ábrázolása egy 1275-ös selmecbányai pecsétről, míg keresztezett formája 1347-ből ismert."
    },
    {
        "question": "Melyik korábbi viselet tekinthető a mai Gruben, illetve a mai Bányaing valós ősének?",
        "options": ["Gruben: Bibertárói ruha (Biberstollen), Bányaing: Freibergi fekete ruha", "Gruben: Freibergi fekete ruha, Bányaing: Miksa-féle viselet", "Gruben: Tiroli fehér ruha, Bányaing: Magyaros ruha", "Gruben: Alt Deutschen Tracht, Bányaing: Bibertárói ruha"],
        "answer": "Gruben: Bibertárói ruha (Biberstollen), Bányaing: Freibergi fekete ruha",
        "explanation": "A szakirodalom alapján a Gruben elődje a Bibertárói ruha (Biberstollen), a Bányaingé pedig a Freibergi fekete ruha."
    },
    {
        "question": "Melyik évben egységesítették véglegesen az akadémiai egyenruhákat az Erdészeti palota átadásakor?",
        "options": ["1892-ben", "1839-ben", "1884-ben", "1900-ban"],
        "answer": "1892-ben",
        "explanation": "Az Erdészeti palota átadásakor, 1892-ben egységesítették véglegesen a ma is ismert egyenruhákat."
    },
    {
        "question": "Hány gomb és milyen válltömés található a miskolci bányászok és kohászok Grubenen?",
        "options": ["Elöl 5 nagy, mellzsebeken 2 kis, hátul 3-3 nagy gomb; a vállon 4-5 függőleges és 3 vízszintes hurka", "Elöl 7 nagy, hátul 2-2 kis gomb; a vállon 3 függőleges és 3 vízszintes hurka", "Elöl 5 nagy, kézelőn 3-3 kis gomb; válltömés nélkül", "Elöl 8-10 kis gomb, mellen 5-5 kis gomb; vállrojtozással"],
        "answer": "Elöl 5 nagy, mellzsebeken 2 kis, hátul 3-3 nagy gomb; a vállon 4-5 függőleges és 3 vízszintes hurka",
        "explanation": "A Gruben elől 5 nagy, a mellzsebeken 2 kis, hátul 3-3 nagy bányászgombbal rendelkezik, vállát 4-5 függőleges és 3 vízszintes hurka vastagítja."
    },
    {
        "question": "Milyen színű paszományt viselnek a bányászok és a kohászok a Grubenen?",
        "options": ["Bányászok: fekete, kohászok: meggypiros", "Bányászok: meggypiros, kohászok: fekete", "Bányászok: zöld, kohászok: sötétkék", "Mindkét szak: aranyszínű"],
        "answer": "Bányászok: fekete, kohászok: meggypiros",
        "explanation": "A Gruben fekete alapú; a bányászok fekete, a kohászok meggypiros paszományt viselnek."
    },
    {
        "question": "Milyen volt az erdészek 1839-ben engedélyezett egyenruhája?",
        "options": ["Zöld, világosabb zöld gallérral és hajtókával, ezüst beszegéssel és ezüst gombokkal", "Fekete, meggypiros paszománnyal és arany gombokkal", "Őzbarna, sötétkék gallérral és fekete gombokkal", "Szürke, állógalléros, négy zsebbel és ezüst paszománnyal"],
        "answer": "Zöld, világosabb zöld gallérral és hajtókával, ezüst beszegéssel és ezüst gombokkal",
        "explanation": "A kamara 1839-ben zöld egyenruha viselését engedélyezte az erdészeknek, világosabb zöld gallérral és hajtókával, ezüst beszegéssel és ezüst gombokkal."
    },
    {
        "question": "Miben tér el a dunaújvárosi Aufhauer a miskolcitól?",
        "options": ["Hiányzik róla a hátsó hasíték és a 6 kisgomb, viszont van egy mellzsebe a jobb oldalon", "Nem 5, hanem 7 nagy gombbal gombolódik elöl", "Ezüst gombok vannak rajta arany helyett", "Válltömések találhatók rajta, mint a Grubenen"],
        "answer": "Hiányzik róla a hátsó hasíték és a 6 kisgomb, viszont van egy mellzsebe a jobb oldalon",
        "explanation": "A dunaújvárosi Aufról hiányzik a hátsó hasíték és a hat kisgomb, viszont rendelkezik egy mellzsebbel a jobb oldalon."
    },
    {
        "question": "Milyen színű a Walden alapanyaga, és milyen színű paszományt viselnek rajta az erdészek, a faiparosok és a geodéták?",
        "options": ["Őzbarna alap; Erdész: zöld, Fás: fekete, Geodéta: sötétkék paszomány", "Palackzöld alap; Erdész: barna, Fás: fekete, Geodéta: kék paszomány", "Őzbarna alap; Erdész: fekete, Fás: zöld, Geodéta: piros paszomány", "Fekete alap; Erdész: zöld, Fás: barna, Geodéta: sárga paszomány"],
        "answer": "Őzbarna alap; Erdész: zöld, Fás: fekete, Geodéta: sötétkék paszomány",
        "explanation": "A Walden őzbarna anyagból készül; az erdészek zöld, a fások fekete, a székesfehérvári geodéták sötétkék paszománnyal viselik."
    },
    {
        "question": "Melyik szakok egyenruhája/egyenviselete az Atilla, a Veblen, a Jurátus, az Aurum és a Stefánia?",
        "options": ["Atilla: erdész díszegyenruha, Veblen: soproni közgazdász, Jurátus: miskolci jogász, Aurum: miskolci gazdász, Stefánia: miskolci egészségügyis", "Atilla: miskolci bölcsész, Veblen: miskolci gazdász, Jurátus: jogász, Aurum: soproni közgazdász, Stefánia: dunaújvárosi tanár", "Atilla: bányász díszruha, Veblen: geodéta, Jurátus: jogász, Aurum: kohász, Stefánia: bölcsész", "Atilla: erdész, Veblen: faiparos, Jurátus: gépész, Aurum: gazdász, Stefánia: zenész"],
        "answer": "Atilla: erdész díszegyenruha, Veblen: soproni közgazdász, Jurátus: miskolci jogász, Aurum: miskolci gazdász, Stefánia: miskolci egészségügyis",
        "explanation": "Atilla: erdész díszegyenruha, Veblen: soproni közgazdász (1999), Jurátus: miskolci jogász (2002), Aurum: miskolci gazdász, Stefánia: miskolci egészségügyis (2005)."
    },
    {
        "question": "Hogyan lehet 'levenni' a Tempus-foltot az egyenruháról, ha a kapcsolat mégsem végződik házassággal?",
        "options": ["Csak az egyenruha anyagával és bélésével együtt kivágva, és a helye csak nagyobb Tempusszal foltozható be", "Le kell fejteni a cérnát és fekete posztóval befoltozni", "A Fuchsmajornak kell leégetnie egy szakestélyen", "Át kell húzni egy fekete szalaggal"],
        "answer": "Csak az egyenruha anyagával és bélésével együtt kivágva, és a helye csak nagyobb Tempusszal foltozható be",
        "explanation": "A Tempust csak anyaggal és béléssel együtt kivágva lehet eltávolítani, és a helye nem foltozható be (csak egy másik, nagyobb Tempus folttal)."
    },
    {
        "question": "Hogyan viselték a farbőrt (arschleder) a bányászok, illetve a kohászok?",
        "options": ["A bányászok hátul, a kohászok elöl (kötényként)", "A bányászok elöl, a kohászok hátul", "Mindketten hátul viselték", "A bányászok a vállukon, a kohászok a derekukon"],
        "answer": "A bányászok hátul, a kohászok elöl (kötényként)",
        "explanation": "A bányászok a hátsó felükön hordták (ezen csúsztak le a vágatokba), míg a kohászok fordítva, kötényként viselték."
    },

    # 91-100: Nóták, Diáknapok, Szakmai szervezetek, Tolások és Fogalmak
    {
        "question": "Mi volt a címe az első ismert, 1826-ban Carl Stegmayer gyűjtésében kiadott selmeci daloskönyvnek?",
        "options": ["Klänge aus der Teufe (Hangok a mélyből)", "Erinnerung an Schemnitz", "Schemnitzer Akademische Lieder", "A mi nótáink"],
        "answer": "Klänge aus der Teufe (Hangok a mélyből)",
        "explanation": "Az első ismert daloskönyv az 1826-os Klänge aus der Teufe volt, amely 19 kotta nélküli dalt és 5 verset tartalmazott."
    },
    {
        "question": "Melyik 1870-ben kiadott daloskönyv tartalmazta 88 nóta mellett a 'Cerevis' nevű kártyajáték szabályait is?",
        "options": ["Schemnitzer Akademische Lieder", "Klänge aus der Teufe", "Selmeci Bursch dalok", "Erinnerung an Schemnitz"],
        "answer": "Schemnitzer Akademische Lieder",
        "explanation": "Az 1870-es Schemnitzer Akademische Lieder tartalmazta a 88 nótát és a Cerevis kártyajáték szabályait."
    },
    {
        "question": "Melyik évre fejeződött be a dalok magyarra fordítása az 'A mi nótáink' daloskönyvben (kivéve a balekkeresztelő nótát)?",
        "options": ["1931-re", "1905-re", "1911-re", "1921-re"],
        "answer": "1931-re",
        "explanation": "1905-ben Tassonyi Ernő regényében jelent meg a magyar Bányász himnusz, a teljes fordítás pedig az 1931-es kiadásra fejeződött be."
    },
    {
        "question": "Mikor, hol és kinek a kezdeményezésére indult útjára a Selmeczi Diák Napok rendezvény, és milyen gyakran tartják Selmecbányán?",
        "options": ["1991-ben Székesfehérváron, Szabó László a. Szacó kezdeményezésére; 2000 óta 5 évente Selmecbányán", "1989-ben Sopronban, Suszter Mór kezdeményezésére; 10 évente Selmecbányán", "1995-ben Miskolcon; minden páros évben Selmecbányán", "2000-ben Selmecbányán; 4 évente Selmecbányán"],
        "answer": "1991-ben Székesfehérváron, Szabó László a. Szacó kezdeményezésére; 2000 óta 5 évente Selmecbányán",
        "explanation": "1991-ben indult Székesfehérváron Szabó László a. Szacó kezdeményezésére, 2000 óta pedig 5 évente (2000, 2005, 2010, 2015...) Selmecbányán tartják."
    },
    {
        "question": "Mikor alakult meg az OMBKE (Országos Magyar Bányászati és Kohászati Egyesület), és ki volt az első elnöke?",
        "options": ["1892-ben, gróf Teleki Géza", "1768-ban, Born Ignác", "1866-ban, gróf Keglevich Béla", "1868-ban, Péch Antal"],
        "answer": "1892-ben, gróf Teleki Géza",
        "explanation": "Előfutára az 1768-as Born Ignác-féle társaság volt, de az OMBKE 1892-ben alakult meg gróf Teleki Géza elnökletével."
    },
    {
        "question": "Mikor alakult meg az Országos Erdészeti Egyesület (OEE) az Ungarischer Forstvereinből, és kik voltak az első vezetői?",
        "options": ["1866-ban; elnöke gróf Keglevich Béla, főtitkára Bedő Albert", "1851-ben; elnöke Wagner Károly, főtitkára Divald Adolf", "1892-ben; elnöke Teleki Géza, titkára Cséti Ottó", "1808-ban; elnöke Henrik David Wilckens"],
        "answer": "1866-ban; elnöke gróf Keglevich Béla, főtitkára Bedő Albert",
        "explanation": "Az 1851-es Ungarischer Forstverein 1866-ban alakult át OEE-vé, elnöke gróf Keglevich Béla, főtitkára Bedő Albert volt."
    },
    {
        "question": "Milyen nevet kapott az 1989-ben (Miskolc-Sopron), az 1996-ban (Miskolc-Dunaújváros) és a 2006-ban (Miskolc-Selmecbánya) eltolt csille?",
        "options": ["1989: Ede, 1996: Leopold, 2006: Sámuel", "1989: Sámuel, 1996: Ede, 2006: Samu", "1989: Flóris, 1996: Leopold, 2006: Mikoviny", "1989: Ede, 1996: Krokodil, 2006: Samu"],
        "answer": "1989: Ede, 1996: Leopold, 2006: Sámuel",
        "explanation": "A miskolci csilletolások csilléi: 1989 Sopronba - Ede (2005-ben kohlenbrennerré avatták), 1996 Dunaújvárosba - Leopold, 2006 Selmecbányára - Sámuel."
    },
    {
        "question": "Milyen 'tolások' történtek 2002-ben (Sopron-Miskolc), 2017-ben (Székesfehérvár-Sopron) és 2019-ben (Dunaújváros-Miskolc)?",
        "options": ["2002: Rönktolás, 2017: Obeliszktolás, 2019: Öntött műemlék tolás", "2002: Csilletolás, 2017: Rönktolás, 2019: Üsttolás", "2002: Rönktolás, 2017: Szintezőműszer-tolás, 2019: Csilletolás", "2002: Hordótolás, 2017: Obeliszktolás, 2019: Rönktolás"],
        "answer": "2002: Rönktolás, 2017: Obeliszktolás, 2019: Öntött műemlék tolás",
        "explanation": "2002-ben faragott rönköt (E/5-tel szemben áll), 2017-ben obeliszket, 2019-ben pedig öntött műemléket toltak."
    },
    {
        "question": "Mit jelentett Selmecbányán a 'kamara' (és a 'kammer'), illetve a 'Verschiess'?",
        "options": ["Kamara: a diákok által bérelt kis szoba/lakás; Verschiess: a legszigorúbb büntetés, a kiközösítés", "Kamara: a bányatárspénztár épülete; Verschiess: a sörpárbaj elvesztése", "Kamara: a szakestély elnöksége; Verschiess: a vizsgán való megbukás", "Kamara: az egyenruhák szekrénye; Verschiess: a Tempus-folt kivágása"],
        "answer": "Kamara: a diákok által bérelt kis szoba/lakás; Verschiess: a legszigorúbb büntetés, a kiközösítés",
        "explanation": "Kollégium híján a diákok magánházaknál béreltek szobát (kamarát). A Verschiess a kiközösítés volt, amit utoljára a '40-es években a Volksbundisták ellen használtak."
    },
    {
        "question": "Mi a Selmeci sapka (ködvágó) helyes viselési módja az egyenruha sapkatartó zsinórja alatt?",
        "options": ["Állományjelzővel felfelé, a sapka 'szája' pedig a váll felé nézzen", "Állományjelzővel lefelé, a sapka 'szája' a mellkas felé nézzen", "A gombokkal kifelé, a sapka 'szája' lefelé nézzen", "A jobb vállon, állományjelzővel hátrafelé"],
        "answer": "Állományjelzővel felfelé, a sapka 'szája' pedig a váll felé nézzen",
        "explanation": "A Selmeci sapka a sapkatartó zsinór alá állományjelzővel felfelé kerül, míg a sapka 'szája' a váll felé kell, hogy nézzen."
    },

    # 110-150: Gyakorló kérdések a fontosabb fogalmakról, szokásokról és viseletekről
    {
        "question": "Mi a selmeci hagyomány szerint a balek legfontosabb feladata?",
        "options": ["Figyelje és kövesse Firmáját, és tartsa be a balekok tízparancsolatát", "Ő vezesse a szakestélyt a Praeses helyett", "Ő hitelesítse a Házirendet a szakestély elején", "Ő ossza ki a tisztségviselők szalagjait"],
        "answer": "Figyelje és kövesse Firmáját, és tartsa be a balekok tízparancsolatát",
        "explanation": "A balek legfőbb feladata, hogy kövesse Firmáját, tanuljon tőle, és betartsa a balekok tízparancsolatát."
    },
    {
        "question": "Melyik állítás írja le helyesen a Firma és a balek kapcsolatát?",
        "options": ["A Firma irányítja és támogatja a balekot, a balek pedig tanul tőle és követi az útmutatását", "A balek vezeti a Firmát a szakestélyen", "A Firma csak a vizsgán segíthet a baleknak", "A két megnevezés ugyanazt a rangot jelenti"],
        "answer": "A Firma irányítja és támogatja a balekot, a balek pedig tanul tőle és követi az útmutatását",
        "explanation": "A hagyomány szerint a Firma felelősséget vállal a balekért; a balek a Firmájától tanulja meg a közösség szabályait."
    },
    {
        "question": "Melyik sorrend kapcsolódik a hallgató hagyományos selmeci előrehaladásához?",
        "options": ["balek, Kohlenbrenner, Firma, Veterán, Filiszter", "Firma, balek, Filiszter, Kohlenbrenner, Veterán", "Kohlenbrenner, balek, Veterán, Firma, Filiszter", "balek, Firma, Kohlenbrenner, Filiszter, Veterán"],
        "answer": "balek, Kohlenbrenner, Firma, Veterán, Filiszter",
        "explanation": "A megnevezések a hagyományos hierarchiához kötődnek: a balekból Kohlenbrenner, majd Firma, később Veterán, tanulmányai után pedig Filiszter lehet."
    },
    {
        "question": "Miért nevezik a másodéves hallgatót Kohlenbrennernek?",
        "options": ["Mert a második évben vegytant és mesterséges szénelőállítást tanult", "Mert a kollégiumi kazánokat fűtötte", "Mert csak szénbányában dolgozhatott", "Mert a szakestélyen fekete ruhát viselt"],
        "answer": "Mert a második évben vegytant és mesterséges szénelőállítást tanult",
        "explanation": "A Kohlenbrenner elnevezés a második évben tanult vegytanhoz és a mesterséges szén előállításához kapcsolódik."
    },
    {
        "question": "Mit jelent a 'Veterán' megnevezés a selmeci hagyományban?",
        "options": ["Olyan Firmát, aki az iskola elvégzéséhez szükséges képzési időn túl van", "A szakestély nótáit vezető tisztségviselőt", "A balekvizsgára készülő elsőévest", "A végzett, elvalétált hallgatót"],
        "answer": "Olyan Firmát, aki az iskola elvégzéséhez szükséges képzési időn túl van",
        "explanation": "A hagyomány szerint a Veterán az a Firma, aki a képzési időn túl is az iskolában marad."
    },
    {
        "question": "Mit jelent a 'kussch!' a balekokkal kapcsolatos hagyományban?",
        "options": ["A balek maradjon csendben", "A balek emelje fel a korsóját", "A balek kérjen szót", "A balek köszönjön a Firmájának"],
        "answer": "A balek maradjon csendben",
        "explanation": "A balek tízparancsolatának visszatérő felszólítása a kussch!, vagyis a balek maradjon csendben és figyeljen."
    },
    {
        "question": "Mit jelent a 'konfidens' szó a balek tízparancsolatában?",
        "options": ["Bizalmaskodó vagy túl közvetlen személyt", "A szakestély elnökét", "A megkeresztelt harmadévest", "A nótákat intonáló tisztségviselőt"],
        "answer": "Bizalmaskodó vagy túl közvetlen személyt",
        "explanation": "A 'ne légy konfidens!' arra figyelmezteti a balekot, hogy ne legyen bizalmaskodó, és tartsa tiszteletben a hierarchiát."
    },
    {
        "question": "Mi a szerepe a 'vulgo' és az 'avagy' formulának a balekkeresztelőn?",
        "options": ["A keresztapa a 'vulgo' nevet mondja, majd a keresztanya utána az 'avagy' formulát mondja", "A keresztapa az 'avagy' formulát mondja, majd a keresztanya a 'vulgo' nevet", "Mindkét formulát a Praeses mondja", "A 'vulgo' a Firma, az 'avagy' pedig a szakestély neve"],
        "answer": "A keresztapa a 'vulgo' nevet mondja, majd a keresztanya utána az 'avagy' formulát mondja",
        "explanation": "A PDF szerint a keresztapa mondja ki a vulgo nevet, ezt követi a keresztanya 'avagy' formulája."
    },
    {
        "question": "Mi a balekvizsgán megszerezhető legjobb érdemjegy?",
        "options": ["Elégséges (2)", "Közepes (3)", "Jeles (5)", "Megfelelt"],
        "answer": "Elégséges (2)",
        "explanation": "A balekvizsga hagyományos tréfája szerint a legjobb megszerezhető jegy az elégséges."
    },
    {
        "question": "Mit jelent az UV-csekk a balekvizsga hagyományában?",
        "options": ["Egy üveg vagy doboz sört, amelyet bukás után kell leadni", "A következő vizsga időpontját", "A balekindex pótlását", "Egy krampampulihoz szükséges jegyet"],
        "answer": "Egy üveg vagy doboz sört, amelyet bukás után kell leadni",
        "explanation": "Aki megbukik, a hagyomány szerint egy üveg vagy doboz sör, azaz UV-csekk leadása után próbálkozhat újra."
    },
    {
        "question": "Mire szolgált eredetileg a balekfogadás?",
        "options": ["Az új hallgató megismertetésére a selmeci diáksággal és annak szokásaival", "A végzősök elbúcsúztatására", "A szakestély tisztségviselőinek megválasztására", "A tanulmányi eredmények kihirdetésére"],
        "answer": "Az új hallgató megismertetésére a selmeci diáksággal és annak szokásaival",
        "explanation": "A balekfogadás célja az újonnan felvett diák bevezetése volt a közösségbe és a hagyományok világába."
    },
    {
        "question": "Ki a szakestély legfőbb tisztségviselője?",
        "options": ["A Praeses, vagyis az Elnök", "A Major Domus", "A Fuchsmajor", "A Cantus Praeses"],
        "answer": "A Praeses, vagyis az Elnök",
        "explanation": "A Praeses a szakestély legfőbb tisztségviselője, szava és utasítása a szakestély rendjét meghatározza."
    },
    {
        "question": "Milyen színű a Praeses széles tisztségviselői szalagja?",
        "options": ["Fehér", "Kék", "Piros", "Fekete"],
        "answer": "Fehér",
        "explanation": "A Praeses szalagja fehér; a Major Domusé kék, a Fuchsmajoré fekete, a Cantus Praesesé piros."
    },
    {
        "question": "Milyen színű a Major Domus széles tisztségviselői szalagja?",
        "options": ["Kék", "Fehér", "Sárga", "Fahéjbarna"],
        "answer": "Kék",
        "explanation": "A Major Domus, vagyis a Háznagy kék szalagot visel."
    },
    {
        "question": "Milyen színű a Fuchsmajor széles tisztségviselői szalagja?",
        "options": ["Fekete", "Piros", "Fehér", "Kék"],
        "answer": "Fekete",
        "explanation": "A Fuchsmajor, vagyis a Balekcsősz szalagja fekete."
    },
    {
        "question": "Mi a Cantus Praeses legfontosabb feladata?",
        "options": ["A nóták megfelelő időben történő intonálása", "A Házirend felolvasása", "Az érkezők fogadása", "A világítás biztosítása"],
        "answer": "A nóták megfelelő időben történő intonálása",
        "explanation": "A Cantus Praeses vezeti a szakestély nótáit, az Elnök utasítására a megfelelő időben indítva azokat."
    },
    {
        "question": "Mi a Contrapunkt feladata?",
        "options": ["Az Elnök szavának visszhangzása és tréfás elferdítése", "A résztvevők fogadása", "A krampampuli elkészítése", "A szakestély világításának kezelése"],
        "answer": "Az Elnök szavának visszhangzása és tréfás elferdítése",
        "explanation": "A Contrapunkt az Elnök szavát visszhangozza, és megfelelő helyzetben tréfásan elferdíti vagy megerősíti."
    },
    {
        "question": "Mi a Leibfuchs, vagyis a Garatőr feladata?",
        "options": ["Gondoskodik arról, hogy az Elnök előtt mindig teli korsó legyen", "Ő vezeti a nótákat", "Ő hitelesíti a Házirendet", "Ő fogadja az új balekokat"],
        "answer": "Gondoskodik arról, hogy az Elnök előtt mindig teli korsó legyen",
        "explanation": "A Garatőr feladata, hogy az Elnök előtt mindig legyen teli korsó."
    },
    {
        "question": "Mi a Fuhrwerk, vagyis a Fuvaros feladata?",
        "options": ["Pótolja az asztalokon elfogyó ételt és italt", "A felszólalók mellett világít", "A szakestély első poharát tartja", "A balekok tízparancsolatát olvassa fel"],
        "answer": "Pótolja az asztalokon elfogyó ételt és italt",
        "explanation": "A Fuhrwerk az asztalokon lévő étel és ital pótlásával segíti a Major Domus munkáját."
    },
    {
        "question": "Mi a Pater Krampampuli szerepe?",
        "options": ["Ő készíti el és vezeti fel a krampampulit", "Ő választja meg a Praesest", "Ő őrzi az Elnök korsóját", "Ő vezeti a Szalamander menetet"],
        "answer": "Ő készíti el és vezeti fel a krampampulit",
        "explanation": "A Pater Krampampuli a szakestély alatt félrevonulva készíti el a krampampulit, majd az ital felvezetését is ő végzi."
    },
    {
        "question": "Mi történik a szakestély elején a világítással?",
        "options": ["A résztvevők helyet foglalása után lekapcsolják", "Végig égve marad, mert csak a szünetben kapcsolják le", "A Fuchsmajor oltja el minden felszólalás előtt", "A Pater Krampampuli kapcsolja fel a szakestély végén"],
        "answer": "A résztvevők helyet foglalása után lekapcsolják",
        "explanation": "A szakestély kezdetén, miután mindenki elfoglalta a helyét, lekapcsolják a teremben lévő világítást."
    },
    {
        "question": "Mi a 'Sza-sza-szakestély' nóta szerepe a szakestély kezdetén?",
        "options": ["A Cantus ezzel indítja a szakestélyt", "Ezzel jelzik a szakestély végét", "Ez a szünet végét jelző nóta", "Ezt csak a Gyászszakestélyen éneklik"],
        "answer": "A Cantus ezzel indítja a szakestélyt",
        "explanation": "A szakestély kezdetén a Cantus a 'Sza-sza-szakestély' nótát kezdi el, amely alatt a résztvevők megválasztják az Elnököt."
    },
    {
        "question": "Mi a szakestély komoly részének első felszólalása?",
        "options": ["A Komoly pohár", "A Vendégköszöntő nóta", "A Silentium Eks", "A Valete-beszéd"],
        "answer": "A Komoly pohár",
        "explanation": "A Komoly pohár a szakestély első felszólalása, amely a témát érintő beszédként megadja a komoly rész alaphangját."
    },
    {
        "question": "Mit jelent a Silentium Eks a szakestély menetében?",
        "options": ["A komoly rész végét és a szünet kezdetét", "A szakestély megnyitását", "A krampampuli felvezetését", "A balekvizsga eredményének kihirdetését"],
        "answer": "A komoly rész végét és a szünet kezdetét",
        "explanation": "A Silentium Eks akkor következik, amikor az Elnök lezárja a komoly részt, és elkezdődik a szakestély szünete."
    },
    {
        "question": "Melyik nóta jelzi általában a miskolci szakestély szünetének végét?",
        "options": ["A Steingrubeni induló", "A Sza-sza-szakestély", "A Gaudeamus igitur", "A Bányász himnusz"],
        "answer": "A Steingrubeni induló",
        "explanation": "Miskolcon a szünet végét általában a Steingrubeni induló jelzi."
    },
    {
        "question": "Melyik nóta jelzi a szakestély szünetének végét Sopronban?",
        "options": ["A Szerencse fel a tárna vár", "A Steingrubeni induló", "A Dal az elnökhöz", "A Valete nóta"],
        "answer": "A Szerencse fel a tárna vár",
        "explanation": "Sopronban a szünet végét a 'Szerencse fel a tárna vár' jelzi."
    },
    {
        "question": "Mikor lehet a szakestélyen a 'folyó ügyeket' elintézni?",
        "options": ["Nóta alatt, a megfelelő Tempus-formulával és kézjellel", "Bármikor, külön jelzés nélkül", "Csak a Komoly pohár alatt", "Csak a Praeses helyetteseinek engedélyével"],
        "answer": "Nóta alatt, a megfelelő Tempus-formulával és kézjellel",
        "explanation": "Miskolcon a résztvevő nóta alatt, a 'Tempus helyemre és italomra' formulával és a hagyományos kéztartással jelezheti távozási szándékát."
    },
    {
        "question": "Mit jelent az 'Eks!' vezényszó?",
        "options": ["Fenékig kell inni", "Félig kell inni", "Tetszés szerinti mennyiséget kell inni", "A korsót át kell adni a szomszédnak"],
        "answer": "Fenékig kell inni",
        "explanation": "Az Elnök vezényszavai közül az Eks! a korsó fenékig ürítését jelenti."
    },
    {
        "question": "Mit jelent a 'Tükrös!' vezényszó?",
        "options": ["Félig kell inni", "Fenékig kell inni", "Csak egy kortyot kell inni", "A korsót meg kell tölteni"],
        "answer": "Félig kell inni",
        "explanation": "A Tükrös! vezényszó jelentése: a résztvevő félig igyon."
    },
    {
        "question": "Mit jelent a 'Lefety!' vezényszó?",
        "options": ["Tetszés szerinti mértékben kell inni", "Fenékig kell inni", "Félig kell inni", "A korsót le kell tenni"],
        "answer": "Tetszés szerinti mértékben kell inni",
        "explanation": "A Lefety! nem ír elő meghatározott mennyiséget, tetszés szerinti ivást jelent."
    },
    {
        "question": "Melyik állítás igaz a szakestély Házirendjére?",
        "options": ["A legidősebb, keresztelkedés szerint jelen lévő Firma hitelesíti aláírásával és sörével", "A Praeses egyedül írja alá a szakestély előtt", "A Fuchsmajor hitelesíti a balekok nevében", "A Házirendet csak a szakestély végén olvassák fel"],
        "answer": "A legidősebb, keresztelkedés szerint jelen lévő Firma hitelesíti aláírásával és sörével",
        "explanation": "A Háznagy által felolvasott Házirendet a keresztelkedés szerint legidősebb jelenlévő Firma hitelesíti."
    },
    {
        "question": "Mi történik a korsóavatáskor?",
        "options": ["A korsót egy avatási beszéddel és a korsóavató szertartás részeként avatják fel", "A korsót azonnal összetörik", "A korsót a Fuchsmajor kapja meg emlékül", "A korsót csak a szakestély szünetében lehet használni"],
        "answer": "A korsót egy avatási beszéddel és a korsóavató szertartás részeként avatják fel",
        "explanation": "A korsóavatás külön szertartás, amelynek során a korsót beszéddel avatják fel; a hagyomány szerint ezután használható."
    },
    {
        "question": "Mi a 'reibolás' lényege a Gyászszakestélyen?",
        "options": ["Az üres korsó jellegzetes kopogtatása, dörzsölése és összetörése", "A gyászszalagok elégetése", "A bányászlámpák eloltása", "A szakestély teljes elnémítása"],
        "answer": "Az üres korsó jellegzetes kopogtatása, dörzsölése és összetörése",
        "explanation": "A reibolás során az üres korsót meghatározott módon megkopogtatják, az asztalhoz dörzsölik, majd összetörik."
    },
    {
        "question": "Melyik ruhadarab kapcsolódik a mai Gruben történeti elődjéhez?",
        "options": ["A Bibertárói ruha, vagyis a Biberstollen", "A Freibergi fekete ruha", "A tiroli fehér ruha", "A magyaros díszruha"],
        "answer": "A Bibertárói ruha, vagyis a Biberstollen",
        "explanation": "A szakirodalom szerint a mai Gruben valós történeti elődje a Bibertárói ruha, a Biberstollen."
    },
    {
        "question": "Melyik ruhadarab kapcsolódik a mai Bányaing történeti elődjéhez?",
        "options": ["A Freibergi fekete ruha", "A Bibertárói ruha", "A Walden", "Az Atilla"],
        "answer": "A Freibergi fekete ruha",
        "explanation": "A mai Bányaing elődjének a Freibergi fekete ruhát tekintik."
    },
    {
        "question": "Mikor nyerte el nagyjából a mai formáját az akadémiai egyenruha?",
        "options": ["Az Erdészeti palota 1892-es átadásakor", "A Berg-Schola 1735-ös alapításakor", "Az Akadémia 1762-es létrehozásakor", "A miskolci Egyetemváros építésekor"],
        "answer": "Az Erdészeti palota 1892-es átadásakor",
        "explanation": "Az egyenruhákat többször szabályozták, véglegesebb, ma is ismert formájukat az Erdészeti palota átadásakor, 1892-ben nyerték el."
    },
    {
        "question": "Milyen alapanyagú és paszományú a Walden?",
        "options": ["Őzbarna alapú; erdészeknél zöld, faiparosoknál fekete, geodétáknál sötétkék paszományú", "Fekete alapú; erdészeknél meggypiros, faiparosoknál zöld paszományú", "Palackzöld alapú; minden szakon fekete paszományú", "Szürke alapú; minden szakon arany paszományú"],
        "answer": "Őzbarna alapú; erdészeknél zöld, faiparosoknál fekete, geodétáknál sötétkék paszományú",
        "explanation": "A Walden őzbarna anyagból készül, a szakokhoz tartozó paszomány színe pedig eltérő."
    },
    {
        "question": "Hogyan viselik a farbőrt a bányászok?",
        "options": ["Hátul, hogy a vágatokban csúszásra is használható legyen", "Elöl, kötényként", "A vállon átvetve", "A derék mellett oldalt"],
        "answer": "Hátul, hogy a vágatokban csúszásra is használható legyen",
        "explanation": "A bányászok hátul viselték a farbőrt, többek között azért, mert ezen csúsztak le a vágatokba."
    },
    {
        "question": "Hogyan viselik a farbőrt a kohászok?",
        "options": ["Elöl, kötényként", "Hátul, a bányászokhoz hasonlóan", "A sapka alatt", "A vállukon, köpönyegként"],
        "answer": "Elöl, kötényként",
        "explanation": "A kohászok a farbőrt fordítva, elöl, kötényként viselték."
    },
    {
        "question": "Melyik különbség igaz a dunaújvárosi Aufra a miskolcihoz képest?",
        "options": ["Hiányzik a hátsó hasítéka és hat kisgombja, de jobb oldali mellzsebe van", "Hét nagy gombbal záródik és nincs gallérja", "Ezüst gombos és zöld paszományú", "Válltömést kapott, mint a Gruben"],
        "answer": "Hiányzik a hátsó hasítéka és hat kisgombja, de jobb oldali mellzsebe van",
        "explanation": "A dunaújvárosi Auf egyik jellegzetes eltérése a hátsó hasíték és a hat kisgomb hiánya, valamint a jobb oldali mellzseb."
    },
    {
        "question": "Milyen színű paszományt viselnek a bányászok a Grubenen?",
        "options": ["Fekete", "Meggy-piros", "Zöld", "Sötétkék"],
        "answer": "Fekete",
        "explanation": "A Gruben fekete alapú, és a bányászok fekete paszományt viselnek rajta."
    },
    {
        "question": "Milyen színű paszományt viselnek a kohászok a Grubenen?",
        "options": ["Meggy-piros", "Fekete", "Zöld", "Barna"],
        "answer": "Meggy-piros",
        "explanation": "A kohászok Grubenen a paszomány meggy-piros színű."
    },
    {
        "question": "Mi a Selmeci sapka, más néven ködvágó?",
        "options": ["A selmeci hagyomány jellegzetes fejfedője", "A szakestély elnöki szalagja", "A bányászok farbőre", "A balekvizsga indexe"],
        "answer": "A selmeci hagyomány jellegzetes fejfedője",
        "explanation": "A Selmeci sapka vagy ködvágó a selmeci diákhagyomány jellegzetes fejfedője."
    },
    {
        "question": "Mi a Tempus-folt hagyományos jelentése?",
        "options": ["Egy kapcsolat vagy eljegyzés emlékét jelző folt az egyenruhán", "A szakestély szünetének jelzése", "A balekvizsgán kapott bukási jel", "A tisztségviselői szalag helyettesítője"],
        "answer": "Egy kapcsolat vagy eljegyzés emlékét jelző folt az egyenruhán",
        "explanation": "A Tempus-folt a hagyomány szerint egy kapcsolat vagy eljegyzés emlékét őrzi az egyenruhán."
    },
    {
        "question": "Hogyan távolítható el a Tempus-folt, ha a kapcsolat nem házassággal végződik?",
        "options": ["Az anyaggal és a béléssel együtt kivágva; a helye csak nagyobb Tempusszal fedhető el", "Egyszerűen lefejtve és fekete cérnával összevarrva", "A szakestélyen elégetve", "A Fuchsmajor engedélyével lemosva"],
        "answer": "Az anyaggal és a béléssel együtt kivágva; a helye csak nagyobb Tempusszal fedhető el",
        "explanation": "A hagyomány szerint a Tempust az egyenruha anyagával és bélésével együtt vágják ki; a helyét csak nagyobb Tempus fedheti el."
    },
    {
        "question": "Melyik köszöntés kapcsolódik általánosan a selmeci hagyományhoz?",
        "options": ["Jó szerencsét!", "Legyen Fényes Sikere a Kohásznak!", "Világost a Geósnak!", "Sza-sza-szakestély!"],
        "answer": "Jó szerencsét!",
        "explanation": "A 'Jó szerencsét!' a selmeci bányászati-kohászati hagyomány általánosan használt köszöntése."
    },
    {
        "question": "Melyik köszöntés kapcsolódik a kohászokhoz?",
        "options": ["Legyen Fényes Sikere a Kohásznak!", "Világost a Geósnak!", "Jó erdőt!", "Szerencse fel a tárna vár!"],
        "answer": "Legyen Fényes Sikere a Kohásznak!",
        "explanation": "A kohászok köszöntése: 'Legyen Fényes Sikere a Kohásznak!'"
    },
    {
        "question": "Melyik köszöntés kapcsolódik a székesfehérvári geodétákhoz?",
        "options": ["Világost a Geósnak!", "Legyen Fényes Sikere a Kohásznak!", "Jó szerencsét a bányásznak!", "Éljen a Praeses!"],
        "answer": "Világost a Geósnak!",
        "explanation": "A székesfehérvári geodéták köszöntése: 'Világost a Geósnak!'"
    },
    {
        "question": "Mi látható a bányász címer jellegzetes Schlägel und Eisen motívumában?",
        "options": ["Kalapács és nyeles ék", "Bányalámpa és csille", "Kard és pajzs", "Ásó és lapát"],
        "answer": "Kalapács és nyeles ék",
        "explanation": "A Schlägel und Eisen a bányászati jelképpé vált kalapácsot és nyeles éket ábrázolja."
    },
    {
        "question": "Mi volt a kamara Selmecbányán?",
        "options": ["A diákok által bérelt kis szoba vagy lakás", "A szakestély elnökségi asztala", "A bányatárspénztár épülete", "Az egyenruhák tárolóhelye"],
        "answer": "A diákok által bérelt kis szoba vagy lakás",
        "explanation": "Mivel nem volt kollégium, a diákok magánházaknál béreltek szobát vagy kisebb lakást, ezt nevezték kamarának."
    },
    {
        "question": "Mit jelentett a Verschiess?",
        "options": ["A legszigorúbb büntetést, a kiközösítést", "A szakestély szünetét", "A balekkeresztelő kezdetét", "A sörpárbaj győzelmét"],
        "answer": "A legszigorúbb büntetést, a kiközösítést",
        "explanation": "A Verschiess a közösségből való kiközösítést jelentette, vagyis a hagyományos büntetések legsúlyosabb formáját."
    },
    {
        "question": "Melyik állítás igaz a 'Filiszter' szóra?",
        "options": ["Régen a diákság jókedvét értetlenül néző polgárt, ma gyakran elvalétált hallgatót jelent", "Mindig az elsőéves hallgatót jelentette", "A szakestély elnökének másik neve", "A balekvizsga hivatalos neve"],
        "answer": "Régen a diákság jókedvét értetlenül néző polgárt, ma gyakran elvalétált hallgatót jelent",
        "explanation": "A szó jelentése történetileg változott: eredetileg a diákság életét nem értő polgárra, ma pedig az egyetemi éveit befejező hallgatóra is használják."
    },
    {
        "question": "Mit jelent a 'Valete!'?",
        "options": ["Éljetek boldogul!", "Jó szerencsét!", "Igyunk fenékig!", "Csendet kérek!"],
        "answer": "Éljetek boldogul!",
        "explanation": "A Valete latin eredetű búcsúformula, jelentése: éljetek boldogul."
    }
]


LEADERBOARD_DB = Path(__file__).with_name("leaderboard.db")


def initialize_leaderboard():
    connection = sqlite3.connect(LEADERBOARD_DB)
    try:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS leaderboard (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                score INTEGER NOT NULL,
                total INTEGER NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        connection.commit()
    finally:
        connection.close()


def get_leaderboard():
    connection = sqlite3.connect(LEADERBOARD_DB)
    try:
        return connection.execute(
            """
            SELECT name, score, total
            FROM leaderboard
            ORDER BY score * 1.0 / total DESC, score DESC, created_at ASC
            LIMIT 10
            """
        ).fetchall()
    finally:
        connection.close()


def save_leaderboard_entry(name, score, total):
    connection = sqlite3.connect(LEADERBOARD_DB)
    try:
        connection.execute(
            """
            INSERT INTO leaderboard (name, score, total, created_at)
            VALUES (?, ?, ?, datetime('now'))
            """,
            (name, score, total),
        )
        connection.commit()
    finally:
        connection.close()


def build_wrong_answer_explanation(question, user_answer):
    correct_answer = question["answer"]
    source_explanation = question["explanation"]

    if user_answer is None:
        return (
            f"Erre a kérdésre nem érkezett válasz. A helyes válasz: "
            f"'{correct_answer}'. {source_explanation}"
        )

    return (
        f"Azért volt hibás, mert nem a '{user_answer}' a helyes válasz, hanem "
        f"'{correct_answer}'. {source_explanation}"
    )


def render_question_report_button(question, report_key):
    if st.button("Hibáztam? Segíts kijavítani!", key=f"report-button-{report_key}"):
        st.session_state.report_question = {
            "report_key": report_key,
            "question": question["question"],
            "options": question["options"],
            "answer": question["answer"],
        }
        st.session_state.report_text = ""


def render_question_report_form(report_key):
    report_question = st.session_state.get("report_question")
    if report_question is not None and report_question["report_key"] == report_key:
        st.warning(
            f"Jelentett kérdés: **{report_question['question']}**"
        )
        report_text = st.text_area(
            "Írd le, mi lenne helyes, vagy mi a probléma!",
            key="report_text",
        )
        if report_text.strip():
            options = "\n".join(
                f"- {option}" for option in report_question["options"]
            )
            email_body = (
                "Szia!\n\n"
                "Hibát szeretnék jelenteni a balekvizsga egyik kérdésében.\n\n"
                f"Kérdés:\n{report_question['question']}\n\n"
                f"Válaszlehetőségek:\n{options}\n\n"
                f"Jelenlegi helyes válasz: {report_question['answer']}\n\n"
                f"Javasolt javítás / megjegyzés:\n{report_text.strip()}"
            )
            mailto_url = (
                "mailto:nagymark2357@gmail.com"
                f"?subject={quote('balekvizsga kérdés javítása')}"
                f"&body={quote(email_body)}"
            )
            st.link_button(
                "Jelentés megnyitása az e-mailben",
                mailto_url,
                use_container_width=True,
            )


initialize_leaderboard()

if "page" not in st.session_state:
    st.session_state.page = "welcome"

if st.session_state.page == "welcome":
    st.title("balekvizsgára")
    st.subheader("Üdvözöllek a balekvizsgán!")
    st.write(
        "Teszteld a tudásodat a selmeci hagyományokról, a szakestélyekről "
        "és az egyenruhákról."
    )

    if st.button("Készülj fel!", type="primary", use_container_width=True):
        st.session_state.page = "quiz"
        st.session_state.quiz_questions = None
        st.session_state.user_answers = {}
        st.session_state.current_question = 0
        st.session_state.submitted = False
        st.session_state.leaderboard_saved = False
        st.rerun()

    st.subheader("Leaderboard")
    leaderboard = get_leaderboard()
    if leaderboard:
        st.table(
            [
                {
                    "Helyezés": index,
                    "Név": name,
                    "Pontszám": f"{score} / {total}",
                }
                for index, (name, score, total) in enumerate(leaderboard, start=1)
            ]
        )
    else:
        st.info("Még nincs eredmény a ranglistán. Légy te az első!")

    st.stop()


st.title("balekvizsgára")

# 50 véletlenszerű kérdés kiválasztása és a válaszlehetőségek megkeverése munkamenetenként egyszer
if not st.session_state.get("quiz_questions"):
    sample_size = min(50, len(ALL_QUESTIONS))
    selected = random.sample(ALL_QUESTIONS, sample_size)

    # Keverjük meg az opciókat, hogy ne mindig az első legyen a helyes válasz
    prepared_questions = []
    for q in selected:
        shuffled_opts = q["options"].copy()
        random.shuffle(shuffled_opts)
        prepared_questions.append({
            "question": q["question"],
            "options": shuffled_opts,
            "answer": q["answer"],
            "explanation": q["explanation"]
        })
    st.session_state.quiz_questions = prepared_questions

if "user_answers" not in st.session_state:
    st.session_state.user_answers = {}
if "submitted" not in st.session_state:
    st.session_state.submitted = False
if "leaderboard_saved" not in st.session_state:
    st.session_state.leaderboard_saved = False

if st.session_state.submitted:
    score = sum(
        st.session_state.user_answers.get(i) == q["answer"]
        for i, q in enumerate(st.session_state.quiz_questions)
    )
    st.metric(label="Végső pontszám", value=f"{score} / {len(st.session_state.quiz_questions)}")
    st.subheader("Gyakorolandó kérdések")

    incorrect_questions = [
        (i, q, st.session_state.user_answers.get(i))
        for i, q in enumerate(st.session_state.quiz_questions)
        if st.session_state.user_answers.get(i) != q["answer"]
    ]

    if not incorrect_questions:
        st.success("Minden kérdésre helyesen válaszoltál!")

    for i, q, user_ans in incorrect_questions:
        st.markdown(f"**{i + 1}. kérdés: {q['question']}**")
        valasz_szoveg = user_ans if user_ans is not None else "Nem válaszoltál"
        st.error(f"A te válaszod: '{valasz_szoveg}'. A helyes válasz: '{q['answer']}'.")
        st.info(f"**Miért volt hibás?** {build_wrong_answer_explanation(q, user_ans)}")
    if not st.session_state.leaderboard_saved:
        st.subheader("Felkerüljön az eredményed a leaderboardra?")
        wants_to_join = st.checkbox("Igen, szeretném beküldeni az eredményemet.")
        if wants_to_join:
            leaderboard_name = st.text_input("Név a leaderboardon", max_chars=30)
            if st.button("Eredmény beküldése", disabled=not leaderboard_name.strip()):
                save_leaderboard_entry(
                    leaderboard_name.strip(),
                    score,
                    len(st.session_state.quiz_questions),
                )
                st.session_state.leaderboard_saved = True
                st.success("Az eredményed felkerült a leaderboardra!")
                st.rerun()

    if st.button("Vissza a kezdőlapra"):
        st.session_state.clear()
        st.session_state.page = "welcome"
        st.rerun()
else:
    question_index = st.session_state.get("current_question", 0)
    question_count = len(st.session_state.quiz_questions)
    question = st.session_state.quiz_questions[question_index]
    saved_answer = st.session_state.user_answers.get(question_index)
    burst_event = st.session_state.get("answer_burst")

    if burst_event is not None and burst_event["question_index"] == question_index:
        burst_class = "correct" if burst_event["is_correct"] else "wrong"
        st.markdown(
            f'<div class="answer-burst answer-burst--{burst_class}"></div>',
            unsafe_allow_html=True,
        )
        st.session_state.pop("answer_burst", None)

    with st.container(key=f"question-slide-{question_index}"):
        st.progress((question_index + 1) / question_count)
        st.markdown(
            f'<p class="quiz-counter">{question_index + 1} / {question_count}. kérdés</p>',
            unsafe_allow_html=True,
        )
        report_button_column = st.columns([1, 2])[1]
        with report_button_column:
            with st.container(key=f"question-report-{question_index}"):
                render_question_report_button(question, f"quiz-{question_index}")
        render_question_report_form(f"quiz-{question_index}")
        st.subheader(question["question"])

        for option_index, option in enumerate(question["options"]):
            is_selected = option == saved_answer
            is_correct = is_selected and saved_answer == question["answer"]
            answer_state = "correct" if is_correct else "wrong" if is_selected else "idle"
            option_label = f"{'✓' if is_correct else '✕'} {option}" if is_selected else option
            with st.container(key=f"answer-choice-{answer_state}-{question_index}-{option_index}"):
                if st.button(
                    option_label,
                    key=f"answer-{question_index}-{option_index}",
                    type="primary" if is_correct else "secondary",
                    disabled=saved_answer is not None,
                    use_container_width=True,
                ):
                    st.session_state.user_answers[question_index] = option
                    st.session_state.answer_burst = {
                        "question_index": question_index,
                        "is_correct": option == question["answer"],
                    }
                    st.rerun()

        selected_answer = saved_answer
        if selected_answer is not None:
            if selected_answer == question["answer"]:
                st.success("Helyes válasz!")
            else:
                st.error(f"Helytelen. A helyes válasz: {question['answer']}")
                st.info(
                    f"**Miért volt hibás?** "
                    f"{build_wrong_answer_explanation(question, selected_answer)}"
                )
        back_column, next_column = st.columns(2)
        with back_column:
            if st.button("← Előző", disabled=question_index == 0, use_container_width=True):
                st.session_state.current_question = question_index - 1
                st.rerun()

        with next_column:
            is_last_question = question_index == question_count - 1
            if is_last_question:
                if st.button(
                    "Eredmény megtekintése",
                    disabled=selected_answer is None,
                    use_container_width=True,
                ):
                    st.session_state.submitted = True
                    st.rerun()
            elif st.button(
                "Következő →",
                disabled=selected_answer is None,
                use_container_width=True,
            ):
                st.session_state.current_question = question_index + 1
                st.rerun()