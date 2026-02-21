"""Speech-to-Text platform for Mistral AI using Voxtral."""
from __future__ import annotations

import io
import logging
import wave
from typing import AsyncIterable

import aiohttp
from homeassistant.components.stt import (
    AudioBitRates,
    AudioChannels,
    AudioCodecs,
    AudioFormats,
    AudioSampleRates,
    SpeechMetadata,
    SpeechResult,
    SpeechResultState,
    SpeechToTextEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_STT_LANGUAGE,
    DEFAULT_STT_LANGUAGE,
    DOMAIN,
    MISTRAL_API_BASE,
    STT_MODEL,
)

_LOGGER = logging.getLogger(__name__)

# Map from BCP-47 code → display name used in the config dropdown
LANGUAGE_OPTIONS: list[tuple[str, str]] = [
    ("",   "Auto-detect"),
    ("af", "Afrikaans"),
    ("ar", "Arabic"),
    ("az", "Azerbaijani"),
    ("be", "Belarusian"),
    ("bg", "Bulgarian"),
    ("bs", "Bosnian"),
    ("ca", "Catalan"),
    ("cs", "Czech"),
    ("cy", "Welsh"),
    ("da", "Danish"),
    ("de", "German"),
    ("el", "Greek"),
    ("en", "English"),
    ("es", "Spanish"),
    ("et", "Estonian"),
    ("fa", "Persian"),
    ("fi", "Finnish"),
    ("fr", "French"),
    ("gl", "Galician"),
    ("he", "Hebrew"),
    ("hi", "Hindi"),
    ("hr", "Croatian"),
    ("hu", "Hungarian"),
    ("hy", "Armenian"),
    ("id", "Indonesian"),
    ("is", "Icelandic"),
    ("it", "Italian"),
    ("ja", "Japanese"),
    ("kk", "Kazakh"),
    ("kn", "Kannada"),
    ("ko", "Korean"),
    ("lt", "Lithuanian"),
    ("lv", "Latvian"),
    ("mk", "Macedonian"),
    ("ml", "Malayalam"),
    ("mr", "Marathi"),
    ("ms", "Malay"),
    ("mt", "Maltese"),
    ("my", "Burmese"),
    ("nb", "Norwegian Bokmål"),
    ("ne", "Nepali"),
    ("nl", "Dutch"),
    ("pl", "Polish"),
    ("pt", "Portuguese"),
    ("ro", "Romanian"),
    ("ru", "Russian"),
    ("sk", "Slovak"),
    ("sl", "Slovenian"),
    ("sr", "Serbian"),
    ("sv", "Swedish"),
    ("sw", "Swahili"),
    ("ta", "Tamil"),
    ("th", "Thai"),
    ("tl", "Filipino"),
    ("tr", "Turkish"),
    ("uk", "Ukrainian"),
    ("ur", "Urdu"),
    ("vi", "Vietnamese"),
    ("zh", "Chinese"),
]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up STT entity."""
    async_add_entities([MistralSTTEntity(hass, config_entry)])


class MistralSTTEntity(SpeechToTextEntity):
    """Mistral AI / Voxtral speech-to-text entity — separate device from conversation."""

    _attr_has_entity_name = True
    _attr_name = "Mistral AI STT (Voxtral)"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self._entry = entry
        # _stt suffix → separate device from the conversation entity
        self._attr_unique_id = f"{entry.entry_id}_stt"

    @property
    def device_info(self) -> DeviceInfo:
        """Own device for STT, separate from conversation."""
        return DeviceInfo(
            # Different identifiers from conversation entity → creates SEPARATE device
            identifiers={(DOMAIN, f"{self._entry.entry_id}_stt")},
            name="Mistral AI STT",
            manufacturer="Mistral AI",
            model=STT_MODEL,
            entry_type=DeviceEntryType.SERVICE,
            configuration_url="https://docs.mistral.ai/capabilities/audio_transcription",
        )

    @property
    def supported_languages(self) -> list[str]:
        return [code for code, _ in LANGUAGE_OPTIONS if code]

    @property
    def supported_formats(self) -> list[AudioFormats]:
        return [AudioFormats.WAV]

    @property
    def supported_codecs(self) -> list[AudioCodecs]:
        return [AudioCodecs.PCM]

    @property
    def supported_bit_rates(self) -> list[AudioBitRates]:
        return [AudioBitRates.BITRATE_16]

    @property
    def supported_sample_rates(self) -> list[AudioSampleRates]:
        return [AudioSampleRates.SAMPLERATE_16000]

    @property
    def supported_channels(self) -> list[AudioChannels]:
        return [AudioChannels.CHANNEL_MONO]

    async def async_process_audio_stream(
        self,
        metadata: SpeechMetadata,
        stream: AsyncIterable[bytes],
    ) -> SpeechResult:
        """Collect raw PCM, wrap in WAV, transcribe via Voxtral."""
        pcm_data = b""
        async for chunk in stream:
            pcm_data += chunk

        if not pcm_data:
            _LOGGER.warning("STT: received empty audio stream")
            return SpeechResult("", SpeechResultState.ERROR)

        _LOGGER.debug("STT: %d bytes PCM rate=%s ch=%s bits=%s",
                      len(pcm_data), metadata.sample_rate,
                      metadata.channel, metadata.bit_rate)

        # HA always delivers raw PCM — always wrap in a WAV container
        wav_bytes = _pcm_to_wav(
            pcm_data,
            sample_rate=int(metadata.sample_rate),
            channels=int(metadata.channel),
            sample_width=int(metadata.bit_rate) // 8,
        )

        api_key = self._entry.data[CONF_API_KEY]
        lang_code = (self._entry.options.get(CONF_STT_LANGUAGE, DEFAULT_STT_LANGUAGE) or "").strip()

        session = async_get_clientsession(self.hass)
        try:
            form = aiohttp.FormData()
            form.add_field(
                "file", wav_bytes,
                filename="audio.wav",
                content_type="application/octet-stream",
            )
            form.add_field("model", STT_MODEL)
            if lang_code:
                form.add_field("language", lang_code)

            async with session.post(
                f"{MISTRAL_API_BASE}/audio/transcriptions",
                headers={"Authorization": f"Bearer {api_key}"},
                data=form,
                timeout=aiohttp.ClientTimeout(total=60),
            ) as resp:
                if resp.status != 200:
                    body = await resp.text()
                    _LOGGER.error("Mistral STT HTTP %s: %s", resp.status, body)
                    return SpeechResult("", SpeechResultState.ERROR)
                result = await resp.json()

        except aiohttp.ClientError as err:
            _LOGGER.error("Mistral STT API error: %s", err)
            return SpeechResult("", SpeechResultState.ERROR)

        text = result.get("text", "").strip()
        if not text:
            _LOGGER.warning("Voxtral returned empty transcription")
            return SpeechResult("", SpeechResultState.ERROR)

        _LOGGER.debug("Voxtral result: %s", text)
        return SpeechResult(text, SpeechResultState.SUCCESS)


def _pcm_to_wav(pcm_data: bytes, sample_rate: int, channels: int, sample_width: int) -> bytes:
    """Wrap raw PCM in a RIFF/WAV container."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_data)
    return buf.getvalue()
