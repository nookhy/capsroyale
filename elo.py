import math

K = 32  # Facteur de mise à jour de l'ELO

def expected_score(player_elo, opponent_elo):
    return 1 / (1 + 10 ** ((opponent_elo - player_elo) / 400))

def update_elo(winner_elo, loser_elo):
    expected_win = expected_score(winner_elo, loser_elo)
    new_winner_elo = round(winner_elo + K * (1 - expected_win))
    new_loser_elo = round(loser_elo + K * (0 - (1 - expected_win)))
    return new_winner_elo, new_loser_elo


from werkzeug.security import generate_password_hash

#print(generate_password_hash('saucisseV45'))