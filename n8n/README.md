# n8n RAG System

A production-ready RAG (Retrieval Augmented Generation) system built with n8n - zero code required.

## Demo Video

https://github.com/user-attachments/assets/demo.mp4

> Upload `demo.mp4` to GitHub and replace the link above with the actual video URL.

## Overview

This project demonstrates how to build an intelligent chatbot that answers questions using your own data, leveraging the power of:

- **n8n** - No-code automation platform
- **OpenAI Embeddings** - Vector generation
- **Supabase Vector Store** - Vector database
- **Google Gemini** - LLM for chat responses

## Architecture

The system consists of two workflows:

### Workflow 1: Data Ingestion Pipeline

![Data Ingestion](n8n%20data%20ingestion.png)

```
Google Sheets → Edit Fields → OpenAI Embeddings → Supabase Vector Store
```

| Node | Function |
|------|----------|
| When clicking 'Execute workflow' | Manual trigger |
| Get row(s) in sheet | Reads data from Google Sheets |
| Edit Fields | Transforms and processes data |
| Embeddings OpenAI | Generates vector embeddings |
| Default Data Loader | Loads documents |
| Supabase Vector Store | Stores vectors for retrieval |

**Result:** 60 documents ingested with one click.

### Workflow 2: RAG Chat Agent

![RAG Agent](RAG.png)

```
Chat Trigger → AI Agent → Response
                  ↓
         Google Gemini (LLM)
         Simple Memory (Context)
         Supabase Vector Store (Retrieval)
         OpenAI Embeddings (Query)
```

| Node | Function |
|------|----------|
| When chat message received | Chat trigger |
| AI Agent | Orchestrates the RAG pipeline |
| Google Gemini Chat Model | LLM for generating responses |
| Simple Memory | Maintains conversation context |
| Supabase Vector Store | Retrieves relevant documents |
| Embeddings OpenAI | Converts queries to vectors |

## Tech Stack

| Technology | Purpose |
|------------|---------|
| n8n | Workflow automation |
| Google Sheets | Data source |
| OpenAI | Embeddings generation |
| Supabase | Vector database |
| Google Gemini | Chat model |

## Benefits

- **No Code Required** - Drag, drop, connect
- **Production Ready** - Scalable architecture
- **Fast Setup** - Build in minutes, not weeks
- **Cost Effective** - Pay only for API usage
- **Flexible** - Easy to modify and extend

## Getting Started

1. Set up n8n (cloud or self-hosted)
2. Configure API credentials:
   - OpenAI API Key
   - Supabase credentials
   - Google Gemini API Key
   - Google Sheets access
3. Import the workflows
4. Run data ingestion first
5. Start chatting with your RAG agent

## Use Cases

- Customer support chatbots
- Internal knowledge base Q&A
- Document search and retrieval
- FAQ automation
- Research assistants

## Acknowledgments

Thanks **Ed Donner** for the great course!

## License

MIT
