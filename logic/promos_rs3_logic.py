import json
from datetime import datetime

# Path to the RS3 member list JSON file
RS3_MEMBERLIST_PATH = "/root/ghosted-bot/data/members/runescape3/rs3_memberlist.json"

def calculate_days_in_clan(join_date):
    try:
        join_date_obj = datetime.strptime(join_date, "%m/%d/%Y")
        return (datetime.now() - join_date_obj).days
    except ValueError:
        return None  # Return None if the date format is incorrect

def determine_promotion(current_rank, days_in_clan):
    rank_hierarchy = {'Recruit': 1, 'Corporal': 2, 'Sergeant': 3, 'Lieutenant': 4, 'Captain': 5}
    new_rank = None

    if days_in_clan is None:
        return None

    if days_in_clan <= 30:
        new_rank = 'Recruit'
    elif 31 <= days_in_clan <= 90:
        new_rank = 'Corporal'
    elif 91 <= days_in_clan <= 180:
        new_rank = 'Sergeant'
    elif 181 <= days_in_clan <= 365:
        new_rank = 'Lieutenant'
    elif days_in_clan > 365:
        new_rank = 'Captain'

    # Check if the new rank is a promotion
    if new_rank and rank_hierarchy.get(new_rank, 0) > rank_hierarchy.get(current_rank, 0):
        return new_rank
    return None  # No change or demotion avoided

def run_promotions():
    try:
        with open(RS3_MEMBERLIST_PATH, "r") as f:
            members_data = json.load(f)
    except FileNotFoundError:
        raise ValueError("RS3 member list JSON file not found")

    promotions = []
    ignored_ranks = ['Captain', 'General', 'Overseer', 'Admin', 'Deputy Owner', 'Owner']  # Ignored Ranks

    for member_name, data in members_data.items():
        current_rank = data.get("Clan Rank", "Recruit")
        join_date = data.get("Join Date", "Unknown")

        # Skip ranks that are to be ignored
        if current_rank in ignored_ranks:
            continue

        if join_date != "Unknown":
            days_in_clan = calculate_days_in_clan(join_date)
            new_rank = determine_promotion(current_rank, days_in_clan)

            if new_rank:
                promotions.append([member_name, join_date, current_rank, new_rank])

    if promotions:
        promotion_summary = '\n'.join([f"{i+1}. {p[0]} has been promoted from {p[2]} to **{p[3]}**!" for i, p in enumerate(promotions)])
    else:
        promotion_summary = None

    debug_details = '\n'.join([f"{p[0]}: {p[2]} -> {p[3]}" for p in promotions])

    return promotion_summary, debug_details