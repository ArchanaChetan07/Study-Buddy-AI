from setuptools import setup, find_packages

setup(
    name="study-buddy-ai",
    version="2.0.0",
    description="AI-powered adaptive quiz app built on Groq LLaMA",
    author="Study Buddy AI",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "streamlit>=1.35.0",
        "langchain>=0.2.0",
        "langchain-groq>=0.1.6",
        "pydantic>=2.0.0",
        "pandas>=2.0.0",
        "python-dotenv>=1.0.0",
        "prometheus-client>=0.20.0",
    ],
)
