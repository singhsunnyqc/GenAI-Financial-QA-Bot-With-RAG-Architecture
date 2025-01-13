# History-Aware QnA Bot Using RAG Architecture

## Overview
This project implements a history-aware Question and Answer (QnA) bot powered by Retrieval-Augmented Generation (RAG) architecture. It answers questions based on information retrieved from all URLs listed in the sitemap: [Zerodha Varsity Sitemap](https://zerodha.com/varsity/chapter-sitemap2.xml).

## Quick Start
To run this solution, you only need to execute one script: `src/app.py`.

### Prerequisites

1. **Install Dependencies**  
   Ensure you have all required dependencies installed:
   ```bash
   pip install -r requirements.txt
2. **Configure Your OpenAI API Key**  
   Add your OpenAI API key in the .env file to enable the bot's functionality.

3. **Run the Application**  
   Start the RAG application by running the following command from your terminal:
   ```bash
   streamlit run src/app.py
4. **This solution is compatible with Python version 3.13.1**


## Responsible AI Features

The bot incorporates a range of Responsible AI principles designed to enhance transparency, accuracy, and safety:

- **Explainability**: Each bot response includes a direct link to the source of information, promoting transparency and accountability.

- **Prevention of Hallucinations**: A system prompt is used to minimize the occurrence of fabricated or incorrect responses, ensuring that answers are grounded in reliable data.

- **[WIP] Guardrails**: Multiple layers of protection are in place to ensure the bot’s outputs remain feasible, relevant, and ethical:
  - **Input Guardrails**: Evaluate the feasibility and appropriateness of the user’s input.
  - **Dialog Guardrails**: Monitor the flow of conversation to ensure logical coherence and relevance.
  - **Retrieval Guardrails**: Assess the relevance and reliability of external information retrieved for answering queries.
  - **Execution Guardrails**: Ensure that any actions or computations performed by the bot are feasible and accurate.
  - **Output Guardrails**: Validate that the bot’s final responses are contextually accurate and appropriate.

 


## Video Demo



https://github.com/user-attachments/assets/bc9dc63d-d13e-4879-b8df-42f17826915e


  
