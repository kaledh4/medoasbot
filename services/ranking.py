import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def calculate_vendor_score(vendor: dict) -> float:
    """
    Calculates a strict SaaS score (0-100) for a vendor based on REAL performance metrics.
    NO MOCK DATA.
    
    Formula:
    1. Rating (30pts): (rating / 5) * 30
    2. Speed (20pts): Based on 'average_response_seconds'
    3. Win Rate (20pts): (wins / total_completed) * 20
    4. Reliability (15pts): Penalty for timeouts (Future)
    5. Freshness (15pts): Bonus for new vendors (< 10 offers)
    """
    
    score = 0.0
    
    # ---------------------------------------------------------
    # 1. RATING SCORE (Max 30)
    # ---------------------------------------------------------
    rating = float(vendor.get('rating', 5.0))
    score += (rating / 5.0) * 30
    
    # ---------------------------------------------------------
    # 2. SPEED SCORE (Max 20) — REAL DATA 🚀
    # ---------------------------------------------------------
    avg_speed = vendor.get('average_response_seconds') # In seconds
    
    if avg_speed is None:
        # NEW VENDOR BONUS: Give them full speed points to compete
        # equivalent to < 5 mins
        score += 20
    else:
        avg_speed = float(avg_speed)
        if avg_speed <= 300: # < 5 mins
            score += 20
        elif avg_speed <= 900: # < 15 mins
            score += 15
        elif avg_speed <= 1800: # < 30 mins
            score += 10
        elif avg_speed <= 3600: # < 1 hour
            score += 5
        else:
            score += 0 # Too slow
            
    # ---------------------------------------------------------
    # 3. WIN RATE SCORE (Max 20)
    # ---------------------------------------------------------
    total_offers = int(vendor.get('metrics_total_offers', 0))
    total_wins = int(vendor.get('metrics_wins', 0))
    
    if total_offers > 0:
        win_rate = total_wins / total_offers
        score += win_rate * 20
    else:
        # New vendor starts with neutral win rate assumption (50% of max points)
        score += 10 
        
    # ---------------------------------------------------------
    # 4. FRESHNESS BOOST (Max 15)
    # ---------------------------------------------------------
    # Help new vendors get their first 10 leads
    if total_offers < 10:
        score += 15
        
    # ---------------------------------------------------------
    # 5. Reliability (Max 15) - Placeholder for now (Default Full)
    # ---------------------------------------------------------
    score += 15
    
    return round(score, 2)

def rank_vendors(vendors: list, limit: int = 5) -> list:
    """
    Sorts a list of vendors by their Real-Time Score.
    Returns the top N vendors.
    """
    ranked_list = []
    
    for v in vendors:
        final_score = calculate_vendor_score(v)
        # Store score in the dict for debugging/logging
        v['_debug_score'] = final_score
        ranked_list.append(v)
        
    # Sort DESC
    ranked_list.sort(key=lambda x: x['_debug_score'], reverse=True)
    
    # Log the leaderboard
    logger.info("🏆 Vendor Leaderboard:")
    for i, v in enumerate(ranked_list[:limit]):
        logger.info(f"   #{i+1} {v.get('name')} - Score: {v['_debug_score']} (Speed: {v.get('average_response_seconds')}s)")
        
    return ranked_list[:limit]
