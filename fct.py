import math

K  = 50  # Facteur de mise à jour de l'ELO pour gagnants


def expected_score(player_elo, opponent_elo):
    return 1 / (1 + 10 ** ((opponent_elo - player_elo) / 400))

def update_elo(winner_elo, loser_elo, mode):
    alpha = 1
    if mode == 'Capacks':
        alpha = 1
    if mode =='16evolve':
        alpha = 0.6
    if mode == 'CD':
        alpha = 0.5
    if mode == 'Davis':
        alpha = 0.5
    if mode == 'Trevis':
        alpha = 0.5
    
    expected_win = expected_score(winner_elo, loser_elo)
    new_winner_elo = round(winner_elo + alpha*K * (1 - expected_win))
    new_loser_elo = round(loser_elo + alpha*K * (0 - (1 - expected_win)))
    return new_winner_elo, new_loser_elo

def get_tier(elo):
    if elo < 350:
        return "0chiasse", "caca.png"
    elif elo < 500:
        return "Bronze", "bronze.png"
    elif elo < 800:
        return "Argent", "argent.png"
    elif elo < 1100:
        return "Or", "or.png"
    elif elo < 1400:
        return "Platine", "platine.png"
    elif elo < 1900:
        return "Diamant", "diamant.png"
    else:
        return "Légende", "legende.png"




