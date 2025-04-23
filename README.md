# AI-Powered Essay Writing Assistant with LangGraph

An advanced AI system that automates essay writing through research, drafting, and iterative refinement using LangChain and LangGraph.

## Features

🔄 **Multi-stage Workflow**:
- **Planning**: Generates detailed essay outlines
- **Research**: Performs web searches for relevant information
- **Drafting**: Creates initial essay versions
- **Critique**: Provides detailed improvement suggestions
- **Revision**: Implements feedback through multiple iterations

🔎 **Smart Research Integration**:
- Automatic query generation for targeted research
- Content aggregation from multiple sources
- Information filtering and summarization

✍️ **AI Writing Pipeline**:
- GPT-3.5-turbo powered content generation
- Customizable writing style and structure
- Revision tracking with version control

## Technical Architecture
A[Plan Outline] --> B[Research Phase]
B --> C[Generate Draft]
C --> D{Critique Check}
D -->|Needs Revision| E[Research Updates]
E --> C
D -->|Approved| F[Final Output]


## Key Components

- **State Management**: Typed dictionary for tracking essay progress
- **Tool Integration**: Tavily Search API for web research
- **Checkpointing**: SQLite-based memory for process persistence
- **Structured Outputs**: Pydantic models for query generation

## Usage
input_data = {
'task': "Your essay question here",
"max_revision": 3, # Max revision cycles
"revision_num": 1, # Starting revision
"content": [], # Research container
"plan": "", # Generated outline
"draft": "", # Essay content
"critique": "", # Improvement suggestions
}

for step in graph.stream(input_data):
print(step["current_state"]) # Track progress


## Configuration

1. Add your OpenAI API key in `OPENAI_API_KEY`
2. Set Tavily API key in `tavily_api_key`
3. Configure max revisions as needed

## Use Cases

- Academic writing assistance
- Content creation automation
- Research paper drafting
- Educational AI applications

## Contribution

Open to PRs for:
- Additional research tools
- Enhanced critique mechanisms
- UI/API integrations
- Performance optimizations
