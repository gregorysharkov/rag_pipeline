# Company News Fetcher

This script fetches the latest 5 news articles for each of 5 specified companies and saves each company's news into separate files within the `documents` folder.

## Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Get NewsAPI Key**:
   - Visit [NewsAPI.org](https://newsapi.org/register) to get a free API key
   - The free tier allows 1000 requests per day

3. **Configure Environment**:
   - Open the `.env` file in the project root
   - Replace `your_newsapi_key_here` with your actual NewsAPI key:
   ```
   NEWS_API_KEY=your_actual_api_key_here
   ```

## Usage

Run the script from the project root:

```bash
python fetch_company_news.py
```

## What it does

- Fetches 5 news articles for each of these companies:
  - Apple
  - Microsoft
  - Google
  - Amazon
  - Tesla

- Saves each company's news to separate files in the `documents/` folder:
  - `apple_news.txt`
  - `microsoft_news.txt`
  - `google_news.txt`
  - `amazon_news.txt`
  - `tesla_news.txt`

## Output Format

Each file contains:
- Header with company name and generation timestamp
- For each article:
  - Title
  - Source
  - Author
  - Publication date
  - URL
  - Description
  - Content preview (truncated if long)

## Customization

You can modify the script to:
- Change the list of companies in the `companies` list
- Adjust the number of articles per company by changing `articles_per_company`
- Modify the output directory by changing the `output_dir` parameter

## Error Handling

The script includes error handling for:
- Missing or invalid API key
- Network connectivity issues
- API rate limiting
- File writing permissions

## Requirements

- Python 3.6+
- Internet connection
- Valid NewsAPI key
