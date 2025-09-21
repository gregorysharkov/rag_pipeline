# Enhanced News Fetcher with Full Content

This enhanced version extracts **full article content** by scraping the article URLs, not just the truncated summaries from NewsAPI.

## 🆕 What's New

- ✅ **Full Article Content**: Extracts complete article text
- ✅ **Smart Extraction**: Uses newspaper3k for robust content parsing
- ✅ **Error Handling**: Graceful fallback to original content if extraction fails
- ✅ **Rate Limiting**: Respectful delays between requests
- ✅ **Enhanced Metadata**: Keywords, better author info, etc.

## 🚀 Quick Setup

1. **Install the new dependency**:
   ```bash
   pip install newspaper3k
   ```

2. **Run the enhanced fetcher**:
   ```bash
   python fetch_full_news.py
   ```

## 📊 Output Comparison

### Old Output (Truncated):
```
Content: Amazon will now let you shop for products by pointing your camera at them. On Thursday, the company announced Lens Live, a new feature that uses your camera to scan things in the environment around you, while surfacing matching product listings. This feature,… [+2495 chars]
```

### New Output (Full Content):
```
Content Extraction: ✅ Success
Keywords: Amazon, AI, shopping, camera, technology

--- FULL ARTICLE CONTENT ---
Amazon will now let you shop for products by pointing your camera at them. On Thursday, the company announced Lens Live, a new feature that uses your camera to scan things in the environment around you, while surfacing matching product listings.

The feature can identify objects as you pan your camera around a room and find potential matches on Amazon. It works by using computer vision and AI to recognize items in real-time through your phone's camera.

[COMPLETE ARTICLE TEXT CONTINUES...]
--- END ARTICLE CONTENT ---
```

## 🔧 How It Works

1. **Fetch Articles**: Gets article metadata from NewsAPI (same as before)
2. **Extract Content**: Visits each article URL and scrapes full content using newspaper3k
3. **Enhanced Data**: Combines original metadata with extracted full text
4. **Individual Files**: Saves each article as a separate file in company-specific folders
5. **Create Index**: Generates an index file for each company listing all articles

## 📁 Output Structure

The enhanced script creates a structured directory layout:

```
notebooks/documents/
├── amazon/
│   ├── _amazon_index.txt                    # Index of all Amazon articles
│   ├── Amazon_Lens_Live_AI_shops_20250914_143022.txt
│   ├── Amazon_Q3_Results_Beat_20250914_143023.txt
│   └── Amazon_Prime_Video_Update_20250914_143024.txt
├── apple/
│   ├── _apple_index.txt                     # Index of all Apple articles
│   ├── Apple_iPhone_16_Launch_20250914_143025.txt
│   └── Apple_Vision_Pro_Sales_20250914_143026.txt
└── microsoft/
    ├── _microsoft_index.txt                 # Index of all Microsoft articles
    └── Microsoft_Azure_Growth_20250914_143027.txt
```

**Benefits:**
- 🗂️ **Organized Structure**: Each company has its own folder
- 📄 **Individual Files**: Each article is a separate file for better RAG processing
- 📋 **Index Files**: Quick overview of all articles per company
- 🏷️ **Descriptive Names**: Filenames based on article titles + timestamps

## ⚙️ Configuration

You can customize the script by modifying:

```python
# Number of articles per company (reduced to 3 for faster processing)
articles_per_company=3

# Companies to fetch news for
companies = ["Apple", "Microsoft", "Google", "Amazon", "Tesla"]

# Output directory
output_dir = "notebooks/documents/"
```

## 🛡️ Error Handling

The script handles various scenarios:
- **Network timeouts**: Retry mechanism with backoff
- **Paywall articles**: Falls back to original truncated content
- **Invalid URLs**: Skips extraction, keeps original data
- **Rate limiting**: Built-in delays between requests

## 💡 Tips for Better Results

1. **Respect Rate Limits**: The script includes 1-second delays between extractions
2. **Check Success Rate**: Monitor the extraction success rate in the output
3. **Fallback Content**: Even failed extractions still save the original NewsAPI content
4. **Different Sources**: Some news sources work better than others for extraction

## 🚨 Limitations

- Some websites block automated content extraction
- Paywalled articles may not be fully accessible
- JavaScript-heavy sites might not extract properly
- Rate limiting may slow down the process

## 🔄 Migration from Old Script

If you want to keep using the old script occasionally:
- `fetch_company_news.py` - Original (fast, truncated content)
- `fetch_full_news.py` - Enhanced (slower, full content)

Both scripts can coexist and use the same configuration!
