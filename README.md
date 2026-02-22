<!-- Image: Mistral AI Conversation -->
# Mistral AI Conversation

Home Assistant integration that enables **Mistral AI** as a conversation agent, speech-to-text (STT), and support for Mistral Agents.  
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge)](https://github.com/hacs/integration)  
[![HA Version](https://img.shields.io/badge/Home%20Assistant-2023.5%2B-blue?style=for-the-badge&logo=home-assistant)](https://www.home-assistant.io/)  
[![Mistral AI](https://img.shields.io/badge/Mistral%20AI-Powered-orange?style=for-the-badge)](https://mistral.ai/)  
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)

---

## Table of Contents

1. [About This Project](#about-this-project)  
2. [Features](#features)  
3. [Requirements](#requirements)  
4. [Installation](#installation)  
5. [Configuration](#configuration)  
6. [Options & Modes](#options--modes)  
7. [Speech-to-Text (STT)](#speech-to-text-stt)  
8. [Controlling Devices](#controlling-devices)  
9. [Using as a Service Action](#using-as-a-service-action)  
10. [Example Prompts](#example-prompts)  
11. [FAQ](#faq)  
12. [License](#license)

---

## Release notes
v.1.9 Improved multi language support (2026-2-22)

---

## About This Project

This integration makes **Mistral AI** available as a full conversation agent inside Home Assistant.

You can choose between:

- **Model Mode** — Directly configure model settings, prompt template, etc.
- **Agent Mode** — Use preconfigured Agents from the Mistral Console, including custom tools and system prompts.

> Note: Mistral’s API does not provide text-to-speech (TTS). Use another TTS provider in Home Assistant.

---

## Features

| Feature | Status | Description |
|---------|:------:|------------|
| Conversation agent in HA Assist | ✅ | Selectable assistant |
| Model-based configuration | ✅ | Direct model configuration |
| Agent Mode | ✅ | Use external Agents |
| Speech-to-Text (STT) | ✅ | Voxtral support |
| Text-to-Speech (TTS) | ❌ | Not supported |
| Control HA devices | ✅ | Lights, switches, covers |
| Session memory | ✅ | Per conversation |
| Jinja2 prompt templating | ✅ | Dynamic prompts |
| Language detection | ✅ | Responds in user language |

---

## Requirements

- Home Assistant Core 2023.5+
- Mistral AI API key

---

## Installation

### Via HACS (Recommended)

1. Open HACS → Integrations → Custom repositories  
2. Add:

        https://github.com/SnarfNL/mistral_conversation

   Category: Integration  
3. Install “Mistral AI Conversation”  
4. Restart Home Assistant

### Manual Install

1. Copy:

        custom_components/mistral_conversation/

   to:

        /config/custom_components/

2. (Optional) Remove cache:

        rm -rf /config/custom_components/mistral_conversation/__pycache__

3. Restart Home Assistant fully

---

## Configuration

### Creating an API Key

1. Sign up at https://mistral.ai  
2. Go to https://console.mistral.ai/api-keys  
3. Create and copy your API key  

### Setting Up the Integration

1. Settings → Devices & Services → Add Integration  
2. Search “Mistral AI Conversation”  
3. Enter your API key  

---

## Options & Modes

### Model Mode

Default options:

- Mode: Model  
- Model: mistral-large-latest  
- Temperature: 0.7  
- Max tokens: 1024  

### Agent Mode

1. Create an agent at https://console.mistral.ai/build/agents  
2. Copy the Agent ID (ag_...)  
3. Enter it in integration options  

---

## Speech-to-Text (STT)

STT entity:

    stt.mistral_ai_stt_voxtral

To enable:
- Settings → Voice Assistants  
- Select Mistral AI STT (Voxtral)

Specs:
- Model: voxtral-mini-latest  
- Max length: 30 minutes  
- Formats: WAV, OGG  
- 16000 Hz  

---

## Controlling Devices

Enable “Allow AI to control Home Assistant” and expose entities.

Supported domains:
light, switch, cover, media_player, fan, climate, lock, scene, script, automation

---

## Using as a Service Action

Example automation:

    action:
      - service: conversation.process
        data:
          agent_id: conversation.mistral_ai_conversation
          text: "What's the outside temperature?"
          response_variable: result

---

## Example Prompts

- “How many lights are on?”
- “Turn off bedroom lights.”
- “Activate movie mode.”
- “What’s the temperature in the living room?”

---

## FAQ

Q: I don’t see the integration.  
A: Restart Home Assistant.

Q: 400 error?  
A: Check temperature value (0.0–1.0).

Q: Agent not responding?  
A: Verify Agent ID starts with ag_.

---

## License

MIT License — see LICENSE file.

Made for the Home Assistant community.
