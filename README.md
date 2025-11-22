# Agentified WebShop Benchmark

This repository contains the "Agentified" version of the WebShop benchmark, designed to be compatible with the [A2A Protocol](https://a2a-protocol.org/) and ready for the AgentBeats platform.

It consists of:
- **Green Agent (Assessor):** Evaluates the performance of other agents on WebShop tasks.
- **White Agent (Baseline):** A baseline agent using Google Gemini (`gemini-1.5-pro`) to perform shopping tasks.
- **Launcher:** A script to orchestrate the assessment locally.

## Prerequisites

- **Conda** (Miniconda or Anaconda)
- **Python 3.10** (Required for compatibility with Gym 0.26 and WebShop dependencies)
- **Java 11+** (Required for Pyserini if using full search features)

## Installation

### 1. Set up the Environment
Create a Conda environment to manage dependencies. This is crucial to avoid version conflicts (especially with `gym` and `numpy`).

```bash
conda create -n webshop python=3.10
conda activate webshop
```

### 2. Install WebShop Benchmark
The core benchmark code resides in `webshop-benchmark/`. Install it in editable mode so the agents can import `web_agent_site`:

```bash
cd webshop-benchmark
pip install -e .
```

*Note: You must ensure the WebShop data (product data, search indices) is downloaded and placed correctly as per the original WebShop instructions. Typically this involves running their `setup.sh` or downloading the tarballs to `webshop-benchmark/data`.*

### 3. Install Agent Dependencies
Navigate to the `agentify-webshop` directory and install the specific requirements for the agents:

```bash
cd ../agentify-webshop
pip install -r requirements.txt
```

This command installs:
- `a2a-sdk` (Agent-to-Agent Protocol SDK)
- `google-generativeai` (Gemini API)
- `gym==0.26.2` (Compatible Gym version)
- `spacy`, `flask`, `selenium`, etc.

### 4. Download Spacy Model
The Green Agent uses Spacy for text analysis.

```bash
python -m spacy download en_core_web_sm
```

## Configuration

### 1. Google Gemini API Key
The White Agent uses Google Gemini.

1.  Go to [Google AI Studio](https://aistudio.google.com/) and generate an API Key.
2.  Create a `.env` file in `agentify-webshop/` to store it securely:

```bash
cd agentify-webshop
# Create .env file
echo "GEMINI_API_KEY=your_actual_api_key_here" > .env
```

3.  **Security Note:** The `.env` file is added to `.gitignore` to prevent accidental commit of your secrets.

## Usage

### Run Local Assessment (The Easy Way)
To run a full end-to-end assessment locally, use the launcher script. It starts both agents, performs the handshake, and executes the task.

```bash
conda activate webshop
cd agentify-webshop
python -m src.launcher
```

**Expected Output:**
- The Green Agent starts on port 9001.
- The White Agent starts on port 9002.
- The launcher waits for readiness.
- An assessment task is sent.
- The White Agent interacts with the simulated WebShop.
- Final results (Success/Fail + Metrics) are printed.

### Manual / Debugging Mode
You can run the agents individually to inspect logs or debug specific components.

**Terminal 1: Green Agent**
```bash
cd agentify-webshop
python -m src.green_agent.agent
```
*Verifies that the Assessor is running and serving the Agent Card at `localhost:9001`.*

**Terminal 2: White Agent**
```bash
cd agentify-webshop
python -m src.white_agent.agent
```
*Verifies that the Baseline Agent is running and serving its Agent Card at `localhost:9002`.*

**Terminal 3: Launcher (Custom)**
You can modify `src/launcher.py` to connect to these existing instances or simply use `curl`/`a2a-client` to send requests manually.

