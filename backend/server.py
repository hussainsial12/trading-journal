from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, timezone
from enum import Enum
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


# Enums for trade data
class TradeDirection(str, Enum):
    LONG = "long"
    SHORT = "short"

class TradeStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"

class EmotionRating(str, Enum):
    VERY_CONFIDENT = "very_confident"
    CONFIDENT = "confident"
    NEUTRAL = "neutral"
    ANXIOUS = "anxious"
    VERY_ANXIOUS = "very_anxious"

class MarketCondition(str, Enum):
    TRENDING = "trending"
    SIDEWAYS = "sideways"
    VOLATILE = "volatile"
    CALM = "calm"