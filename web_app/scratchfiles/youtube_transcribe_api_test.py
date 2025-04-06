from web_app.backend.agents.researcher.youtube_transcript_generator import (
    YoutubeTranscriptGenerator,
)


def main():
    # Create transcript generator
    generator = YoutubeTranscriptGenerator()
    url = "https://www.youtube.com/watch?v=WWS4GnLJkaE"
    transcript = generator.get_transcript(url)
    print(transcript)

if __name__ == "__main__":
    main()
