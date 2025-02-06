import math

K = 32  # Facteur de mise à jour de l'ELO

def expected_score(player_elo, opponent_elo):
    return 1 / (1 + 10 ** ((opponent_elo - player_elo) / 400))

def update_elo(winner_elo, loser_elo, mode):
    alpha = 1
    if mode == 'Capacks':
        alpha = 1
    if mode == 'CD':
        alpha = 1
    if mode == 'Davis':
        alpha = 1
    if mode == 'Trevis':
        alpha = 1
    
    expected_win = expected_score(winner_elo, loser_elo)
    new_winner_elo = round(winner_elo + alpha*K * (1 - expected_win))
    new_loser_elo = round(loser_elo + alpha*K * (0 - (1 - expected_win)))
    return new_winner_elo, new_loser_elo

def get_tier(elo):
    if elo < 450:
        return "Bronze", "bronze.png"
    elif elo < 800:
        return "Argent", "argent.png"
    elif elo < 1300:
        return "Or", "or.png"
    elif elo < 1600:
        return "Platine", "platine.png"
    elif elo < 2000:
        return "Diamant", "diamant.png"
    else:
        return "Légende", "legende.png"



