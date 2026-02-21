<a name="readme-top"></a>

<div align="center">
  <img src="custom_components/mistral_conversation/icon@2x.png" alt="Mistral AI Conversation" width="128" height="128">

  <h1>Mistral AI Conversation</h1>
  <p><strong>Een Home Assistant custom integratie die Mistral AI beschikbaar maakt als volwaardige gespreksagent in de spraakassistent.</strong></p>

  [![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge)](https://github.com/hacs/integration)
  [![HA Version](https://img.shields.io/badge/Home%20Assistant-2023.5%2B-blue?style=for-the-badge&logo=home-assistant)](https://www.home-assistant.io/)
  [![Mistral AI](https://img.shields.io/badge/Mistral%20AI-Powered-orange?style=for-the-badge)](https://mistral.ai/)
  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)
</div>

---

## Inhoudsopgave

1. [Over dit project](#over-dit-project)
2. [Wat is Mistral AI?](#wat-is-mistral-ai)
3. [Functies](#functies)
4. [Vereisten](#vereisten)
5. [Installatie](#installatie)
   - [Via HACS](#via-hacs-aanbevolen)
   - [Handmatig](#handmatige-installatie)
6. [Configuratie](#configuratie)
   - [API-sleutel aanmaken](#api-sleutel-aanmaken)
   - [Integratie instellen](#integratie-instellen)
   - [Als spraakassistent instellen](#als-spraakassistent-instellen)
7. [Opties](#opties)
   - [Beschikbare modellen](#beschikbare-modellen)
   - [Systeemprompt](#systeemprompt)
   - [Temperature](#temperature)
8. [Apparaten bedienen](#apparaten-bedienen)
9. [Gebruik als service-actie](#gebruik-als-service-actie)
10. [Voorbeeldprompts](#voorbeeldprompts)
11. [Verschil met BlaXun integratie](#verschil-met-blaxun-integratie)
12. [Veelgestelde vragen](#veelgestelde-vragen)
13. [Licentie](#licentie)

---

## Over dit project

Deze integratie breidt de originele [BlaXun Mistral AI integratie](https://github.com/BlaXun/home_assistant_mistral_ai) uit met de functionaliteit om Mistral AI te gebruiken als **volwaardige conversatie-agent** in de ingebouwde Home Assistant spraakassistent (Assist). Waar de originele integratie werkt via service-aanroepen en events, integreert deze versie diepgaand met HA's conversation-platform — net zoals de officiële Google Gemini en OpenAI integraties.

<p align="right">(<a href="#readme-top">terug naar boven</a>)</p>

---

## Wat is Mistral AI?

[Mistral AI](https://mistral.ai/) is een Frans AI-bedrijf dat krachtige taalmodellen ontwikkelt. Hun modellen scoren hoog op benchmarks, zijn beschikbaar via een betaalbare API en worden gerund vanuit Europa — wat gunstig is voor privacy (GDPR).

Mistral biedt zowel open als gesloten modellen aan, van de lichtgewicht `mistral-7b` tot het krachtige `mistral-large`. Ze zijn bekend om hun efficiëntie: goede prestaties voor een lage prijs per token.

<p align="right">(<a href="#readme-top">terug naar boven</a>)</p>

---

## Functies

- ✅ **Selecteerbaar als gespreksagent** in *Instellingen → Spraakassistenten*
- ✅ **Volledig instelbaar via de UI** — geen YAML vereist
- ✅ **Keuze uit meerdere Mistral-modellen** (large, medium, small, nemo, ...)
- ✅ **Home Assistant bedienen** via spraak of tekst (lampen, schakelaars, covers, ...)
- ✅ **Gespreksgeheugen** — context blijft bewaard gedurende een sessie
- ✅ **Meertalig** — antwoordt in de taal van de gebruiker
- ✅ **Jinja2 templates** in de systeemprompt (gebruik `{{ now() }}`, `{{ ha_name }}` etc.)
- ✅ **Instelbare creativiteit** via temperature slider (0.0–1.0)
- ✅ **Veiligheidscheck** op service-aanroepen — alleen bekende services worden uitgevoerd
- ✅ **Geen extra Python packages** — gebruikt HA's ingebouwde `aiohttp`

<p align="right">(<a href="#readme-top">terug naar boven</a>)</p>

---

## Vereisten

| Vereiste | Minimale versie |
|---|---|
| Home Assistant Core | 2023.5 |
| Python | 3.11 |
| Mistral AI account | — |
| Mistral API-sleutel | — |

<p align="right">(<a href="#readme-top">terug naar boven</a>)</p>

---

## Installatie

### Via HACS (aanbevolen)

1. Zorg dat [HACS](https://hacs.xyz/) geïnstalleerd is
2. Ga in HACS naar **Integraties**
3. Klik rechtsboven op de **drie puntjes** → **Aangepaste repositories**
4. Vul in:
   - **URL:** `https://github.com/JOUW-GEBRUIKER/mistral_conversation`
   - **Categorie:** Integratie
5. Klik **Toevoegen**, sluit het venster
6. Zoek op **"Mistral AI Conversation"** en klik **Downloaden**
7. Herstart Home Assistant

### Handmatige installatie

1. Download de nieuwste release als `.zip`
2. Pak uit en kopieer de map `custom_components/mistral_conversation/` naar:
   ```
   /config/custom_components/mistral_conversation/
   ```
3. **Verwijder eventuele `.pyc` cachebestanden** van een vorige installatie:
   ```bash
   rm -rf /config/custom_components/mistral_conversation/__pycache__
   ```
4. Herstart Home Assistant volledig (niet alleen herladen)

<p align="right">(<a href="#readme-top">terug naar boven</a>)</p>

---

## Configuratie

### API-sleutel aanmaken

1. Maak een account aan op [mistral.ai](https://mistral.ai/)
2. Ga naar [console.mistral.ai/api-keys](https://console.mistral.ai/api-keys)
3. Klik **Create new key**
4. Kopieer de sleutel (je ziet hem maar één keer!)

> **Tip:** Mistral biedt een gratis tier aan. Controleer de actuele limieten op [mistral.ai/pricing](https://mistral.ai/pricing/).

### Integratie instellen

1. Ga naar **Instellingen → Apparaten & Diensten**
2. Klik rechtsonder op **+ Integratie toevoegen**
3. Zoek op **Mistral AI Conversation**
4. Voer je **API-sleutel** in
5. Klik **Voltooien**

De integratie verschijnt nu onder Apparaten & Diensten.

### Als spraakassistent instellen

1. Ga naar **Instellingen → Spraakassistenten**
2. Klik op je assistent (standaard heet die "Home Assistant")
3. Kies bij **Gespreksagent** de optie **Mistral AI Conversation**
4. Klik **Opslaan**

Vanaf nu verwerkt Mistral AI alle gesprekken via je assistent.

<p align="right">(<a href="#readme-top">terug naar boven</a>)</p>

---

## Opties

Klik op de integratie in **Instellingen → Apparaten & Diensten** en dan op **Configureren** om de opties aan te passen.

| Optie | Standaard | Beschrijving |
|---|---|---|
| **Systeemprompt** | Zie hieronder | Instructies voor de AI. Ondersteunt Jinja2 templates. |
| **Model** | `mistral-large-latest` | Welk Mistral-model gebruikt wordt |
| **Max tokens** | `1024` | Maximale lengte van het AI-antwoord |
| **Temperature** | `0.7` | Creativiteit van de antwoorden (0.0–1.0) |
| **HA bedienen** | Aan | Of de AI je apparaten mag bedienen |

### Beschikbare modellen

| Model | Beschrijving | Aanbevolen voor |
|---|---|---|
| `mistral-large-latest` | Krachtigste model, beste begrip | Dagelijks gebruik, complexe vragen |
| `mistral-medium-latest` | Goede balans kwaliteit / kosten | Algemeen gebruik |
| `mistral-small-latest` | Snel en goedkoop | Eenvoudige commando's |
| `open-mistral-nemo` | Compact open source model | Lage latentie |
| `open-codestral-mamba` | Gespecialiseerd in code | Code genereren via automations |
| `mistral-7b-latest` | Kleinste model, snelst | Snelle antwoorden |

> **Aanbeveling:** Start met `mistral-large-latest` voor de beste resultaten bij het bedienen van je huis.

### Systeemprompt

De systeemprompt bepaalt hoe de AI zich gedraagt. Je kunt Jinja2 templates gebruiken:

```jinja2
Je bent een behulpzame spraakassistent voor het slimme huis genaamd {{ ha_name }}.
Antwoord altijd in het Nederlands, tenzij de gebruiker een andere taal spreekt.
Vandaag is het {{ now().strftime('%A %d %B %Y') }}.
De tijd is nu {{ now().strftime('%H:%M') }}.
Wees vriendelijk, bondig en to-the-point.
```

**Beschikbare template-variabelen:**

| Variabele | Omschrijving |
|---|---|
| `{{ ha_name }}` | Naam van je Home Assistant installatie |
| `{{ now() }}` | Huidige datum en tijd |
| `{{ now().strftime(...) }}` | Opgemaakte datum/tijd |

### Temperature

De temperature bepaalt hoe creatief of voorspelbaar de AI antwoorden geeft:

| Waarde | Gedrag |
|---|---|
| `0.0` | Deterministisch — altijd hetzelfde antwoord |
| `0.3` | Conservatief, nauwkeurig |
| `0.7` | Gebalanceerd (aanbevolen) |
| `1.0` | Creatief, variabel |

> **Let op:** Mistral's temperatuurbereik is `0.0–1.0`, afwijkend van sommige andere modellen.

<p align="right">(<a href="#readme-top">terug naar boven</a>)</p>

---

## Apparaten bedienen

Als **"Laat AI Home Assistant bedienen"** is ingeschakeld, kan de AI entiteiten in je huis bedienen.

### Stap 1: Entiteiten blootstellen

Ga naar **Instellingen → Spraakassistenten → Blootgestelde apparaten** en zet de entiteiten aan die de AI mag zien en bedienen.

### Stap 2: Praten

Vraag gewoon wat je wilt:

| Wat je zegt | Wat de AI doet |
|---|---|
| "Zet de keukenlamp aan" | `light.turn_on` op de keukenlamp |
| "Doe alle lichten uit" | `light.turn_off` op alle lichten |
| "Open de gordijnen" | `cover.open_cover` |
| "Vergrendel de voordeur" | `lock.lock` |
| "Zet de tv aan" | `media_player.turn_on` |
| "Schakel de ventilator om" | `fan.toggle` |

### Ondersteunde domeinen

De integratie ondersteunt de volgende HA-domeinen voor veilige service-aanroepen:

`light` · `switch` · `cover` · `media_player` · `fan` · `climate` · `lock` · `alarm_control_panel` · `scene` · `script` · `automation` · `homeassistant`

<p align="right">(<a href="#readme-top">terug naar boven</a>)</p>

---

## Gebruik als service-actie

Naast de spraakassistent kun je de integratie ook gebruiken via de standaard `conversation.process` service-actie. Dit is handig in automations en scripts:

```yaml
action: conversation.process
data:
  agent_id: conversation.mistral_ai_conversation
  text: "Wat is de staat van de keukenlamp?"
response_variable: result
```

Het antwoord vind je in `result.response.speech.plain.speech`.

### Voorbeeld: Dynamische pushmelding

```yaml
alias: Slimme deurbelmelding
sequence:
  - action: conversation.process
    data:
      agent_id: conversation.mistral_ai_conversation
      text: >
        De deurbel heeft een foto gemaakt. Beschrijf in één zin wat er voor
        de deur kan zijn, gebaseerd op tijdstip {{ now().strftime('%H:%M') }}.
    response_variable: ai_result
  - action: notify.mobile_app
    data:
      title: "Deurbel 🔔"
      message: "{{ ai_result.response.speech.plain.speech }}"
```

### Voorbeeld: Ochtendrapport

```yaml
alias: Ochtendrapport
sequence:
  - action: conversation.process
    data:
      agent_id: conversation.mistral_ai_conversation
      text: >
        Geef een korte samenvatting voor mijn dag. Buiten is het
        {{ states('sensor.buiten_temperatuur') }}°C.
        Ik heb {{ states('calendar.werk') }} vandaag.
    response_variable: rapport
  - action: tts.speak
    target:
      entity_id: tts.google_translate_nl
    data:
      media_player_entity_id: media_player.woonkamer
      message: "{{ rapport.response.speech.plain.speech }}"
```

<p align="right">(<a href="#readme-top">terug naar boven</a>)</p>

---

## Voorbeeldprompts

Hier zijn wat ideeën voor wat je aan de assistent kunt vragen:

**Informatie over je huis:**
- *"Hoeveel lampen zijn er momenteel aan?"*
- *"Wat is de temperatuur in de woonkamer?"*
- *"Is de achterdeur vergrendeld?"*

**Bedienen:**
- *"Zet alle lampen in de slaapkamer uit"*
- *"Zet de thermostaat op 20 graden"*
- *"Activeer de 'Film kijken' scene"*

**Algemene vragen:**
- *"Wat kan ik vanavond koken met pasta en kaas?"*
- *"Stel een timer in voor 10 minuten"*
- *"Wat is het nieuws vandaag?"*

<p align="right">(<a href="#readme-top">terug naar boven</a>)</p>

---

## Verschil met BlaXun integratie

Deze integratie is gebaseerd op en geïnspireerd door de [originele BlaXun Mistral AI integratie](https://github.com/BlaXun/home_assistant_mistral_ai). De voornaamste verschillen:

| Functie | BlaXun mistral_ai_api | Mistral AI Conversation |
|---|---|---|
| Gespreksagent in HA Assist | ❌ | ✅ |
| Selecteerbaar in Spraakassistenten | ❌ | ✅ |
| UI-configuratie | Beperkt (YAML) | ✅ Volledig via UI |
| HA apparaten bedienen | ❌ | ✅ |
| Gespreksgeheugen (context) | Handmatig via `conversation_id` | ✅ Automatisch |
| Gebruik als service-actie | ✅ | ✅ via `conversation.process` |
| Mistral Agents (agent_id) | ✅ | ❌ (gepland) |
| Sensor entity (state) | ✅ | ❌ |
| Event bij antwoord | ✅ | ❌ |

Gebruik je de BlaXun integratie voor automation-gebaseerde flows? Dan kun je die gewoon naast deze integratie blijven gebruiken.

<p align="right">(<a href="#readme-top">terug naar boven</a>)</p>

---

## Veelgestelde vragen

**Q: Ik zie de integratie niet in de dropdown bij Spraakassistenten.**  
A: Zorg dat je een **volledige herstart** hebt gedaan (niet alleen "opnieuw laden"). Verwijder ook eventuele `__pycache__` mappen.

**Q: Ik krijg een 400 Bad Request fout.**  
A: Controleer of je temperature tussen 0.0 en 1.0 staat. Mistral accepteert geen hogere waarden.

**Q: De AI antwoordt in het Engels terwijl ik Nederlands spreek.**  
A: Pas de systeemprompt aan: voeg toe `Antwoord altijd in het Nederlands.`

**Q: Kan ik meerdere instanties draaien (bijv. één per kamer)?**  
A: Ja — voeg de integratie meerdere keren toe met verschillende API-sleutels en systeem-prompts.

**Q: Hoe duur is het gebruik?**  
A: Zie [mistral.ai/pricing](https://mistral.ai/pricing/). Voor normaal thuisgebruik verwacht je enkele centen per dag met `mistral-small`.

**Q: Worden mijn gesprekken opgeslagen?**  
A: Mistral AI verwerkt je verzoeken via hun servers. Raadpleeg hun [privacybeleid](https://mistral.ai/privacy-policy) voor details.

<p align="right">(<a href="#readme-top">terug naar boven</a>)</p>

---

## Licentie

Gedistribueerd onder de MIT-licentie. Zie `LICENSE` voor meer informatie.

<p align="right">(<a href="#readme-top">terug naar boven</a>)</p>

---

<div align="center">
  Gemaakt met ❤️ voor de Home Assistant community<br>
  Gebaseerd op het werk van <a href="https://github.com/BlaXun/home_assistant_mistral_ai">BlaXun</a>
</div>
