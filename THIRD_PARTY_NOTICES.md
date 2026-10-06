# Deferred voice research notice

MoneroAI release candidate 5 does not install or run Piper. Microsoft Zira is
the temporary primary voice and all production setup, preload, and response
paths bypass Piper with zero wait.

The source tree retains an experimental downloader and service for a possible
future voice upgrade. If that work is reactivated, the relevant components are:

- **Piper 1.7 (`piper-tts`)** — GPL-3.0-or-later. Source and license:
  <https://github.com/OHF-Voice/piper1-gpl>
- **Piper `en_US-ljspeech-high` model** — model repository is MIT; its model
  card identifies the LJSpeech source dataset as public domain:
  <https://huggingface.co/rhasspy/piper-voices>

Neither Piper nor its model is bundled in this release. Review all applicable
licenses before reactivation or commercial distribution.
