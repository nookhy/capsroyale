from flask import Flask, render_template, request, redirect, session, jsonify, flash, url_for
from models import db, User, Match, Admin, DrawMatch
from fct import update_elo, get_tier
from werkzeug.security import generate_password_hash, check_password_hash
from fct import update_elo
from sqlalchemy.sql import func

import os
from flask import current_app
from werkzeug.utils import secure_filename
from datetime import datetime
import pytz
local_tz = pytz.timezone('Europe/Paris')

from PIL import Image, ExifTags


def is_mobile():
    user_agent = request.user_agent.string.lower()
    return any(device in user_agent for device in ["iphone", "android", "mobile", "ipad", "tablet"])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config["ALLOWED_EXTENSIONS"]


def init_routes(app):
    @app.route("/")
    def index():
        mobile = is_mobile()
        user = None
        if "user_id" in session:
            user = User.query.get(session["user_id"])  # 🔥 Récupère l'utilisateur connecté
        return render_template("home.html", user=user, mobile=mobile)  # ✅ On envoie user + mobile
    

    @app.route("/check_notifications")
    def check_notifications():
        if "user_id" not in session:
            return jsonify({"unread": 0})

        user_id = session["user_id"]

        # 🔥 Vérifie s'il y a des matchs non confirmés pour ce joueur
        pending_matches = Match.query.filter(
            ((Match.player1_id == user_id) | (Match.player2_id == user_id) |
            (Match.player3_id == user_id) | (Match.player4_id == user_id) |
            (Match.player5_id == user_id) | (Match.player6_id == user_id)),
            Match.confirmed == False
        ).count()

        return jsonify({"unread": pending_matches})
    
    @app.route("/register", methods=["GET", "POST"])
    def register():
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form["password"]
            floor = request.form["floor"]
            year = request.form["year"]
            profile_picture = request.files.get("profile_picture")
            

            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                return "Ce pseudo est déjà pris. Choisissez un autre."

            hashed_password = generate_password_hash(password)

            filename = None
            if profile_picture and allowed_file(profile_picture.filename):
                safe_name = secure_filename(profile_picture.filename)
                filename = f"{username}_profile.jpg"
                filepath = os.path.join(current_app.config["UPLOAD_FOLDER_PROFILE"], filename)

                img = Image.open(profile_picture)
                img = img.convert("RGB")
                img.thumbnail((300, 300))
                img.save(filepath, "JPEG", quality=80)


            new_user = User(username=username, password=hashed_password, floor=floor, year=year, profile_picture=filename if filename else "default.png")
            db.session.add(new_user)
            db.session.commit()
            return redirect("/login")

        return render_template("register.html")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        error = None  # 🔥 Ajout d'une variable pour gérer les erreurs

        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password")
            
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
        matches = Match.query.order_by(Match.date.desc()).all()  # 🔥 Récupère tous les matchs par date
        return render_template("admin_dashboard.html", users=users, matches=matches)
        
    
    @app.route("/delete_match/<int:match_id>", methods=["POST"])
    def delete_match(match_id):
        if "admin_id" not in session:
            return redirect("/admin_login")

        match = Match.query.get(match_id)
        if match:
        # 🔥 Supprimer l'image si elle existe
            if match.photo_filename:
                photo_path = os.path.join(current_app.config["UPLOAD_FOLDER"], match.photo_filename)
                if os.path.exists(photo_path):
                    os.remove(photo_path)
                    print(f"🗑️ Image supprimée : {photo_path}")
                else:
                    print(f"⚠️ Fichier image introuvable : {photo_path}")

            db.session.delete(match)
            db.session.commit()
            flash("Match supprimé avec succès", "success")
        else:
            flash("Match introuvable", "danger")

        return redirect("/admin_dashboard")

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

    @app.route("/edit_elo/<int:user_id>", methods=["GET", "POST"])
    def edit_elo(user_id):
        if "admin_id" not in session:
            return redirect("/admin_login")

        user = User.query.get(user_id)
        if not user:
            return "Utilisateur introuvable", 404

        if request.method == "POST":
            new_elo = request.form.get("new_elo")
            try:
                new_elo = int(new_elo)
            except ValueError:
                return "Le ELO doit être un nombre valide.", 400

            user.elo = new_elo  # 🔥 Mise à jour du ELO
            db.session.commit()
            return redirect("/admin_dashboard")

        return render_template("edit_elo.html", user=user)

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
            new_photo = request.files.get("profile_picture")


            if new_username:
                user.username = new_username
            if new_password:
                user.password = generate_password_hash(new_password)  # 🔒 Hash du nouveau mot de passe
            if new_floor:
                user.floor = new_floor
            if new_year:
                user.year = new_year

            if new_photo and allowed_file(new_photo.filename):
                # Supprimer ancienne photo si ce n’est pas default.png
                if user.profile_picture and user.profile_picture != "default.png":
                    try:
                        os.remove(os.path.join(current_app.config["UPLOAD_FOLDER_PROFILE"], user.profile_picture))
                    except FileNotFoundError:
                        pass

                filename = f"{user.id}_profile.jpg"
                filepath = os.path.join(current_app.config["UPLOAD_FOLDER_PROFILE"], filename)

                img = Image.open(new_photo)
                img = img.convert("RGB")
                img.thumbnail((300, 300))
                img.save(filepath, "JPEG", quality=70)

                user.profile_picture = filename

            db.session.commit()  # 🔥 Mise à jour en base de données
            return redirect("/profile")  # ✅ Redirige après la mise à jour

        return render_template("edit_profile.html", user=user)


    @app.route("/logout")
    def logout():
        session.pop("user_id", None)  # 🔥 Supprime l'utilisateur de la session
        return redirect("/login") 

    @app.route("/logout_admin")
    def logout_admin():
        session.pop("admin_id", None)  # 🔥 Supprime l'ID admin de la session
        return redirect("/admin_login")  # ✅ Redirige vers la page de connexion admin

    @app.route("/profile")
    def profile():
        if "user_id" not in session:
            return redirect("/login")

        user = User.query.get(session["user_id"])
        if not user:  # 🛑 Cas où l'utilisateur n'existe pas (supprimé ou invalide)
            session.pop("user_id", None)  # Supprime l'ID invalide de la session
            return redirect("/login")  # Redirige vers la connexion
        tier, icon = get_tier(user.elo)

        # 🔥 Récupérer les matchs où le joueur a participé
        matches = Match.query.filter(
            ((Match.player1_id == user.id) | (Match.player2_id == user.id) |
            (Match.player3_id == user.id) | (Match.player4_id == user.id) |
            (Match.player5_id == user.id) | (Match.player6_id == user.id)),
            Match.confirmed == True # 🔥 On filtre les matchs confirmés uniquement
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
            elif match.winning_team == "Team2":
                result = "Victoire" if user in team2 else "Défaite"
            else:
                result = "Match nul"

            match_history.append({
                "date": match.date.strftime("%d/%m/%Y %H:%M"),
                "mode": match.mode,
                "players": [p.username for p in players],
                "result": result
            })

        return render_template("profile.html", user=user, match_history=match_history, tier=tier, icon=icon)


    @app.route("/ranking")
    def ranking():
        players = User.query.order_by(User.elo.desc()).all()  # Classement général
        current_user_id = session.get("user_id")
        
        
        # 🔥 Ajouter les tiers aux joueurs
        ranked_players = []
        for player in players:
            tier, icon = get_tier(player.elo)
            ranked_players.append({
                "id": player.id,
                "username": player.username,
                "floor": player.floor,
                "year": player.year,
                "elo": player.elo,
                "tier": tier,
                "icon": icon,
                "profile_picture": player.profile_picture
            })

        # 🔥 Classement des étages par SOMME des ELO
        ranking_by_total = (
            db.session.query(User.floor, func.sum(User.elo).label("total_elo"))
            .group_by(User.floor)
            .order_by(func.sum(User.elo).desc())
            .all()
        )

        # 🔥 Classement des étages par MOYENNE des ELO
        ranking_by_average = (
            db.session.query(User.floor, func.avg(User.elo).label("avg_elo"))
            .group_by(User.floor)
            .order_by(func.avg(User.elo).desc())
            .all()
        )

        return render_template(
            "ranking.html",
            players=ranked_players,
            ranking_by_total=ranking_by_total,
            ranking_by_average=ranking_by_average,
            current_user_id=current_user_id  # Passe l'ID de l'utilisateur connecté
        )


    @app.route("/notifications")
    def notifications():
        
        if "user_id" not in session:
            return redirect("/login")

        user = User.query.get(session["user_id"])
        if not user:  # 🛑 Cas où l'utilisateur a été supprimé
            session.pop("user_id", None)
            return redirect("/login")

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
            players = [p for p in players if p]
            print(f"DEBUG: players = {players}")
            # 🔥 Déterminer les gagnants en fonction de la team gagnante
            if match.winning_team == "Team1":
                winners = players[:len(players) // 2]  # 🔥 La moitié des joueurs sont Team 1
            elif match.winning_team == "Team2":
                winners = players[len(players) // 2:]  # 🔥 L’autre moitié est Team 2
            else:
                winners = [DrawMatch("Égalité")]  # 🔥 Sinon, c'est un match nul

            matches_info.append({
            "match": match,
            "players": players,
            "winners": winners
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

            draw = False
            # Déterminer les gagnants et les perdants
            if match.winning_team == "Team1":
                winners, losers = team1, team2
                draw = False
            elif match.winning_team == "Team2":
                winners, losers = team2, team1
                draw = False
            else:
                winners, losers = team1, team2
                draw = True


            # 🔥 Mise à jour de l'ELO pour chaque joueur
            moywin = 0
            moylose = 0
            for winner in winners:
                for loser in losers:
                    winner_obj = User.query.get(winner)
                    loser_obj = User.query.get(loser)
                    moywin += winner_obj.elo / len(winners)
                    moylose += loser_obj.elo / len(losers)
            for winner in winners:
                winner_obj = User.query.get(winner)
                winner_obj.elo, _ = update_elo(winner_obj.elo, moylose, match.mode, draw)
            for loser in losers:
                loser_obj = User.query.get(loser)
                _, loser_obj.elo = update_elo(moywin, loser_obj.elo, match.mode, draw)


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
            commentaire = request.form.get("commentaire", "").strip()  # ✅ Récupère le commentaire
            photo = request.files.get("photo")
            photo_filename = None

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


            if photo and allowed_file(photo.filename):
                filename = secure_filename(photo.filename)
                timestamp = datetime.now(local_tz).strftime("%Y%m%d%H%M%S")
                players_ids = "-".join(str(p.id) for p in players)
                photo_filename = f"{timestamp}_{players_ids}.jpg"
                photo_path = os.path.join(current_app.config["UPLOAD_FOLDER"], photo_filename)
                photo.save(photo_path)
                # Limiter la taille de l'image (ex: largeur max 600px) et la réorienter si nécessaire
                img_path = os.path.join("static/uploads", photo_filename)
                with Image.open(img_path) as img:
                    try:
                        for orientation in ExifTags.TAGS.keys():
                            if ExifTags.TAGS[orientation] == 'Orientation':
                                break
                        exif = img._getexif()
                        if exif is not None:
                            orientation_value = exif.get(orientation)
                            if orientation_value == 3:
                                img = img.rotate(180, expand=True)
                            elif orientation_value == 6:
                                img = img.rotate(270, expand=True)
                            elif orientation_value == 8:
                                img = img.rotate(90, expand=True)
                    except (AttributeError, KeyError, IndexError):
                        pass  # Pas de données EXIF ou erreur, on ignore

                    img = img.convert("RGB")  # Pour compatibilité JPEG
                    img.thumbnail((600, 600))
                    img.save(img_path, "JPEG", quality=70)
                
                # ✅ Vérifier s’il y a trop d’images
                photo_matches = Match.query.filter(Match.photo_filename != None).order_by(Match.date.asc()).all()
                if len(photo_matches) >= 2:
                    oldest_match = photo_matches[0]  # le plus ancien
                    if oldest_match.photo_filename:
                        old_path = os.path.join(current_app.config["UPLOAD_FOLDER"], oldest_match.photo_filename)
                        if os.path.exists(old_path):
                            os.remove(old_path)
                    oldest_match.photo_filename = None
                    db.session.commit()

            

            match = Match(
                player1_id=players[0].id, player2_id=players[1].id,
                player3_id=players[2].id if len(players) > 2 else None,
                player4_id=players[3].id if len(players) > 3 else None,
                player5_id=players[4].id if len(players) > 4 else None,
                player6_id=players[5].id if len(players) > 5 else None,
                winning_team=winning_team,
                mode=mode,
                confirmed=False,
                commentaire=commentaire,  # ✅ Stocke le commentaire
                photo_filename=photo_filename

            )

            db.session.add(match)
            db.session.commit()

            return redirect("/notifications")

        return render_template("declare_match.html", user=user)

    @app.route("/reject_match/<int:match_id>")
    def reject_match(match_id):
        match = Match.query.get(match_id)
        if not match:
            return "Match introuvable.", 404  # 🔥 Retourne une erreur si le match n'existe pas
        
        user_id = session.get("user_id")
        if not user_id:
            return redirect("/login")  # 🔒 Redirige si l'utilisateur n'est pas connecté

        # 🔥 Vérifie si l'utilisateur fait bien partie du match
        players = [
            match.player1_id, match.player2_id,
            match.player3_id, match.player4_id,
            match.player5_id, match.player6_id
        ]
        players = [p for p in players if p]  # 🔥 Supprime les joueurs `None`

        if user_id not in players:
            return "Vous ne pouvez pas refuser ce match.", 403  # 🔥 Empêche les autres de supprimer un match

        print(f"🚨 Match {match.id} refusé par {user_id}, suppression en cours...")

        # 🔥 Supprimer l'image si elle existe
        if match.photo_filename:
            photo_path = os.path.join(current_app.config["UPLOAD_FOLDER"], match.photo_filename)
            if os.path.exists(photo_path):
                os.remove(photo_path)
                print(f"🗑️ Image supprimée : {photo_path}")
            else:
                print(f"⚠️ Fichier image introuvable : {photo_path}")

        # 🔥 Supprime le match de la base de données
        db.session.delete(match)
        db.session.commit()

        return redirect("/notifications")

    @app.route("/feed")
    def feed():
        matches = Match.query.filter(Match.confirmed==True).order_by(Match.date.desc()).limit(50).all()  # ✅ 50 derniers matchs confirmés
        #for match in matches:
            #if isinstance(match.date, int):
                #match.date = str(match.date) 
        matches_info = []
        
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
            # 🔥 Déterminer les gagnants en fonction de la team gagnante
            if match.winning_team == "Team1":
                winners = players[:len(players) // 2]  # 🔥 La moitié des joueurs sont Team 1
            elif match.winning_team == "Team2":
                winners = players[len(players) // 2:]  # 🔥 L’autre moitié est Team 2
            else: 
                winners = [DrawMatch("Égalité")]

            matches_info.append({
                "match": match,
                "players": players,  # 🔥 Filtrer les joueurs valides
                "winners": winners
            })

        return render_template("feed.html", matches=matches_info)


    @app.route("/search_users")
    def search_users():
        query = request.args.get("q", "").strip()
        print(query)  # 🔥 Récupère la recherche
        if not query:
            return jsonify([])  # 🔥 Retourne une liste vide si rien n'est tapé
        
        # 🔥 S'assurer que la requête est bien encodée en UTF-8
        try:
            query = query.encode('utf-8').decode('utf-8')  
        except UnicodeDecodeError:
            return jsonify([])

        users = User.query.filter(User.username.ilike(f"{query}%")).limit(10).all()  # 🔍 Trouve les joueurs
        results = [{"id": user.id, "username": user.username} for user in users]  # 🔄 Formatte la réponse JSON

        return jsonify(results)  # 🔥 Renvoie la liste des joueurs en JSON
    
    @app.route("/search_profile")
    def search_profile():
        query = request.args.get("q", "").strip()
        
        if not query:
            flash("Veuillez entrer un pseudo.", "warning")
            return redirect("/")  
            
        # 🔥 S'assurer que la requête est bien encodée en UTF-8
        try:
            query = query.encode('utf-8').decode('utf-8')  
        except UnicodeDecodeError:
            return jsonify([])

        user = User.query.filter(User.username.ilike(f"{query}%")).first()
        
        if not user:
            flash("Utilisateur introuvable", "danger")
            return redirect("/")

        return redirect(url_for("view_profile", user_id=user.id))

    @app.route("/profile/<int:user_id>")
    def view_profile(user_id):
        user = User.query.get(user_id)
        tier, icon = get_tier(user.elo)
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
            elif match.winning_team == "Team2":
                result = "Victoire" if user in team2 else "Défaite"
            else:
                result = "Match nul"

            match_history.append({
                "date": match.date.strftime("%d/%m/%Y %H:%M"),
                "mode": match.mode,
                "players": [p.username for p in players],
                "result": result
            })

        return render_template("profile_view.html", user=user, match_history=match_history, tier=tier, icon=icon)
        
        