from agents.extensions.memory import SQLAlchemySession
from agents import Agent, Runner, RunConfig, function_tool
from dotenv import load_dotenv
import asyncio
import os 
import sys 

load_dotenv()


session = SQLAlchemySession()