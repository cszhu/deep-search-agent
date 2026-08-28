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

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

from app.podcast_generator import (
    generate_podcast_script,
    synthesize_podcast_audio,
    process_report_podcast,
)


@patch("google.genai.Client")
def test_generate_podcast_script_fallback(mock_genai_client):
    """Tests that generate_podcast_script returns a valid dialogue list even when Gemini API is mocked or fails."""
    mock_instance = MagicMock()
    mock_genai_client.return_value = mock_instance
    mock_instance.models.generate_content.side_effect = Exception("Mock network error")

    sample_report = "# Strategic Report\nLoneStar balance sheet expanding to $22.5B."
    script = generate_podcast_script(sample_report)
    assert isinstance(script, list)
    assert len(script) >= 5
    assert "speaker" in script[0]
    assert "text" in script[0]


@patch("google.cloud.texttospeech.TextToSpeechClient")
def test_synthesize_podcast_audio(mock_tts_client, tmp_path):
    """Tests synthesis of audio turns into an MP3 file."""
    mock_instance = MagicMock()
    mock_tts_client.return_value = mock_instance
    mock_response = MagicMock()
    mock_response.audio_content = b"ID3_MOCK_AUDIO_DATA_BYTES"
    mock_instance.synthesize_speech.return_value = mock_response

    script = [
        {"speaker": "Alex", "text": "Welcome to the podcast."},
        {"speaker": "Morgan", "text": "Thanks Alex, excited to present our analysis."}
    ]

    out_file = str(tmp_path / "test_out.mp3")
    res_path = synthesize_podcast_audio(script, out_file)

    assert res_path == out_file
    assert os.path.exists(out_file)
    assert mock_instance.synthesize_speech.call_count == 2


@patch("google.genai.Client")
@patch("google.cloud.texttospeech.TextToSpeechClient")
def test_process_report_podcast(mock_tts_client, mock_genai_client, tmp_path):
    """Tests processing of report text into podcast assets and HTML player embedding."""
    mock_genai_instance = MagicMock()
    mock_genai_client.return_value = mock_genai_instance
    mock_genai_instance.models.generate_content.side_effect = Exception("Mock network error")

    mock_instance = MagicMock()
    mock_tts_client.return_value = mock_instance
    mock_response = MagicMock()
    mock_response.audio_content = b"MOCK_MP3_CONTENT"
    mock_instance.synthesize_speech.return_value = mock_response

    sample_md = "# Title\nReport details."
    sample_html = "<html><body><div class=\"executive-header\">Header</div>Body</body></html>"

    res = process_report_podcast(sample_md, sample_html, output_dir=str(tmp_path))
    assert res["status"] == "success"
    assert "<div class=\"podcast-player-card\">" in res["updated_html"]
    assert "assets/gemini_advisors_podcast.mp3" in res["updated_html"]
