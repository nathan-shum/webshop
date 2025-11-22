# ✅ WebShop on Apple Silicon (ARM64) – Verified Setup Guide

These instructions capture the exact sequence that brought the original WebShop benchmark up on an M-series Mac without Docker. Follow every step in order for a reproducible install.

---
## 1. Prerequisites
1. **Homebrew** (for `libomp`, `jq`, etc.).
2. **Miniconda/Anaconda** (Python 3.8.13 via conda works best).
3. **Git** to clone the repo.
4. ~15 GB free disk (models + indexes).

---
## 2. Create & Prepare the Conda Environment
```bash
# From anywhere
conda create -n webshop python=3.8.13
conda activate webshop

# Optional but recommended
conda config --env --set channel_priority flexible
```

### Install system-level deps via conda
```bash
conda install -c pytorch faiss-cpu=1.7.4
conda install -c conda-forge openjdk=11 jq=1.7
```

### Upgrade pip toolchain inside the env
```bash
pip install --upgrade pip setuptools wheel
```

---
## 3. Clone the Repository
```bash
cd ~/Desktop  # anywhere you like
git clone https://github.com/princeton-nlp/webshop.git
cd webshop
```

---
## 4. Python Dependencies (ARM-safe versions)
Install the critical pinned packages **before** running the general requirements to avoid build failures:
```bash
pip install "PyYAML==6.0.1" "charset_normalizer==3.3.2" gdown
pip install cleantext==1.1.4 rank-bm25==0.2.2
pip install "pyserini==0.17.0" --extra-index-url https://download.pytorch.org/whl/
pip install torch==2.2.2 --extra-index-url https://download.pytorch.org/whl/cpu
```

Now install the repo requirements (friendly to ARM after the pins above):
```bash
pip install -r requirements.txt
```
> If pip still retries to build incompatible wheels, rerun with `pip install --no-deps` for the already pinned packages, then re-run `pip install -r requirements.txt`.

### Extra packages pulled in implicitly
The commands above also install:
- `Cython`, `nmslib`, `lightgbm`, `onnxruntime`, `sentencepiece`, etc. (via `pyserini`).
- `networkx`, `fsspec` (via `torch`).

---
## 5. Download Required Data
```bash
mkdir -p data && cd data
pip install gdown  # safe to rerun

gdown 1EgHdxQ_YxqIQlvvq5iKlCrkEKR6-j0Ib  # items_shuffle_1000.json (~5 MB)
gdown 1IduG0xl544V_A_jv3tHXC0kyFi7PnyBu  # items_ins_v2_1000.json (~150 KB)
gdown 14Kb5SPBk_jfdLZ_CDBNitW98QLDlKR5O  # items_human_ins.json (~5 MB)
cd ..
```

---
## 6. spaCy Model (large English)
With the dependency fixes above, the spaCy download works:
```bash
python -m spacy download en_core_web_lg
```

---
## 7. Build the Search Resources & Indexes
This is the step that previously failed because of missing `cleantext`, `rank_bm25`, `pyserini`, `torch`. After installing the pinned versions, run:
```bash
cd search_engine
python convert_product_file_format.py
./run_indexing.sh
cd ..
```
You should see logs like:
```
resources_1k/documents.jsonl: 1000 docs added.
Indexing Complete! 1,000 documents indexed
```
This creates:
```
search_engine/resources*/documents.jsonl
search_engine/indexes*/ (Lucene indexes)
```

---
## 8. Full Environment Smoke Test
```bash
python - <<'PY'
import gym
from web_agent_site import envs  # registers

env = gym.make('WebAgentTextEnv-v0', observation_mode='text', num_products=1000)
obs = env.reset()
print("Instruction:", env.instruction_text)
obs, reward, done, info = env.step("search[desk]")
print("Step reward:", reward, "done:", done)
PY
```
If this prints an instruction plus a reward, the native text environment is ready.

---
## 9. Run the Original Setup Script (Optional)
After the manual fixes above you can re-run:
```bash
./setup.sh -d small
```
It should now succeed end-to-end (downloads, indexing, sample trajectories).

---
## 10. Common Pitfalls & Fixes
| Symptom | Root Cause | Fix |
| --- | --- | --- |
| `AttributeError: cython_sources` while installing PyYAML | Pip tries to build incompatible 6.0 wheel | Install `PyYAML==6.0.1` first |
| `pyenv: gdown: command not found` | `gdown` only in global Python | Install `gdown` inside the conda env |
| `ModuleNotFoundError: cleantext` or `pyserini` | Requirements aborted early | Install pins in Section 4 |
| `ModuleNotFoundError: torch` (while running converter) | `pyserini` imports torch on ARM | Install `torch==2.2.2` CPU wheel |
| `Indexing Complete! 0 documents indexed` | `resources*/documents.jsonl` missing | Rerun converter after deps are installed |

---
## 11. What’s Next?
- Launch your agents directly (green/white) from this conda env—no Docker necessary.
- If you still prefer Docker for isolation, the `Dockerfile` in the root remains compatible with this data layout.

Happy benchmarking on Apple Silicon! 💻🍏