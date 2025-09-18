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
# Trade Models
class TradeJournal(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Basic Trade Info
    symbol: str  # NQ (Nasdaq) or ES (S&P)
    direction: TradeDirection
    entry_price: float
    exit_price: Optional[float] = None
    quantity: int
    entry_time: datetime
    exit_time: Optional[datetime] = None
    
    # Financial Metrics
    profit_loss: Optional[float] = None
    commission: Optional[float] = None
    net_pnl: Optional[float] = None
    
    # Strategy & Risk Management
    strategy: str
    stop_loss: Optional[float] = None
    target_price: Optional[float] = None
    risk_reward_ratio: Optional[float] = None
    
    # Psychology & Context
    pre_trade_emotion: EmotionRating
    post_trade_emotion: Optional[EmotionRating] = None
    market_condition: MarketCondition
    
    # Trade Analysis
    setup_description: str
    what_worked: Optional[str] = None
    what_could_improve: Optional[str] = None
    lessons_learned: Optional[str] = None
    
    # Additional Data
    chart_screenshot_url: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    notes: Optional[str] = None
    
    # Status
    status: TradeStatus = TradeStatus.OPEN
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
class TradeJournalCreate(BaseModel):
    symbol: str
    direction: TradeDirection
    entry_price: float
    quantity: int
    entry_time: datetime
    strategy: str
    pre_trade_emotion: EmotionRating
    market_condition: MarketCondition
    setup_description: str
    stop_loss: Optional[float] = None
    target_price: Optional[float] = None
    chart_screenshot_url: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    notes: Optional[str] = None

class TradeJournalUpdate(BaseModel):
    exit_price: Optional[float] = None
    exit_time: Optional[datetime] = None
    post_trade_emotion: Optional[EmotionRating] = None
    what_worked: Optional[str] = None
    what_could_improve: Optional[str] = None
    lessons_learned: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[TradeStatus] = None

class TradeStats(BaseModel):
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_pnl: float
    average_win: float
    average_loss: float
    largest_win: float
    largest_loss: float


