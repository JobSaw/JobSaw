---
trigger: always_on
---

# General Coding Rules & Project Standards

## 1. Security and Version Control
* **Data Protection:** Sensitive information (API keys, credentials, `.env` files) must never be committed. 
* **Git Hygiene:** Use `.gitignore` strictly to prevent sensitive data and build artifacts ("junk") from entering the repository.

## 2. Documentation and Metadata
* **README.md:** Must reflect the current state of the application. If features or installation steps change, the README must be updated in the same commit.
* **Dependencies:** `requirements.txt` must be updated immediately whenever a new package is introduced or a version is changed.

## 3. Architecture and Quality
* **Design Patterns:** Code must be written following established design patterns (e.g., Factory, Singleton, Observer) where appropriate.
* **Principles:** Adhere to SOLID principles and DRY (Don't Repeat Yourself).
* **Efficiency:** Optimize for token usage in API calls. Balance this by using specialized agents for distinct tasks rather than one monolithic agent.

## 4. Commenting and Style
* **Clarity:** Comment all files, functions, and classes using simple, direct language.
* **Tone:** Keep descriptions technical and concise. 
* **Restrictions:** Do not use emojis in code comments or documentation.

## 5. Code interpretation/compilation
* **python** Do not execute the code, give me the commands and I will execute it in a separate terminal and feed-back the output