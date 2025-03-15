# YouTube Script Generator Web App

A Flask web application that provides a step-by-step wizard interface for generating YouTube video scripts using AI agents.

## Features

- Multi-step wizard interface
- Context collection for personalized content
- Web search for relevant references
- Script planning and generation
- Script editing and refinement
- Short video script generation

## Installation

1. Clone the repository
2. Navigate to the web_app directory
3. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Configuration

Create a `.env` file in the web_app directory with the following variables:

```
OPENAI_API_KEY=your_openai_api_key
FLASK_SECRET_KEY=your_secret_key
```

## Running the Application

To run the application, execute:

```bash
python app.py
```

The application will be available at http://127.0.0.1:5000/

## Wizard Steps

1. **Context**: Provide the topic and additional context for your YouTube video
2. **References**: Review and select web search results to use as references
3. **Plan**: Review and edit the content plan
4. **Script**: Review and edit the initial script
5. **Edit**: Review the edited script
6. **Short Video**: Review the short video script

## Development

This is a work in progress. Future updates will include:
- Integration with the agent system
- Ability to save and load projects
- Export options for scripts
- User authentication 