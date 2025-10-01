#!/usr/bin/env python3
"""
Audio Transcription Tool with Sequential Processing and Auto-chunking
Supports .m4a files with sequence naming (e.g., xx_1.m4a, xx_2.m4a)
"""

import os
import re
import argparse
from pathlib import Path
from typing import List, Tuple, Dict
import tempfile
import shutil
import time
from dotenv import load_dotenv
from openai import OpenAI
from pydub import AudioSegment
from pydub.utils import make_chunks
try:
    from tqdm import tqdm
except ImportError:
    # Fallback if tqdm is not available
    def tqdm(iterable, *args, **kwargs):
        return iterable

load_dotenv()

class AudioTranscriber:
    def __init__(self, api_key: str = None, test_mode: bool = False):
        self.client = OpenAI(api_key=api_key or os.getenv('OPENAI_API_KEY'))
        if not self.client.api_key:
            raise ValueError("OpenAI API key not found. Please set OPENAI_API_KEY in .env file")
        
        self.max_file_size_mb = 10  # OpenAI Whisper limit
        self.chunk_length_ms = 10 * 60 * 1000  # 10 minutes in milliseconds
        self.test_mode = test_mode
        self.test_duration_ms = 60 * 1000  # 1 minute for test mode
        
    def find_sequential_files(self, directory: str, pattern_prefix: str) -> List[Path]:
        """Find and sort sequential audio files based on naming pattern"""
        directory = Path(directory)
        files = []
        
        # Pattern to match files like xx_1.m4a, xx_2.m4a, etc.
        pattern = re.compile(rf"{re.escape(pattern_prefix)}_(\d+)\.m4a$", re.IGNORECASE)
        
        for file_path in directory.glob("*.m4a"):
            match = pattern.match(file_path.name)
            if match:
                sequence_num = int(match.group(1))
                files.append((sequence_num, file_path))
        
        # Sort by sequence number
        files.sort(key=lambda x: x[0])
        return [file_path for _, file_path in files]
    
    def get_file_size_mb(self, file_path: Path) -> float:
        """Get file size in MB"""
        return file_path.stat().st_size / (1024 * 1024)
    
    def get_chunk_count(self, file_path: Path) -> int:
        """Get the number of chunks a file will be split into"""
        if self.test_mode:
            return 1
        
        file_size_mb = self.get_file_size_mb(file_path)
        if file_size_mb <= self.max_file_size_mb:
            return 1
        
        # Load audio to calculate actual chunks needed
        audio = AudioSegment.from_file(str(file_path))
        chunks = make_chunks(audio, self.chunk_length_ms)
        return len(chunks)
    
    def chunk_audio_file(self, file_path: Path, temp_dir: Path) -> List[Path]:
        """Chunk audio file if it's too large for OpenAI API or for test mode"""
        # Load audio file first to check duration and handle test mode
        print(f"Loading audio file: {file_path.name}...")
        audio = AudioSegment.from_file(str(file_path))
        
        # Test mode: only process first 1 minute
        if self.test_mode:
            print(f"🧪 TEST MODE: Processing only first 1 minute of {file_path.name}")
            audio = audio[:self.test_duration_ms]
            test_filename = f"{file_path.stem}_test_1min.mp4"
            test_path = temp_dir / test_filename
            audio.export(str(test_path), format="mp4")
            return [test_path]
        
        file_size_mb = self.get_file_size_mb(file_path)
        
        if file_size_mb <= self.max_file_size_mb:
            return [file_path]
        
        print(f"File {file_path.name} ({file_size_mb:.1f}MB) exceeds limit. Chunking...")
        
        # Create chunks
        chunks = make_chunks(audio, self.chunk_length_ms)
        chunk_files = []
        
        print(f"Creating {len(chunks)} chunks...")
        for i, chunk in enumerate(tqdm(chunks, desc="Creating chunks")):
            chunk_filename = f"{file_path.stem}_chunk_{i+1:03d}.mp4"
            chunk_path = temp_dir / chunk_filename
            chunk.export(str(chunk_path), format="mp4")
            chunk_files.append(chunk_path)
        
        return chunk_files
    
    def transcribe_audio(self, file_path: Path, language: str = "th", current_chunk: int = None, total_chunks: int = None) -> str:
        """Transcribe a single audio file using OpenAI Whisper"""
        try:
            if current_chunk and total_chunks:
                print(f"  🎤 [{current_chunk}/{total_chunks}] Transcribing: {file_path.name}...")
            else:
                print(f"  🎤 Transcribing: {file_path.name}...")
            start_time = time.time()
            
            with open(file_path, "rb") as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language=language,
                    response_format="text"
                )
            
            elapsed_time = time.time() - start_time
            print(f"  ✅ Completed in {elapsed_time:.1f}s")
            return transcript.strip()
        except Exception as e:
            print(f"  ❌ Error transcribing {file_path.name}: {str(e)}")
            return f"[ERROR: Could not transcribe {file_path.name}]"
    
    def process_sequential_files(self, files: List[Path], language: str = "th") -> str:
        """Process sequential audio files and return combined transcript"""
        all_transcripts = []
        temp_dir = Path(tempfile.mkdtemp(prefix="audio_chunks_"))
        
        try:
            print(f"\n📁 Processing {len(files)} file(s)...")
            
            # Calculate total chunks for overall progress
            print("📊 Calculating total chunks...")
            total_chunks = sum(self.get_chunk_count(file_path) for file_path in files)
            print(f"📈 Total chunks to process: {total_chunks}")
            
            # Create overall progress bar
            overall_progress = tqdm(total=total_chunks, desc="Overall Progress", unit="chunk")
            current_chunk = 0
            
            for i, file_path in enumerate(files, 1):
                print(f"\n📄 [{i}/{len(files)}] Processing: {file_path.name}")
                
                # Chunk file if needed
                chunk_files = self.chunk_audio_file(file_path, temp_dir)
                
                file_transcripts = []
                print(f"🔄 File {i}: Transcribing {len(chunk_files)} chunk(s)...")
                
                for j, chunk_file in enumerate(chunk_files, 1):
                    current_chunk += 1
                    overall_progress.set_description(f"File {i}/{len(files)} - Chunk {j}/{len(chunk_files)} ({current_chunk}/{total_chunks})")
                    
                    transcript = self.transcribe_audio(chunk_file, language, current_chunk, total_chunks)
                    if transcript and not transcript.startswith("[ERROR"):
                        file_transcripts.append(transcript)
                    
                    overall_progress.update(1)
                
                if file_transcripts:
                    combined_transcript = " ".join(file_transcripts)
                    prefix = "🧪 TEST " if self.test_mode else ""
                    all_transcripts.append(f"=== {prefix}File {i}: {file_path.name} ===\n{combined_transcript}")
                    print(f"✅ File {i} completed successfully")
                else:
                    print(f"⚠️  No valid transcript generated for file {i}")
            
            overall_progress.close()
                
        finally:
            # Clean up temporary directory
            print(f"\n🧹 Cleaning up temporary files...")
            shutil.rmtree(temp_dir, ignore_errors=True)
        
        return "\n\n".join(all_transcripts)
    
    def generate_summary(self, transcript: str, language: str = "thai") -> str:
        """Generate summary using OpenAI GPT"""
        try:
            print(f"🤖 Generating summary in {language}...")
            start_time = time.time()
            
            test_note = "Note: This summary is based on a 1-minute test sample." if self.test_mode else ""
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": f"You are a helpful assistant that creates concise summaries. Please summarize the following transcript in {language}. Focus on key points, main topics discussed, and important conclusions. {test_note}"
                    },
                    {
                        "role": "user",
                        "content": f"Please summarize this transcript:\n\n{transcript}"
                    }
                ],
                max_tokens=1000,
                temperature=0.3
            )
            
            elapsed_time = time.time() - start_time
            print(f"✅ Summary generated in {elapsed_time:.1f}s")
            
            summary = response.choices[0].message.content.strip()
            if self.test_mode:
                summary = f"🧪 TEST MODE SUMMARY (1 minute sample)\n\n{summary}"
            
            return summary
        except Exception as e:
            print(f"❌ Error generating summary: {str(e)}")
            return "[ERROR: Could not generate summary]"
    
    def save_outputs(self, transcript: str, summary: str, output_dir: Path, prefix: str):
        """Save transcript and summary to files"""
        output_dir.mkdir(exist_ok=True)
        
        # Add test prefix if in test mode
        file_prefix = f"{prefix}_test" if self.test_mode else prefix
        
        # Save transcript
        transcript_file = output_dir / f"{file_prefix}_transcript.txt"
        with open(transcript_file, 'w', encoding='utf-8') as f:
            f.write(transcript)
        print(f"\n💾 Transcript saved to: {transcript_file}")
        
        # Save summary
        summary_file = output_dir / f"{file_prefix}_summary.txt"
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(summary)
        print(f"💾 Summary saved to: {summary_file}")

