# Contribute a language or voice

Help translate commentary, record natural narration or review language and chess terminology. A short sample is enough to start; you do not need a finished ZIP or an Anki test.

## Get started in three steps

1. **Choose a language and a role.** Tell us whether you want to translate, narrate or review. If you would like help choosing a task or finding collaborators, [start a Discussion](https://github.com/Chess-for-Anki/chess-for-anki/discussions). This is optional.
2. **Share a small sample.** [Open a language contribution issue](https://github.com/Chess-for-Anki/chess-for-anki/issues/new?template=language_pack.yml) with your language, a short translation or recording link, and the license and credits. For a review, identify the phrase and suggest a correction. Use clear chess terminology; record narration at a natural base `1x` pace so users can choose their playback speed.
3. **Refine it together.** The maintainer will review the wording, pronunciation and rights with you before publishing a pack. Agree on the phrase list before recording a full narrator. You may share test results if you have them; untested samples are welcome. Submissions are never downloaded, installed or executed automatically.

For audio or full packs, share a stable download link, preferably an asset in your own GitHub release. Paste short text samples directly into the issue. Do not attach ZIP files or programs to the issue.

## Language availability

| Locale | Language | Current natural narration status |
| --- | --- | --- |
| `en-US` | English | English Michael is available as an optional download. Reviews and corrections are welcome. |
| `pt-BR` | Portuguese (Brazil) | Planned; translators, narrators and reviewers welcome. |
| `ru-RU` | Russian | Planned; translators, narrators and reviewers welcome. |
| `zh-CN` | Chinese (Simplified, China) | Planned; translators, narrators and reviewers welcome. |
| `es-ES` | Spanish (Spain) | Planned; translators, narrators and reviewers welcome. |
| `hi-IN` | Hindi (India) | Priority for community contributions; planned, with runtime language support still needed. |
| `fr-FR` | French (France) | Planned; translators, narrators and reviewers welcome. |
| `de-DE` | German | Planned; translators, narrators and reviewers welcome. |
| `ja-JP` | Japanese | Planned; translators, narrators and reviewers welcome. |

Only English natural narration is currently available. Basic system speech for the other listed locales except Hindi requires a suitable voice installed on the user's device; it is separate from community recordings. Hindi is a priority, but it is not yet offered in the runtime's language selector.

Commentary text and the narrator can be selected separately. Natural voice packs are optional downloads; missing recordings can fall back to system speech when an appropriate device voice is available.

## Rights and public sharing

Submit original translations and your own voice, or material you have permission to redistribute under a stated license. Include the requested credits. Recorded speakers must consent to recording and public distribution. Disclose any voice-generation service and confirm that its terms permit redistribution; do not imitate someone without permission.

Issues and Discussions are public. Do not share paid pack content, downloaded reference books, copied explanations without permission, credentials, Anki profiles, review history or private recordings. State that speaker consent exists without posting private consent documents or contact details.

<details>
<summary>Technical pack format and import limits</summary>

## Prepare a pack

These details are for packaging an agreed contribution. You can offer help or submit a sample before preparing a pack.

Keep canonical English phrase keys unchanged. For example, `"Illegal move."` identifies the same phrase in every language; translate its value in `narration.translations` and record that translated phrase. Ask the maintainer for the current phrase list before planning full coverage. One sample clip does not make a complete narrator.

Translate commentary text while preserving each line's `start_fen`, complete `moves` sequence and each note's `san`. The starting position and full move sequence identify the matching line. Do not replace SAN notation with translated piece initials. State the coverage of partial translations; matching English starter commentary can supply fallback lines. Keep recordings clear and free of music, background speech and clipped words, and match the spoken explanation to its visible text.

A pack is a ZIP with a UTF-8 `pack.json` at its root and, when recordings are included, MP3 files directly inside `audio/`. It contains declarative text and media only. Do not include scripts, executables, installers, an Anki profile or another archive.

```text
sample-language-pack.zip
  pack.json
  audio/
    _cfa_voice_0123456789abcdef.mp3
```

This is minimal schema 2 metadata for a single Portuguese narration clip. It demonstrates the format, not a complete language pack. The sample filename must correspond to a real recording in the ZIP.

```json
{
  "schema": 2,
  "id": "voice-pt-br-sample",
  "language": "pt-BR",
  "name": "Portuguese (Brazil) narration sample",
  "version": "0.1.0",
  "lines": [],
  "narration": {
    "language": "pt-BR",
    "clips": {
      "Illegal move.": "_cfa_voice_0123456789abcdef.mp3"
    },
    "translations": {
      "Illegal move.": "Lance ilegal."
    }
  }
}
```

Replace the illustrative hash with a digest for your recording and update every reference to that filename. Use a SHA-256 digest derived from the locale, speaker and spoken text, with at least 16 lowercase hexadecimal characters. A changed recording must have a new filename when its bytes differ from an installed recording.

### Metadata and audio rules

- `schema` is the integer `2` for a new pack with optional narration. Existing schema 1 commentary packs remain supported.
- `id` is 1 to 64 characters and matches `[a-z0-9][a-z0-9-]{0,63}`. Choose a stable, unique lowercase ID.
- `language` and `narration.language` use locale strings matching `[a-z]{2,3}(?:-[A-Za-z0-9]{2,8})*`, such as `pt-BR`. A well-formed locale does not by itself mean that the runtime supports it.
- `name` is a display name of 1 to 120 characters. Include a `version` string so reviewers can identify revisions.
- `lines` is an array of up to 1,000 commentary lines. It can be empty for a voice-only schema 2 pack. A pack must contain commentary or narration.
- Each commentary line has a `start_fen` string of up to 200 characters, a `moves` array of 1 to 600 SAN strings, and the same number of `notes`. Each move string has 1 to 20 characters. Use `""` for the normal starting position. Do not duplicate the same starting position and move sequence.
- Each note has `san` equal to the corresponding move and plain `text` of 1 to 2,500 characters after trimming. Optional `audio` names an MP3 with that same explanation spoken aloud.
- `narration.clips` maps 1 to 2,000 canonical English phrase keys to MP3 filenames. Keys contain 1 to 3,000 characters. Optional `narration.translations` maps up to 2,000 phrase keys to translated plain text; each key and value has 1 to 3,000 characters.
- New narrator filenames follow `_cfa_voice_[a-f0-9]{16,64}.mp3`; commentary filenames use `_cfa_expl_[a-f0-9]{16,64}.mp3`. For example, `_cfa_voice_0123456789abcdef.mp3` has the required shape. These are filenames in JSON, without an `audio/` prefix. Existing English Michael filenames remain supported for compatibility.
- Every referenced MP3 must be included under `audio/`, and every included MP3 must be referenced by the metadata. Use actual MP3 audio, not a renamed file of another type. Do not include duplicate paths, nested media folders, absolute paths or `..` path components.

Current importer limits are **8 MiB per file**, **256 MiB expanded per ZIP**, and **3,000 archive entries**, including metadata and any directory entry. These are import limits, not a promise that a hosting service accepts the same upload size. Split a large contribution into agreed smaller packs if needed.

For a full pack, include its version, coverage, filenames, sizes and a SHA-256 checksum for the ZIP in the issue. Update the version and checksum when the archive changes. If you have tested it, add the Anki and add-on versions and what you checked. Testing is optional for submissions.

Format checks do not establish translation quality, recording rights, complete phrase coverage or compatibility with every Anki installation. The maintainer reviews contributions before publication; only reviewed releases should be described as available.

</details>
