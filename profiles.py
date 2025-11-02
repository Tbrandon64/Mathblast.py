import json
import os
import datetime
import random
import uuid
import logging

# Simple avatars copy (kept local to avoid circular imports)
AVATARS = ["👨", "👩", "🐱", "🐶", "🐼", "🐰", "🦊", "🐸", "🦁", "🐯", "🦄", "🐲"]

_post_save_callback = None

def set_post_save_callback(cb):
    global _post_save_callback
    _post_save_callback = cb

def load_profiles(filename='math_blast_profiles.json'):
    try:
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                data = json.load(f)
                # Defensive: ensure file contains a dict mapping names -> profile data
                if isinstance(data, dict):
                    return data
                else:
                    logging.warning(f"Profiles file {filename} does not contain a dict; resetting.")
                    # overwrite with empty dict to avoid KeyError elsewhere
                    with open(filename, 'w') as fw:
                        json.dump({}, fw)
                    return {}
    except Exception as e:
        logging.error(f"Error loading profiles from {filename}: {e}")
        # Malformed JSON - attempt to overwrite with an empty dict to recover
        try:
            with open(filename, 'w') as fw:
                json.dump({}, fw)
        except Exception:
            pass
        return {}
    return {}

def check_achievements(profile):
    achievements = profile.get('achievements', [])
    stats = profile.get('stats', {})
    try:
        if 'beginner' not in achievements and stats.get('games_played', 0) > 0:
            achievements.append('beginner')
        if 'perfect_10' not in achievements and stats.get('max_streak', 0) >= 10:
            achievements.append('perfect_10')
        if 'level_master' not in achievements and profile.get('highest_level', 0) >= 5:
            achievements.append('level_master')
        if 'math_wizard' not in achievements and profile.get('total_correct', 0) >= 100:
            achievements.append('math_wizard')
    except Exception:
        pass
    return achievements

def save_profile(name, highest_level, total_correct, game_result=None, game_stats=None, xp_gain=0, filename='math_blast_profiles.json'):
    profiles = load_profiles(filename)
    if name in profiles:
        profile = profiles[name]
        profile['highest_level'] = max(highest_level, profile.get('highest_level', 1))
        profile['total_correct'] = total_correct + profile.get('total_correct', 0)
        profile['games_played'] = profile.get('games_played', 0) + (1 if game_result else 0)
        profile['last_modified'] = int(datetime.datetime.now().timestamp())

        if game_result:
            profile['games_won'] = profile.get('games_won', 0) + (1 if game_result == 'win' else 0)
            profile['games_lost'] = profile.get('games_lost', 0) + (1 if game_result == 'lose' else 0)

        if game_stats:
            stats = profile.get('stats', {})
            stats['max_streak'] = max(stats.get('max_streak', 0), game_stats.get('streak', 0))
            stats['perfect_levels'] = stats.get('perfect_levels', 0) + (1 if game_stats.get('no_mistakes', False) else 0)
            stats['fastest_level'] = min(stats.get('fastest_level', float('inf')), game_stats.get('level_time', float('inf')))
            stats['total_time'] = stats.get('total_time', 0) + game_stats.get('total_time', 0)
            profile['stats'] = stats

        profile['achievements'] = check_achievements(profile)
    else:
        profiles[name] = {
            'highest_level': highest_level,
            'total_correct': total_correct,
            'games_played': 0,
            'games_won': 0,
            'games_lost': 0,
            'avatar': random.choice(AVATARS),
            'xp': 0,
            'account_level': 1
        }

    # Apply xp gain and update account level
    try:
        if xp_gain and name in profiles:
            p = profiles[name]
            p['xp'] = p.get('xp', 0) + int(xp_gain)
            # Simple linear leveling: 100 XP per account level
            new_level = max(1, p['xp'] // 100 + 1)
            p['account_level'] = new_level
    except Exception:
        pass

    with open(filename, 'w') as f:
        json.dump(profiles, f)

    # Invoke post-save callback if set (used by app to enqueue syncs)
    try:
        if _post_save_callback:
            try:
                _post_save_callback(name, profiles.get(name))
            except Exception:
                pass
    except Exception:
        pass

def delete_profile(name, filename='math_blast_profiles.json'):
    profiles = load_profiles(filename)
    if name in profiles:
        del profiles[name]
        with open(filename, 'w') as f:
            json.dump(profiles, f)
        return True
    return False

def get_leaderboard(filename='math_blast_profiles.json'):
    profiles = load_profiles(filename)
    return sorted(
        [(name, data) for name, data in profiles.items()],
        key=lambda x: (x[1].get('highest_level', 1), x[1].get('total_correct', 0)),
        reverse=True
    )

class ProfileManager:
    def __init__(self, filename='math_blast_profiles.json'):
        self.filename = filename

    def load_profiles(self):
        return load_profiles(self.filename)

    def save_profiles(self, profiles):
        try:
            with open(self.filename, 'w') as f:
                json.dump(profiles, f)
        except Exception as e:
            logging.error(f"Error saving profiles: {e}")

    def save_profile(self, name, highest_level, total_correct, game_result=None, game_stats=None):
        save_profile(name, highest_level, total_correct, game_result, game_stats, filename=self.filename)

    def delete_profile(self, name):
        return delete_profile(name, filename=self.filename)

    def get_leaderboard(self):
        return get_leaderboard(filename=self.filename)

def generate_unique_tag(existing_profiles_func=None, prefix='P', filename='math_blast_profiles.json'):
    existing = {}
    try:
        if existing_profiles_func:
            existing = existing_profiles_func()
        else:
            existing = load_profiles(filename)
        used = {p.get('tag') for p in existing.values() if isinstance(p, dict) and p.get('tag')}
    except Exception:
        used = set()

    for _ in range(10):
        tag = f"{prefix}{random.randint(1000, 9999)}"
        if tag not in used:
            return tag

    t = uuid.uuid4().hex[:8].upper()
    while t in used:
        t = uuid.uuid4().hex[:8].upper()
    return t
