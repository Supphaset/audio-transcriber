# Audio Transcriber with Sequential Processing

A Python tool for transcribing sequential audio files (.m4a) using OpenAI's Whisper API with automatic chunking for large files and GPT-powered summarization.

## Features

- 🎵 **Sequential Processing**: Automatically detects and processes files in sequence (e.g., `meeting_1.m4a`, `meeting_2.m4a`)
- ✂️ **Auto-chunking**: Automatically splits large audio files that exceed OpenAI's 25MB limit
- 🌏 **Thai Language Support**: Optimized for Thai transcription (configurable for other languages)
- 📝 **Dual Output**: Generates both full transcript and AI-powered summary
- 🔧 **Easy Configuration**: Simple .env file setup for OpenAI API key

## Installation

1. **Clone or download this project**

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up your OpenAI API key**:
   ```bash
   cp .env.example .env
   # Edit .env and add your OpenAI API key
   ```

## Usage

### Basic Usage

```bash
python audio_transcriber.py <directory> <prefix>
```

**Example**: If you have files `meeting_1.m4a`, `meeting_2.m4a`, `meeting_3.m4a` in a folder called `audio/`:

```bash
python audio_transcriber.py audio/ meeting
```

### Advanced Options

```bash
python audio_transcriber.py <directory> <prefix> [options]

Options:
  --language, -l     Language code for transcription (default: th for Thai)
  --output, -o       Output directory (default: output)
  --summary-lang     Language for summary (default: thai)
```

### Examples

**Thai transcription (default)**:
```bash
python audio_transcriber.py ./recordings interview
```

**English transcription**:
```bash
python audio_transcriber.py ./recordings lecture --language en --summary-lang english
```

**Custom output directory**:
```bash
python audio_transcriber.py ./audio meeting --output ./results
```

## File Naming Convention

Your audio files must follow this naming pattern:
- `<prefix>_<number>.m4a`
- Examples: `meeting_1.m4a`, `meeting_2.m4a`, `interview_1.m4a`, `lecture_01.m4a`

The tool will automatically:
1. Find all files matching the pattern
2. Sort them by sequence number
3. Process them in order

## Output

The tool creates two files in the output directory:
- `<prefix>_transcript.txt` - Full transcript of all audio files
- `<prefix>_summary.txt` - AI-generated summary

## Large File Handling

Files larger than 25MB are automatically chunked into smaller segments:
- Each chunk is processed separately
- Transcripts are seamlessly combined
- Temporary chunk files are automatically cleaned up

## Requirements

- Python 3.7+
- OpenAI API key
- Audio files in .m4a format
- Internet connection for API calls

## Cost Considerations

- **Whisper API**: ~$0.006 per minute of audio
- **GPT-4o-mini**: ~$0.00015 per 1K tokens for summaries
- Example: 1 hour of audio ≈ $0.36 + summary cost

## Troubleshooting

### Common Issues

**"OpenAI API key not found"**
- Ensure your `.env` file contains `OPENAI_API_KEY=your_key_here`
- Make sure the `.env` file is in the same directory as the script

**"No sequential files found"**
- Check your file naming matches the pattern: `prefix_number.m4a`
- Ensure files are in the specified directory
- Case-sensitive matching

**"File too large" errors**
- The tool automatically handles large files, but very large files (>100MB) may take longer
- Consider splitting extremely large files manually if needed

### Debug Mode

Add print statements or use verbose logging by modifying the script if needed.

## License

MIT License - feel free to modify and distribute.