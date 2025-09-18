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

# Helper functions
def prepare_for_mongo(data):
    """Convert datetime objects to ISO strings for MongoDB storage"""
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
    return data

def parse_from_mongo(item):
    """Convert ISO strings back to datetime objects"""
    if isinstance(item, dict):
        for key, value in item.items():
            if isinstance(value, str) and key in ['entry_time', 'exit_time', 'created_at', 'updated_at']:
                try:
                    item[key] = datetime.fromisoformat(value.replace('Z', '+00:00'))
                except:
                    pass
    return item

def calculate_pnl(trade_data):
    """Calculate P&L for a trade"""
    if not trade_data.get('exit_price'):
        return None
    
    entry_price = trade_data['entry_price']
    exit_price = trade_data['exit_price']
    quantity = trade_data['quantity']
    direction = trade_data['direction']
    
    if direction == TradeDirection.LONG:
        profit_loss = (exit_price - entry_price) * quantity
    else:  # SHORT
        profit_loss = (entry_price - exit_price) * quantity
    
    # For futures, typically each point is worth different amounts
    # NQ (Nasdaq) = $20 per point, ES (S&P) = $50 per point
    symbol = trade_data['symbol'].upper()
    if symbol == 'NQ':
        profit_loss *= 20  # $20 per point for Nasdaq futures
    elif symbol == 'ES':
        profit_loss *= 50  # $50 per point for S&P futures
    
    commission = trade_data.get('commission', 0) or 0
    net_pnl = profit_loss - commission
    
    return {
        'profit_loss': round(profit_loss, 2),
        'net_pnl': round(net_pnl, 2)
    }
# API Routes
@api_router.get("/")
async def root():
    return {"message": "Trade Journal API"}

@api_router.post("/trades", response_model=TradeJournal)
async def create_trade(trade: TradeJournalCreate):
    trade_dict = trade.dict()
    trade_obj = TradeJournal(**trade_dict)
    
    # Prepare for MongoDB storage
    trade_data = prepare_for_mongo(trade_obj.dict())
    
    await db.trades.insert_one(trade_data)
    return trade_obj

@api_router.get("/trades", response_model=List[TradeJournal])
async def get_trades(limit: int = 100, status: Optional[TradeStatus] = None):
    query = {}
    if status:
        query['status'] = status
    
    trades = await db.trades.find(query).sort("created_at", -1).limit(limit).to_list(limit)
    return [TradeJournal(**parse_from_mongo(trade)) for trade in trades]

@api_router.get("/trades/{trade_id}", response_model=TradeJournal)
async def get_trade(trade_id: str):
    trade = await db.trades.find_one({"id": trade_id})
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    return TradeJournal(**parse_from_mongo(trade))
