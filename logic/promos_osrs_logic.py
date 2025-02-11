import os
import json
from datetime import datetime

# Path to the OSRS member list JSON file
OSRS_MEMBERLIST_PATH = "/root/ghosted-bot/data/members/oldschoolrunescape/osrs_memberlist.json"

def run_promotions():
    try:
        with open(OSRS_MEMBERLIST_PATH, "r") as f:
            members_data = json.load(f)
    except FileNotFoundError:
        raise ValueError("OSRS member list JSON file not found")

    ignored_ranks = {"diamond", "onyx", "administrator", "gnome elder", "mentor", "prefect", "supervisor", "leader", "superior",
                     "executive", "coordinator", "moderator", "deputy owner", "owner"}

    rank_requirements = {
        "thief": {"next_rank": "recruit", "min_time": 14, "min_xp": 50000},
        "recruit": {"next_rank": "corporal", "min_time": 44, "min_xp": 100000},
        "corporal": {"next_rank": "sergeant", "min_time": 94, "min_xp": 500000},
        "sergeant": {"next_rank": "lieutenant", "min_time": 154, "min_xp": 1000000},
        "lieutenant": {"next_rank": "captain", "min_time": 214, "min_xp": 2000000},
        "captain": {"next_rank": "general", "min_time": 274, "min_xp": 3000000},
        "general": {"next_rank": "officer", "min_time": 334, "min_xp": 5000000},
        "officer": {"next_rank": "commander", "min_time": 394, "min_xp": 15000000},
        "commander": {"next_rank": "colonel", "min_time": 454, "min_xp": 25000000},
        "colonel": {"next_rank": "brigadier", "min_time": 494, "min_xp": 50000000},
        "brigadier": {"next_rank": "admiral", "min_time": 524, "min_xp": 100000000},
        "admiral": {"next_rank": "marshal", "min_time": 547, "min_xp": 200000000}
    }

    promotions = []

    def get_rank_priority(rank):
        priority_order = [
            "thief", "recruit", "corporal", "sergeant", "lieutenant",
            "captain", "general", "officer", "commander", "colonel",
            "admiral", "brigadier", "marshal"
        ]
        return priority_order.index(rank.lower()) if rank.lower() in priority_order else -1

    for member_name, data in members_data.items():
        role = data.get("Clan Rank", "thief").lower()
        join_date_str = data.get("Join Date", "Unknown")
        experience = data.get("Total XP", 0)

        if role in ignored_ranks or join_date_str == "Unknown":
            continue

        try:
            join_date = datetime.strptime(join_date_str, "%m/%d/%Y")
            days_in_clan = (datetime.now() - join_date).days
        except ValueError:
            continue

        new_role = role
        for rank, requirements in rank_requirements.items():
            if days_in_clan >= requirements["min_time"] and experience >= requirements["min_xp"]:
                if get_rank_priority(requirements["next_rank"]) > get_rank_priority(role):
                    new_role = requirements["next_rank"]

        if new_role.lower() != role and get_rank_priority(new_role) > get_rank_priority(role):
            promotions.append([member_name, join_date_str, role, new_role])

    promotions.sort(key=lambda x: x[0].lower())

    if promotions:
        promotion_summary = '\n'.join([f"{i+1}. {p[0]} has been promoted from {p[2]} to **{p[3]}**!" for i, p in enumerate(promotions)])
    else:
        promotion_summary = None

    debug_details = '\n'.join([f"{p[0]}: {p[2]} -> {p[3]}" for p in promotions])

    return promotion_summary, debug_details