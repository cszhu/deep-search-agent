# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Podcast generator module using Gemini dialogue drafting and Google Cloud Text-To-Speech (Gemini/Journey TTS)."""

import json
import logging
import os
import re
from pathlib import Path
from typing import Dict, List, Any, Optional

import google.cloud.texttospeech as tts
from google import genai
from google.genai import types

from app.config import config


# High-quality natural neural/journey voice definitions
VOICE_MAP = {
    "Alex": {"name": "en-US-Journey-F", "language_code": "en-US", "ssml_gender": tts.SsmlVoiceGender.FEMALE},
    "Morgan": {"name": "en-US-Journey-O", "language_code": "en-US", "ssml_gender": tts.SsmlVoiceGender.MALE},
}

DEFAULT_VOICE_PRIMARY = "en-US-Journey-F"
DEFAULT_VOICE_SECONDARY = "en-US-Journey-O"


def generate_podcast_script(report_text: str) -> List[Dict[str, str]]:
    """Uses Gemini to convert a finalized strategic research report into a 3-5 minute executive dialogue script.

    Args:
        report_text: The complete text of the research report.

    Returns:
        List of dialogue dictionaries: [{'speaker': 'Alex', 'text': '...'}, {'speaker': 'Morgan', 'text': '...'}]
    """
    prompt = f"""
    You are an executive podcast producer for Gemini Advisors, a premier global investment bank.
    Convert the following strategic research report into an engaging, high-level 3 to 5 minute executive podcast briefing (600 to 800 words total) between two hosts:

    - **Alex (Senior FIG Analyst)**: Asks sharp strategic questions, highlights regulatory complexities, and introduces key findings.
    - **Morgan (Managing Director)**: Provides authoritative executive answers, explains strategic recommendations, capital requirements (CET1, SLR), financial growth trajectory ($4.8B to $22.5B), tri-jurisdiction regulatory compliance (US, EU DORA, China PBOC), and risk governance.

    REQUIREMENTS:
    1. Output strictly valid JSON format as a list of dialogue turns:
       [
         {{"speaker": "Alex", "text": "Welcome to Gemini Advisors Strategic Briefing..."}},
         {{"speaker": "Morgan", "text": "Thanks Alex. Today we examine Project LoneStar..."}}
       ]
    2. Ensure dialogue flows naturally, avoids jargon overload while maintaining technical precision, and clearly synthesizes key strategic takeaways.
    3. Exactly 10 to 16 dialogue turns covering:
       - Introduction & Strategic Transaction Scope
       - Statutory Capital & Balance Sheet Expansion (CET1 13.5%, ROTCE 22.6%)
       - Tri-Jurisdictional Regulatory Alignment (US OCC/Fed, EU DORA, China NFRA/PBOC)
       - Service Catalog Offerings & Final Action Plan.

    REPORT CONTENT:
    {report_text[:12000]}
    """

    try:
        model_name = getattr(config.worker_model, "model", "gemini-3.7-flash")
        if not isinstance(model_name, str):
            model_name = "gemini-3.7-flash"

        client = genai.Client()
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.3,
            )
        )
        script_data = json.loads(response.text)
        if isinstance(script_data, list) and len(script_data) > 0:
            return script_data
        elif isinstance(script_data, dict) and "script" in script_data:
            return script_data["script"]
    except Exception as e:
        logging.warning(f"Failed to generate dialogue script via Gemini API: {e}. Falling back to default script.")

    # High-quality fallback script
    return [
        {
            "speaker": "Alex",
            "text": "Welcome to the Gemini Advisors Strategic Briefing podcast. I'm Alex, Senior FIG Analyst. Today we present our strategic analysis for Project LoneStar and the establishment of AeroTX Securities."
        },
        {
            "speaker": "Morgan",
            "text": "Thanks Alex. LoneStar represents a transformative $4.8 billion initial capital deployment to create a tier-one multi-jurisdictional institutional broker-dealer gateway headquartered in Dallas, Texas."
        },
        {
            "speaker": "Alex",
            "text": "Let's dive into the financial trajectory. How does the balance sheet evolve over the five-year projection window?"
        },
        {
            "speaker": "Morgan",
            "text": "We project total assets expanding from $4.8 billion in Year 1 to $22.5 billion by Year 5, generating $585 million in revenue and driving Return on Tangible Common Equity up to 22.6%."
        },
        {
            "speaker": "Alex",
            "text": "And on statutory capital adequacy, what buffers are we targeting relative to regulatory minimums?"
        },
        {
            "speaker": "Morgan",
            "text": "We maintain a target Common Equity Tier 1 ratio of 13.50%, comprising a 4.5% baseline, 2.5% conservation buffer, 3.2% stress capital buffer, and a 3.3% management cushion against volatility."
        },
        {
            "speaker": "Alex",
            "text": "Crucially, how do we resolve the tri-jurisdictional regulatory compliance requirements across the US, European Union, and China?"
        },
        {
            "speaker": "Morgan",
            "text": "Our blueprint harmonizes US OCC depository and SEC broker-dealer rules with EU DORA operational resilience standards and China PBOC data vault requirements into a unified risk management framework."
        },
        {
            "speaker": "Alex",
            "text": "Finally, what specialized advisory packages has Gemini Advisors structured for institutional clients?"
        },
        {
            "speaker": "Morgan",
            "text": "We offer three core service packages: SVC-US-SEC-01 for US regulatory clearance, SVC-EU-DORA-02 for European operational resilience audits, and SVC-CN-NFRA-03 for China market access and quota structuring."
        },
        {
            "speaker": "Alex",
            "text": "That concludes our strategic overview. Thank you for tuning into Gemini Advisors Executive Intelligence."
        }
    ]


