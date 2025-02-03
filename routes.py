from flask import Flask, render_template, request, redirect, session, jsonify, flash, url_for
from models import db, User, Match, Admin
from elo import update_elo
from werkzeug.security import generate_password_hash, check_password_hash
from elo import update_elo

def is_mobile():
    user_agent = request.user_agent.string.lower()
    return any(device in user_agent for device in ["iphone", "android", "mobile", "ipad", "tablet"])


def init_routes(app):
    @app.route("/")
    def index():
        mobile = is_mobile()
        return render_template("index.html", mobile=mobile)

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if request.method == "POST":
            username = request.form["username"]
            password = request.form["password"]
            floor = request.form["floor"]
            year = request.form["year"]

            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                return "Ce pseudo est déjà pris. Choisissez un autre."

            hashed_password = generate_password_hash(password)
            new_user = User(username=username, password=hashed_password, floor=floor, year=year)
            db.session.add(new_user)
            db.session.commit()
            return redirect("/login")

        return render_template("register.html")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        error = None  # 🔥 Ajout d'une variable pour gérer les erreurs

        if request.method == "POST":
            username = request.form.get("username")
            password = request.form.get("password")
            print(password)
            if not username or not password:
                error = "Veuillez remplir tous les champs."

            user = User.query.filter_by(username=username).first()
            if not user:
                error = "Ce pseudo n'existe pas."
            elif not check_password_hash(user.password, password):
                error = "Mot de passe incorrect."

            if error is None:  # ✅ Si tout est bon, on connecte l'utilisateur
                session["user_id"] = user.id
                return redirect("/profile")

        return render_template("login.html", error=error)

    @app.route("/admin_login", methods=["GET", "POST"])
    def admin_login():
        error = None
        if request.method == "POST":
            username = request.form.get("username")
            password = request.form.get("password")

            admin = Admin.query.filter_by(username=username).first()
            print(admin)
            print(password)
            if not admin or not check_password_hash(admin.password_hash, password):
                error = "Identifiants incorrects !"
            else:
                session["admin_id"] = admin.id
                return redirect("/admin_dashboard")

        return render_template("admin_login.html", error=error)

    @app.route("/admin_dashboard")
    def admin_dashboard():
        if "admin_id" not in session:
            return redirect("/admin_login")

        users = User.query.all()  # 🔥 Récupère tous les utilisateurs
        return render_template("admin_dashboard.html", users=users)

    @app.route("/reset_password/<int:user_id>", methods=["GET", "POST"])
    def reset_password(user_id):
        if "admin_id" not in session:
            return redirect("/admin_login")

        user = User.query.get(user_id)
        if not user:
            return "Utilisateur introuvable", 404

        if request.method == "POST":
            new_password = request.form.get("new_password")
            if not new_password:
                return "Le mot de passe ne peut pas être vide", 400

            user.password = generate_password_hash(new_password)  # 🔒 Hash du nouveau mot de passe
            db.session.commit()
            return redirect("/admin_dashboard")

        return render_template("reset_password.html", user=user)
    
    @app.route("/delete_user/<int:user_id>", methods=["POST"])
    def delete_user(user_id):
        if "admin_id" not in session:
            return redirect("/admin_login")

        user = User.query.get(user_id)
        if not user:
            return "Utilisateur introuvable", 404

        db.session.delete(user)
        db.session.commit()
        return redirect("/admin_dashboard")


    @app.route("/edit_profile", methods=["GET", "POST"])
    def edit_profile():
        if "user_id" not in session:
            return redirect("/login")  # 🔒 Redirige si non connecté

        user = User.query.get(session["user_id"])  # 🔍 Récupère l’utilisateur connecté

        if request.method == "POST":
            new_username = request.form.get("username")
            new_password = request.form.get("password")
            new_floor = request.form.get("floor")
            new_year = request.form.get("year")

            if new_username:
                user.username = new_username
            if new_password:
                user.password = generate_password_hash(new_password)  # 🔒 Hash du nouveau mot de passe
            if new_floor:
                user.floor = new_floor
            if new_year:
                user.year = new_year

            db.session.commit()  # 🔥 Mise à jour en base de données
            return redirect("/profile")  # ✅ Redirige après la mise à jour

        return render_template("edit_profile.html", user=user)


    @app.route("/logout")
    def logout():
        session.pop("user_id", None)  # 🔥 Supprime l'utilisateur de la session
        return redirect("/login") 

    @app.route("/profile")
    def profile():
        if "user_id" not in session:
            return redirect("/login")

        user = User.query.get(session["user_id"])


        # 🔥 Récupérer les matchs où le joueur a participé
        matches = Match.query.filter(
            (Match.player1_id == user.id) | (Match.player2_id == user.id) |
            (Match.player3_id == user.id) | (Match.player4_id == user.id) |
            (Match.player5_id == user.id) | (Match.player6_id == user.id)
        ).order_by(Match.date.desc()).all()

        match_history = []
        for match in matches:
            players = [
                User.query.get(match.player1_id),
                User.query.get(match.player2_id),
                User.query.get(match.player3_id) if match.player3_id else None,
                User.query.get(match.player4_id) if match.player4_id else None,
                User.query.get(match.player5_id) if match.player5_id else None,
                User.query.get(match.player6_id) if match.player6_id else None
            ]
            players = [p for p in players if p]  # 🔄 Supprimer les valeurs None

            # Vérifier si le joueur a gagné ou perdu
            team1 = players[:len(players) // 2]
            team2 = players[len(players) // 2:]

            if match.winning_team == "Team1":
                result = "Victoire" if user in team1 else "Défaite"
            else:
                result = "Victoire" if user in team2 else "Défaite"

            match_history.append({
                "date": match.date.strftime("%d/%m/%Y %H:%M"),
                "mode": match.mode,
                "players": [p.username for p in players],
                "result": result
            })

        return render_template("profile.html", user=user, match_history=match_history)


    @app.route("/ranking")
    def ranking():
        players = User.query.order_by(User.elo.desc()).all()  
        return render_template("ranking.html", players=players)



    @app.route("/notifications")
    def notifications():
        print("🔥 Route /notifications appelée !")
        if "user_id" not in session:
            return redirect("/login")

        user = User.query.get(session["user_id"])

        # 🔥 Récupère uniquement les matchs qui ne sont PAS confirmés
        pending_matches = Match.query.filter(
            ((Match.player1_id == user.id) | (Match.player2_id == user.id) |
            (Match.player3_id == user.id) | (Match.player4_id == user.id) |
            (Match.player5_id == user.id) | (Match.player6_id == user.id)),
            Match.confirmed == False  # 🔥 On filtre les matchs non confirmés uniquement
        ).all()
        print(f"DEBUG - Notifications pour {user.username} : {len(pending_matches)} match(s) en attente.")

        # Charger les objets User pour chaque match
        matches_info = []
        for match in pending_matches:
            players = [
                User.query.get(match.player1_id),
                User.query.get(match.player2_id),
                User.query.get(match.player3_id) if match.player3_id else None,
                User.query.get(match.player4_id) if match.player4_id else None,
                User.query.get(match.player5_id) if match.player5_id else None,
                User.query.get(match.player6_id) if match.player6_id else None
            ]
            matches_info.append({
                "match": match,
                "players": [p for p in players if p]  # 🔥 Filtrer les joueurs valides
            })
        matches_info.reverse()
        return render_template("notifications.html", matches=matches_info, user=user)  # ✅ On passe 'user'


    @app.route("/confirm_match/<int:match_id>")
    def confirm_match(match_id):
        match = Match.query.get(match_id)
        if not match:
            return "Match introuvable."

        user_id = session.get("user_id")
        if not user_id:
            return redirect("/login")

        # Récupérer la liste des joueurs ayant confirmé
        confirmed_players = match.confirmed_players.split(",") if match.confirmed_players else []
        confirmed_players = [p for p in confirmed_players if p]  # 🔥 Supprime les entrées vides

        
        # Vérifier si l'utilisateur a déjà confirmé
        if str(user_id) in confirmed_players:
            print("L'utilisateur a déjà confirmé ce match.")  # 🔍 Debugging
            return redirect("/notifications")

        # Ajouter l'utilisateur à la liste des confirmations
        confirmed_players.append(str(user_id))
        match.confirmed_players = ",".join(confirmed_players)

        print(f"Après confirmation: {match.confirmed_players}")  # 🔍 Debugging

        # Récupérer tous les joueurs du match
        players = [
            match.player1_id, match.player2_id,
            match.player3_id, match.player4_id,
            match.player5_id, match.player6_id
        ]
        players = [p for p in players if p]  # 🔥 Supprime les joueurs `None`

        # 🔥 Vérification propre de la condition de confirmation
        if set(confirmed_players) == set(map(str, players)):
            match.confirmed = True  # ✅ Marquer le match comme confirmé
            print(f"Match {match.id} confirmé !")  # 🔍 Debugging

            # Séparer les équipes
            team1 = players[:len(players) // 2]
            team2 = players[len(players) // 2:]

            # Déterminer les gagnants et les perdants
            if match.winning_team == "Team1":
                winners, losers = team1, team2
            else:
                winners, losers = team2, team1

            # 🔥 Mise à jour de l'ELO pour chaque joueur
            for winner in winners:
                for loser in losers:
                    winner_obj = User.query.get(winner)
                    loser_obj = User.query.get(loser)
                    winner_obj.elo, loser_obj.elo = update_elo(winner_obj.elo, loser_obj.elo)

        db.session.commit()
        return redirect("/notifications")


    @app.route("/declare_match", methods=["GET", "POST"])
    def declare_match():
        if "user_id" not in session:
            return redirect("/login")

        user = User.query.get(session["user_id"])  

        if request.method == "POST":
            mode = request.form.get("mode")
            winning_team = request.form.get("winning_team")

            if not winning_team:  
                return "Erreur : Vous devez sélectionner une équipe gagnante.", 400

            # Récupération des joueurs
            player_usernames = [
                request.form.get("player1"),
                request.form.get("player2"),
                request.form.get("player3"),
                request.form.get("player4"),
                request.form.get("player5"),
                request.form.get("player6"),
            ]
            player_usernames = [p for p in player_usernames if p]  

            # Vérifier les doublons
            if len(set(player_usernames)) != len(player_usernames):
                return "Erreur : Un joueur ne peut pas être sélectionné plusieurs fois !", 400

            players = [User.query.filter_by(username=p).first() for p in player_usernames]

            match = Match(
                player1_id=players[0].id, player2_id=players[1].id,
                player3_id=players[2].id if len(players) > 2 else None,
                player4_id=players[3].id if len(players) > 3 else None,
                player5_id=players[4].id if len(players) > 4 else None,
                player6_id=players[5].id if len(players) > 5 else None,
                winning_team=winning_team,
                mode=mode,
                confirmed=False
            )

            db.session.add(match)
            db.session.commit()

            return redirect("/notifications")

        return render_template("declare_match.html", user=user)

    @app.route("/search_users")
    def search_users():
        query = request.args.get("q", "").strip().lower()  # 🔥 Récupère la recherche
        if not query:
            return jsonify([])  # 🔥 Retourne une liste vide si rien n'est tapé

        users = User.query.filter(User.username.ilike(f"{query}%")).limit(10).all()  # 🔍 Trouve les joueurs
        results = [{"id": user.id, "username": user.username} for user in users]  # 🔄 Formatte la réponse JSON

        return jsonify(results)  # 🔥 Renvoie la liste des joueurs en JSON
    
    @app.route("/search_profile")
    def search_profile():
        query = request.args.get("q", "").strip().lower()
        
        if not query:
            flash("Veuillez entrer un pseudo.", "warning")
            return redirect("/")  

        user = User.query.filter(User.username.ilike(f"{query}%")).first()
        
        if not user:
            flash("Utilisateur introuvable", "danger")
            return redirect("/")

        return redirect(url_for("view_profile", user_id=user.id))

    @app.route("/profile/<int:user_id>")
    def view_profile(user_id):
        user = User.query.get(user_id)
        if not user:
            flash("Profil introuvable", "danger")
            return redirect("/search_profile")

        # 🔥 Récupérer les matchs où ce joueur a participé
        matches = Match.query.filter(
            (Match.player1_id == user.id) | (Match.player2_id == user.id) |
            (Match.player3_id == user.id) | (Match.player4_id == user.id) |
            (Match.player5_id == user.id) | (Match.player6_id == user.id)
        ).order_by(Match.date.desc()).all()

        match_history = []
        for match in matches:
            players = [
                User.query.get(match.player1_id),
                User.query.get(match.player2_id),
                User.query.get(match.player3_id) if match.player3_id else None,
                User.query.get(match.player4_id) if match.player4_id else None,
                User.query.get(match.player5_id) if match.player5_id else None,
                User.query.get(match.player6_id) if match.player6_id else None
            ]
            players = [p for p in players if p]  

            team1 = players[:len(players) // 2]
            team2 = players[len(players) // 2:]

            if match.winning_team == "Team1":
                result = "Victoire" if user in team1 else "Défaite"
            else:
                result = "Victoire" if user in team2 else "Défaite"

            match_history.append({
                "date": match.date.strftime("%d/%m/%Y %H:%M"),
                "mode": match.mode,
                "players": [p.username for p in players],
                "result": result
            })

        return render_template("profile_view.html", user=user, match_history=match_history)
        
        