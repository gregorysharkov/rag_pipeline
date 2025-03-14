# RAG Pipeline - YouTube Shorts Script Generator

A Kedro project that uses OpenAI's API to generate scripts for YouTube shorts, with a future capability to collect and use data from a vector database for enhanced script generation.

## Project Structure

This project follows the Kedro project structure:

```
├── conf/                   # Configuration files
│   ├── base/               # Base configurations
│   │   ├── catalog.yml     # Data catalog definitions
│   │   └── parameters.yml  # Parameters for the pipelines
│   └── local/              # Local configurations (not in version control)
├── data/                   # Data storage
├── docs/                   # Documentation
├── notebooks/              # Jupyter notebooks
├── src/                    # Source code
│   └── rag_pipeline/       # Python package
│       ├── pipelines/      # Pipeline definitions
│       │   ├── collect_data/       # Pipeline for collecting data (placeholder)
│       │   └── generate_script/    # Pipeline for generating YouTube shorts scripts
│       └── pipeline_registry.py    # Pipeline registry
└── tests/                  # Test files
```

## Pipelines

1. **collect_data**: A placeholder pipeline for collecting data and storing it in a vector database.
2. **generate_script**: A pipeline for generating YouTube shorts scripts using OpenAI's API.

## Setup

1. Make sure you have Python 3.7+ installed
2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the root directory with your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

## Usage

### Running the Script Generator Pipeline

```bash
kedro run --pipeline=generate_script
```

### Changing the Topic

You can change the topic for the YouTube short by modifying the `topic` parameter in `conf/base/parameters.yml`.

### Visualizing the Pipeline

```bash
kedro viz
```

## Customization

You can customize the script generation by:

1. Modifying the parameters in `conf/base/parameters.yml`
2. Editing the prompt in `src/rag_pipeline/pipelines/generate_script/nodes.py`
3. Changing the OpenAI model or parameters in the same file

## Future Development

The `collect_data` pipeline is currently a placeholder. In the future, it will be implemented to:

1. Collect data from various sources
2. Process and clean the data
3. Embed the data using OpenAI's embeddings API
4. Store the embeddings in a vector database
5. Use the vector database for RAG (Retrieval-Augmented Generation) to enhance script generation