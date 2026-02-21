<a name="readme-top"></a>

<div align="center">
  <img src="custom_components/mistral_conversation/icon@2x.png" alt="Mistral AI Conversation" width="128" height="128">

  <h1>Mistral AI Conversation</h1>
  <p><strong>Home Assistant integratie met Mistral AI als gespreksagent, spraakherkenning (STT) en ondersteuning voor Mistral Agents.</strong></p>

  [![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge)](https://github.com/hacs/integration)
  [![HA Version](https://img.shields.io/badge/Home%20Assistant-2023.5%2B-blue?style=for-the-badge&logo=home-assistant)](https://www.home-assistant.io/)
  [![Mistral AI](https://img.shields.io/badge/Mistral%20AI-Powered-orange?style=for-the-badge)](https://mistral.ai/)
  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)
</div>

---

## Inhoudsopgave

1. [Over dit project](#over-dit-project)
2. [Functies](#functies)
3. [Vereisten](#vereisten)
4. [Installatie](#installatie)
5. [Configuratie](#configuratie)
   - [API-sleutel aanmaken](#api-sleutel-aanmaken)
   - [Integratie instellen](#integratie-instellen)
   - [Als spraakassistent instellen](#als-spraakassistent-instellen)
6. [Opties & Modi](#opties--modi)
   - [Model-modus](#model-modus)
   - [Agent-modus](#agent-modus)
7. [Spraakherkenning (STT)](#spraakherkenning-stt)
8. [Apparaten bedienen](#apparaten-bedienen)
9. [Gebruik als service-actie](#gebruik-als-service-actie)
10. [Voorbeeldprompts](#voorbeeldprompts)
11. [Veelgestelde vragen](#veelgestelde-vragen)
12. [Licentie](#licentie)

---

## Over dit project

Deze integratie maakt **Mistral AI** beschikbaar als volwaardige gespreksagent in Home Assistant. Je kunt kiezen tussen:

- **Model-modus**: Configureer alles direct in HA (model, prompt, temperature, etc.)
- **Agent-modus**: Gebruik een vooraf geconfigureerde Agent uit de [Mistral Console](https://console.mistral.ai/build/agents) — inclusief eigen tools, systeem-prompt en web search

Daarnaast biedt de integratie **spraakherkenning (STT)** via Mistral's Voxtral-model, zodat je gesproken vragen rechtstreeks kunt laten omzetten naar tekst in de HA Assist-pipeline.

> **Let op: TTS (tekst-naar-spraak)** wordt momenteel **niet** aangeboden door de Mistral API. Gebruik hiervoor een andere HA TTS provider (bijv. Google TTS, Piper, of ElevenLabs).

<p align="right">(<a href="#readme-top">terug naar boven</a>)</p>

---

## Functies

| Functie | Status | Beschrijving |
|---|---|---|
| Gespreksagent in HA Assist | ✅ | Selecteerbaar als agent in Spraakassistenten |
| Model-modus | ✅ | Directe toegang tot Mistral-modellen |
| Agent-modus | ✅ | Gebruik geconfigureerde Agents uit Mistral Console |
| Spraakherkenning (STT) | ✅ | Voxtral Mini via `/v1/audio/transcriptions` |
| TTS (spraaksynthese) | ❌ | Niet beschikbaar in Mistral API |
| HA apparaten bedienen | ✅ | Lampen, schakelaars, covers, etc. |
| Gespreksgeheugen | ✅ | Context blijft bewaard per sessie |
| Jinja2 systeemprompt | ✅ | Templates met `{{ now() }}`, `{{ ha_name }}` etc. |
| Meertalig | ✅ | Antwoordt in de taal van de gebruiker |

<p align="right">(<a href="#readme-top">terug naar boven</a>)</p>

---

## Vereisten

| Vereiste | Minimale versie |
|---|---|
| Home Assistant Core | 2023.5 |
| Python | 3.11 |
| Mistral AI account + API-sleutel | — |

<p align="right">(<a href="#readme-top">terug naar boven</a>)</p>

---

## Installatie

### Via HACS (aanbevolen)

1. HACS → **Integraties** → ⋮ → **Aangepaste repositories**
2. URL: `https://github.com/JOUW-GEBRUIKER/mistral_conversation` — categorie: **Integratie**
3. Zoek "Mistral AI Conversation" → **Downloaden**
4. Herstart Home Assistant volledig

### Handmatig

1. Kopieer de map `custom_components/mistral_conversation/` naar `/config/custom_components/`
2. Verwijder eventuele `__pycache__` mappen van een oude versie:
   ```bash
   rm -rf /config/custom_components/mistral_conversation/__pycache__
   ```
3. **Volledig herstarten** (niet alleen herladen)

<p align="right">(<a href="#readme-top">terug naar boven</a>)</p>

---

## Configuratie

### API-sleutel aanmaken

1. Maak een account aan op [mistral.ai](https://mistral.ai/)
2. Ga naar [console.mistral.ai/api-keys](https://console.mistral.ai/api-keys)
3. Klik **Create new key** en kopieer de sleutel

### Integratie instellen

1. **Instellingen → Apparaten & Diensten → + Integratie toevoegen**
2. Zoek **Mistral AI Conversation**
3. Voer je API-sleutel in → Klik **Voltooien**

### Als spraakassistent instellen

1. **Instellingen → Spraakassistenten** → klik op je assistent
2. Kies bij **Gespreksagent**: **Mistral AI Conversation**
3. Kies bij **Spraak naar tekst**: **Mistral AI STT (Voxtral)** *(optioneel)*
4. Sla op

<p align="right">(<a href="#readme-top">terug naar boven</a>)</p>

---

## Opties & Modi

Klik op de integratie → **Configureren** om de opties te wijzigen.

### Model-modus

Gebruik deze modus als je de AI volledig in HA wilt configureren.

| Optie | Standaard | Beschrijving |
|---|---|---|
| **Modus** | Model | Selecteer "Model" |
| **AI-model** | `mistral-large-latest` | Welk Mistral-model wordt gebruikt |
| **Systeemprompt** | Zie hieronder | Instructies voor de AI (Jinja2 ondersteund) |
| **Temperature** | `0.7` | Creativiteit (0.0–1.0) |
| **Max tokens** | `1024` | Maximale antwoordlengte |

#### Beschikbare modellen

| Model | Gebruik |
|---|---|
| `mistral-large-latest` | Krachtigst, beste begrip — aanbevolen |
| `mistral-medium-latest` | Goed evenwicht kwaliteit/kosten |
| `mistral-small-latest` | Snel en goedkoop |
| `open-mistral-nemo` | Open source compact model |
| `open-codestral-mamba` | Gespecialiseerd in code |
| `mistral-7b-latest` | Kleinste, snelste model |

#### Voorbeeld systeemprompt

```jinja2
Je bent een behulpzame spraakassistent voor {{ ha_name }}.
Antwoord in het Nederlands, tenzij de gebruiker een andere taal spreekt.
Vandaag is het {{ now().strftime('%A %d %B %Y') }}, tijd: {{ now().strftime('%H:%M') }}.
Wees vriendelijk en bondig.
```

### Agent-modus

Gebruik deze modus om een vooraf geconfigureerde Agent uit de Mistral Console te gebruiken. De agent heeft zijn eigen:
- Model
- Systeem-prompt / instructies
- Ingebouwde tools (web search, code interpreter, document library, etc.)

#### Stap 1: Agent aanmaken in Mistral Console

1. Ga naar [console.mistral.ai/build/agents](https://console.mistral.ai/build/agents)
2. Klik **Create new agent**
3. Stel in: naam, model, instructies, en optioneel tools (bijv. web search)
4. Kopieer het **Agent ID** — dit begint met `ag_...`

#### Stap 2: Agent ID invullen in HA

1. Ga naar de integratie-opties in HA
2. Selecteer modus: **Agent**
3. Plak het Agent ID in het veld **Agent ID**
4. Sla op

> **Tip:** Agents zijn ideaal als je wilt dat de AI toegang heeft tot web search, eigen kennisbanken (RAG), of andere geavanceerde tools die je in de console hebt geconfigureerd.

<p align="right">(<a href="#readme-top">terug naar boven</a>)</p>

---

## Spraakherkenning (STT)

De integratie registreert automatisch een **Voxtral STT-entiteit** (`stt.mistral_ai_stt_voxtral`).

### Instellen als STT in de Assist-pipeline

1. **Instellingen → Spraakassistenten** → klik op je assistent
2. Kies bij **Spraak naar tekst**: **Mistral AI STT (Voxtral)**
3. Sla op

### Voxtral specificaties

| Eigenschap | Waarde |
|---|---|
| Model | `voxtral-mini-latest` |
| Maximale audio-duur | 30 minuten |
| Ondersteunde formaten | WAV, OGG |
| Sample rate | 16.000 Hz (16-bit mono) |
| Taaldetectie | Automatisch of handmatig |
| Prijzen | ~$0.003 per minuut |

### Taal instellen

In de opties kun je een taalcode opgeven bij **STT taalcode** voor betere accuratesse:

| Taal | Code |
|---|---|
| Nederlands | `nl` |
| Engels | `en` |
| Duits | `de` |
| Frans | `fr` |
| Spaans | `es` |
| Automatisch | *(leeg laten)* |

<p align="right">(<a href="#readme-top">terug naar boven</a>)</p>

---

## Apparaten bedienen

Als **"Laat AI Home Assistant bedienen"** is ingeschakeld in de opties, kan de AI entiteiten in je huis besturen.

### Blootgestelde apparaten instellen

Ga naar **Instellingen → Spraakassistenten → Blootgestelde apparaten** om te bepalen welke entiteiten de AI mag zien en bedienen.

### Ondersteunde commando's

| Wat je zegt | Wat er gebeurt |
|---|---|
| "Zet de keukenlamp aan" | `light.turn_on` |
| "Doe alle lichten uit" | `light.turn_off` |
| "Open de gordijnen" | `cover.open_cover` |
| "Vergrendel de voordeur" | `lock.lock` |
| "Zet de tv aan" | `media_player.turn_on` |
| "Schakel ventilator om" | `fan.toggle` |
| "Activeer filmscene" | `scene.turn_on` |

### Ondersteunde domeinen

`light` · `switch` · `cover` · `media_player` · `fan` · `climate` · `lock` · `alarm_control_panel` · `scene` · `script` · `automation` · `homeassistant`

> **Let op bij Agent-modus:** Als je een Agent gebruikt met ingebouwde HA-tools, regelt de agent zelf de service-calls via de Mistral Console-configuratie. De bovenstaande "control_ha" instelling werkt dan naast de agent.

<p align="right">(<a href="#readme-top">terug naar boven</a>)</p>

---

## Gebruik als service-actie

Gebruik `conversation.process` in automations:

```yaml
action: conversation.process
data:
  agent_id: conversation.mistral_ai_conversation
  text: "Wat is de temperatuur buiten?"
response_variable: result
```

Het antwoord vind je in `result.response.speech.plain.speech`.

### Voorbeeld: Dynamische melding

```yaml
alias: Slimme deurbelmelding
sequence:
  - action: conversation.process
    data:
      agent_id: conversation.mistral_ai_conversation
      text: >
        De deurbel heeft gerinkeld om {{ now().strftime('%H:%M') }}.
        Geef een korte, vriendelijke melding van één zin.
    response_variable: ai_result
  - action: notify.mobile_app
    data:
      title: "Deurbel 🔔"
      message: "{{ ai_result.response.speech.plain.speech }}"
```

### Voorbeeld: Ochtendrapport via TTS

```yaml
alias: Ochtendrapport
sequence:
  - action: conversation.process
    data:
      agent_id: conversation.mistral_ai_conversation
      text: >
        Geef een korte samenvatting voor mijn dag.
        Buiten is het {{ states('sensor.buiten_temperatuur') }}°C.
    response_variable: rapport
  - action: tts.speak
    target:
      entity_id: tts.piper   # gebruik een andere TTS provider voor spraak
    data:
      media_player_entity_id: media_player.woonkamer
      message: "{{ rapport.response.speech.plain.speech }}"
```

<p align="right">(<a href="#readme-top">terug naar boven</a>)</p>

---

## Voorbeeldprompts

**Informatie over je huis:**
- *"Hoeveel lampen zijn er momenteel aan?"*
- *"Wat is de temperatuur in de woonkamer?"*
- *"Is de achterdeur vergrendeld?"*

**Bedienen:**
- *"Zet alle lampen in de slaapkamer uit"*
- *"Activeer de 'Film kijken' scene"*
- *"Vergrendel de voordeur"*

**Met een web search agent:**
- *"Wat is het nieuws vandaag?"*
- *"Wat is het weerbericht voor morgen in Amsterdam?"*
- *"Zoek op hoeveel het gastarief momenteel is"*

<p align="right">(<a href="#readme-top">terug naar boven</a>)</p>

---

## Veelgestelde vragen

**Q: Ik zie de integratie niet in de dropdown bij Spraakassistenten.**  
A: Zorg dat je een **volledige herstart** hebt gedaan en oude `__pycache__` mappen hebt verwijderd.

**Q: Ik krijg een 400 Bad Request.**  
A: Controleer dat temperature tussen 0.0 en 1.0 staat. Mistral accepteert geen hogere waarden.

**Q: Mijn agent reageert niet.**  
A: Controleer of het Agent ID correct is (begint met `ag_...`). Test het ID eerst in de Mistral Console.

**Q: Kan ik TTS toevoegen?**  
A: Mistral heeft geen eigen TTS API. Gebruik Piper (lokaal), Google TTS, of ElevenLabs als TTS provider in HA.

**Q: Hoe duur is Voxtral STT?**  
A: Circa $0.003 per minuut audio. Voor normaal thuisgebruik verwacht je minder dan €1 per maand.

**Q: Kan ik Agent-modus én HA-apparaten bedienen combineren?**  
A: Ja. Zet "Laat AI Home Assistant bedienen" aan én gebruik een Agent ID. De integratie probeert dan service-calls uit te voeren als de agent een JSON-actie teruggeeft.

**Q: Worden mijn gesprekken opgeslagen?**  
A: Mistral AI verwerkt verzoeken via hun servers. Zie hun [privacybeleid](https://mistral.ai/privacy-policy) voor details.

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
