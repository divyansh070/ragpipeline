try:
    import langchain
    import langchain_core
    import langchain_community
    import langchain_anthropic
    import langchain_openai
    import langchain_google_genai
    print("✅ All LangChain packages imported successfully!")
except ImportError as e:
    print(f"❌ Import failed: {e}")
except Exception as e:
    print(f"❌ Unexpected error: {e}")