def main():
    parser = argparse.ArgumentParser(description="Transcribe sequential audio files with auto-chunking")
    parser.add_argument("directory", help="Directory containing audio files")
    parser.add_argument("prefix", help="File prefix (e.g., 'meeting' for meeting_1.m4a, meeting_2.m4a)")
    parser.add_argument("--language", "-l", default="th", help="Language code for transcription (default: th for Thai)")
    parser.add_argument("--output", "-o", default="output", help="Output directory (default: output)")
    parser.add_argument("--summary-lang", default="thai", help="Language for summary (default: thai)")
    parser.add_argument("--test", action="store_true", help="Test mode: process only first 1 minute of each audio file")
    
    args = parser.parse_args()
    
    try:
        transcriber = AudioTranscriber(test_mode=args.test)
        
        if args.test:
            print("🧪 RUNNING IN TEST MODE - Processing only first 1 minute of each file")
        
        # Find sequential files
        files = transcriber.find_sequential_files(args.directory, args.prefix)
        if not files:
            print(f"No sequential files found with prefix '{args.prefix}' in directory '{args.directory}'")
            return
        
        print(f"\n📋 Found {len(files)} sequential files:")
        for i, file_path in enumerate(files, 1):
            size_mb = transcriber.get_file_size_mb(file_path)
            test_note = " (will process 1min only)" if args.test else ""
            print(f"  {i}. {file_path.name} ({size_mb:.1f}MB){test_note}")
        
        # Process files
        transcript = transcriber.process_sequential_files(files, args.language)
        
        if not transcript:
            print("No transcript generated. Please check your audio files.")
            return
        
        # Generate summary
        print("\n📝 Generating summary...")
        summary = transcriber.generate_summary(transcript, args.summary_lang)
        
        # Save outputs
        output_dir = Path(args.output)
        transcriber.save_outputs(transcript, summary, output_dir, args.prefix)
        
        test_note = " (TEST MODE)" if args.test else ""
        print(f"\n🎉 Processing complete{test_note}! Files saved in '{output_dir}' directory.")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1

if __name__ == "__main__":
    main()