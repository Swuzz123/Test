import os
from openai import OpenAI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from memori import Memori

load_dotenv()

class MemoryManager:
    """
    Manages the Memori + OpenAI integration.
    """
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        
        # Try to get full connection string, or construct it from components
        self.db_url = os.getenv("DATABASE_CONNECTION_STRING")
        if not self.db_url:
            user = os.getenv("POSTGRES_USER", "postgres")
            password = os.getenv("POSTGRES_PASSWORD", "postgres")
            host = os.getenv("POSTGRES_HOST", "localhost")
            port = os.getenv("POSTGRES_PORT", "5432")
            dbname = os.getenv("POSTGRES_DB", "memori_db")
            # Construct SQLAlchemy connection string
            self.db_url = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}"
        
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set.")

        print(f"Connecting to Database: {self.db_url}")

        # 1. Setup OpenAI Client
        self.client = OpenAI(api_key=self.api_key)

        # 2. Setup Database Connection
        try:
            self.engine = create_engine(self.db_url)
            self.Session = sessionmaker(bind=self.engine)
        except Exception as e:
            raise ConnectionError(f"Failed to create database engine: {e}")

        # 3. Initialize Memori & Register Client
        # memori.llm.register(client) modifies the client in-place or returns a wrapper.
        # We pass the session_maker (or session) to conn.
        
        # Ensure MEMORI_API_KEY is available in os.environ for Memori to pick it up
        memori_api_key = os.getenv("MEMORI_API_KEY")
        if not memori_api_key:
             print("Warning: MEMORI_API_KEY not found in environment.")
        
        try:
            self.memori = Memori(conn=self.Session).llm.register(self.client)
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Memori: {e}")
        
        # 4. Initialize Storage Schema
        if hasattr(self.memori, 'config') and hasattr(self.memori.config, 'storage'):
            self.memori.config.storage.build()

    def set_context(self, user_id: str, process_id: str):
        """
        Set the current context (attribution) for the session.
        """
        self.memori.attribution(entity_id=user_id, process_id=process_id)

    def get_client(self):
        """
        Returns the OpenAI client (which is now integrated with Memori).
        """
        return self.client

    def wait_for_augmentation(self):
        """
        Wait for async memory augmentation to complete.
        """
        if hasattr(self.memori, 'augmentation'):
            self.memori.augmentation.wait()

    def set_session(self, session_id: str):
        """
        Set the session ID for the current context.
        """
        if hasattr(self.memori, 'set_session'):
            self.memori.set_session(session_id)
        else:
            print(f"Warning: Memori instance does not have set_session method. Session {session_id} not set.")

    def reset_session(self, session_id: str):
        """
        Hard reset: Re-initialize the Memori instance with a new session.
        This ensures no state leakage from previous sessions.
        """
        print(f"resetting session to: {session_id}")
        
        # 1. Re-create OpenAI Client (CRITICAL: Memori patches the client, so we need a fresh one)
        self.client = OpenAI(api_key=self.api_key)

        # 2. Re-register Client (creates new Memori instance)
        try:
            # We create a new instance to clear internal state
            self.memori = Memori(conn=self.Session).llm.register(self.client)
        except Exception as e:
            raise RuntimeError(f"Failed to re-initialize Memori during reset: {e}")
            
        # 3. Set the new session
        self.set_session(session_id)
        
        # 4. Re-build Storage Schema if needed
        if hasattr(self.memori, 'config') and hasattr(self.memori.config, 'storage'):
            self.memori.config.storage.build()