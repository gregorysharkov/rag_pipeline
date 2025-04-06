import re

from youtube_transcript_api import (
    NoTranscriptFound,
    YouTubeTranscriptApi,
)


class YoutubeTranscriptGenerator:
    """Class to handle YouTube transcript generation and translation."""

    def __init__(self, default_language: str = "en"):
        self.default_language = default_language

    def _extract_video_id(self, url: str) -> str:
        """
        Extract video ID from various forms of YouTube URLs.

        Args:
            url: YouTube video URL

        Returns:
            str: Video ID

        Raises:
            ValueError: If video ID cannot be extracted from the URL
        """
        print(f"Extracting video ID from URL: {url}")
        # Common YouTube URL patterns
        patterns = [
            r"(?:v=|\/)([0-9A-Za-z_-]{11}).*",  # Regular URLs
            r"(?:embed\/)([0-9A-Za-z_-]{11})",  # Embed URLs
            r"(?:youtu\.be\/)([0-9A-Za-z_-]{11})",  # Short URLs
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                video_id = match.group(1)
                return video_id

        raise ValueError(f"Could not extract video ID from URL: {url}")

    def _get_transcript(self, video_id: str):
        """Get the best available transcript and translate if necessary."""
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

        # Try to get default language transcript first
        try:
            transcript = transcript_list.find_transcript([self.default_language])
            return transcript
        # if not found, translate the first one available
        except NoTranscriptFound:
            translation = list(transcript_list._generated_transcripts.values())[0].translate(
                self.default_language
            )
            return translation

    def get_transcript(self, url: str) -> str:
        """
        Get transcript from YouTube video URL.

        Args:
            url: YouTube video URL

        Returns:
            str: Complete transcript text
        """
        # Extract video ID
        video_id = self._extract_video_id(url)

        # Get best available transcript
        transcript = self._get_transcript(video_id)

        # Fetch the transcript data
        transcript_data = transcript.fetch()

        # Combine all transcript entries into one string
        full_text = " ".join([entry.text for entry in transcript_data])
        return full_text