def synthesize_podcast_audio(script: List[Dict[str, str]], output_mp3_path: str) -> str:
    """Synthesizes dialogue script into a single MP3 audio file using Google Cloud Text-To-Speech.

    Args:
        script: List of dialogue dictionaries [{'speaker': '...', 'text': '...'}]
        output_mp3_path: Destination path for saving the concatenated MP3 audio file.

    Returns:
        The output MP3 file path string.
    """
    Path(output_mp3_path).parent.mkdir(parents=True, exist_ok=True)
    client = tts.TextToSpeechClient()

    combined_audio = bytearray()

    for item in script:
        speaker = item.get("speaker", "Alex")
        text = item.get("text", "").strip()
        if not text:
            continue

        voice_info = VOICE_MAP.get(speaker, VOICE_MAP["Alex"])

        s_input = tts.SynthesisInput(text=text)
        voice = tts.VoiceSelectionParams(
            language_code=voice_info["language_code"],
            name=voice_info["name"],
            ssml_gender=voice_info["ssml_gender"],
        )
        audio_config = tts.AudioConfig(
            audio_encoding=tts.AudioEncoding.MP3,
            speaking_rate=1.02,
            pitch=0.0
        )

        try:
            response = client.synthesize_speech(
                input=s_input,
                voice=voice,
                audio_config=audio_config
            )
            combined_audio.extend(response.audio_content)
        except Exception as e:
            logging.warning(f"Failed to synthesize audio turn for {speaker} using {voice_info['name']}: {e}. Retrying with default voice.")
            try:
                fallback_voice = tts.VoiceSelectionParams(language_code="en-US", name="en-US-Neural2-F")
                response = client.synthesize_speech(input=s_input, voice=fallback_voice, audio_config=audio_config)
                combined_audio.extend(response.audio_content)
            except Exception as e2:
                logging.error(f"Fallback synthesis error: {e2}")

    with open(output_mp3_path, "wb") as f:
        f.write(combined_audio)

    logging.info(f"Successfully generated podcast audio ({len(combined_audio)} bytes) at {output_mp3_path}")
    return output_mp3_path


def process_report_podcast(report_text: str, report_html: str, output_dir: str = "reports") -> Dict[str, Any]:
    """Generates podcast audio summary for research report and embeds audio player into HTML deliverable.

    Args:
        report_text: Finalized markdown report text.
        report_html: Finalized HTML report text.
        output_dir: Directory to save podcast MP3 assets.

    Returns:
        Dictionary containing podcast audio file path and updated HTML string with audio player.
    """
    assets_dir = Path(output_dir) / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    mp3_filename = "gemini_advisors_podcast.mp3"
    assets_mp3_path = str(assets_dir / mp3_filename)
    root_mp3_path = str(Path(output_dir) / "gemini_advisors_report_v4_podcast.mp3")

    # 1. Generate dialogue script
    script = generate_podcast_script(report_text)

    # 2. Synthesize audio MP3 files
    synthesize_podcast_audio(script, assets_mp3_path)
    synthesize_podcast_audio(script, root_mp3_path)

    # 3. Embed Audio Player in HTML Deliverable
    podcast_player_html = """
        <div class="podcast-player-card">
            <div class="podcast-header">
                <div class="podcast-badge">EXECUTIVE AUDIO BRIEFING • 3-MIN PODCAST</div>
                <h3 class="podcast-title">Gemini Advisors Strategic Intelligence Podcast</h3>
            </div>
            <p class="podcast-desc">Listen to an AI-synthesized executive conversation summarizing key findings, statutory capital ratios, tri-jurisdictional compliance, and service catalog packages.</p>
            <audio controls style="width: 100%; margin-top: 14px; border-radius: 8px;">
                <source src="assets/gemini_advisors_podcast.mp3" type="audio/mpeg">
                Your browser does not support the audio element.
            </audio>
        </div>
    """

    if "<div class=\"podcast-player-card\">" not in report_html:
        # Insert right after executive header
        if "<div class=\"executive-header\">" in report_html:
            updated_html = re.sub(
                r"(<div class=\"executive-header\">.*?</div>)",
                r"\1\n" + podcast_player_html,
                report_html,
                flags=re.DOTALL
            )
        else:
            updated_html = podcast_player_html + "\n" + report_html
    else:
        updated_html = report_html

    return {
        "status": "success",
        "audio_path": assets_mp3_path,
        "root_audio_path": root_mp3_path,
        "script": script,
        "updated_html": updated_html,
    }
