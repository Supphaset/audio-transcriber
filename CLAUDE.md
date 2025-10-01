# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based audio transcription tool that uses OpenAI's Whisper API to transcribe sequential audio files (.m4a) with automatic chunking for large files and GPT-powered summarization. The tool is optimized for Thai language transcription but supports other languages.

## Core Commands

### Running the transcriber
```bash
python audio_transcriber.py <directory> <prefix>
```

### Examples
```bash
# Basic usage with Thai transcription (default)
python audio_transcriber.py audio/ meeting

# English transcription with custom output
python audio_transcriber.py ./recordings lecture --language en --summary-lang english --output ./results

# Test mode - process only first 1 minute of each file
python audio_transcriber.py audio/ meeting --test --language en --summary-lang english
```

### Installing dependencies
```bash
pip install -r requirements.txt
```

### Environment setup
```bash
cp .env.example .env
# Edit .env to add OPENAI_API_KEY
```

## Architecture

### Main Component: AudioTranscriber Class
- **Location**: `audio_transcriber.py:21`
- **Core functionality**: Handles file discovery, chunking, transcription, and summarization

### Key Methods:
- `find_sequential_files()`: Discovers and sorts audio files by sequence number using regex pattern `prefix_\d+\.m4a`
- `chunk_audio_file()`: Automatically splits files larger than 25MB into 10-minute chunks using pydub
- `transcribe_audio()`: Calls OpenAI Whisper API for transcription
- `generate_summary()`: Uses GPT-4o-mini to create summaries
- `process_sequential_files()`: Orchestrates the entire transcription workflow

### File Processing Flow:
1. Pattern matching for sequential files (`prefix_1.m4a`, `prefix_2.m4a`, etc.)
2. Automatic chunking for files >25MB (OpenAI API limit)
3. Sequential transcription with temporary file cleanup
4. Combined transcript generation with file markers
5. AI-powered summarization
6. Output to `prefix_transcript.txt` and `prefix_summary.txt`

### Dependencies:
- **OpenAI**: Whisper transcription and GPT summarization
- **pydub**: Audio file manipulation and chunking
- **python-dotenv**: Environment variable management
- **tqdm**: Progress bars for better user experience

### Configuration:
- API key stored in `.env` file
- Default language: Thai (`th`)
- Max file size: 25MB (Whisper API limit)
- Chunk length: 10 minutes
- Default output directory: `output/`
- Test mode: processes only first 1 minute of each file for quick testing

### New Features:
- **Progress tracking**: Visual progress bars using tqdm during transcription
- **Test mode**: `--test` flag processes only first 1 minute of audio for quick validation
- **Enhanced output**: Emoji indicators and detailed status messages
- **Improved error handling**: Better error messages with visual indicators

### File Structure Requirements:
- Audio files must follow naming pattern: `<prefix>_<number>.m4a`
- Files are automatically sorted by sequence number
- Supports .m4a format only