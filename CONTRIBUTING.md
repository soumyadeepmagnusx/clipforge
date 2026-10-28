# Contributing to ClipForge

Thank you for your interest in improving **ClipForge**! We welcome contributions of all kinds: bug reports, feature proposals, documentation improvements, and pull requests.

---

## 🛠️ Development Setup

1. **Fork and Clone the Repository**
   ```bash
   git clone https://github.com/soumyadeepmagnusx/clipforge.git
   cd clipforge
   ```

2. **Create a Virtual Environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Verify Tests**
   ```bash
   python tests/test_pipeline.py
   ```

---

## 📐 Code Style & Conventions

- We follow **PEP 8** standards.
- Write descriptive commit messages using [Conventional Commits](https://www.conventionalcommits.org/):
  - `feat: add feature X`
  - `fix: resolve bug Y`
  - `docs: update documentation`
  - `test: add unit tests for module Z`

---

## 📬 Submitting a Pull Request

1. Create a feature branch: `git checkout -b feat/my-new-feature`
2. Commit your changes: `git commit -m "feat: implement X"`
3. Push to your branch: `git push origin feat/my-new-feature`
4. Open a Pull Request on GitHub with a clear summary of your changes.
