CAPS ROYALE

Le site de classement ELO du caps de ECL

pour lancer le site en local et faire des tests, copie les fichiers en local sur ton ordi, ouvre un terminal, et va dans la bonne directory avec cd /Ton/Chemin/Vers/Le/Projet
puis tape flask run --host=0.0.0.0 --port=5001 dans le terminal, tu pourras te co au serv depuis le meme ordi en rentrant http://127.0.0.1:5001/ sur ta barre d'URL.
Si jamais ca marche pas c'est qu'il te manque des modules (comme flask ou SQLalchemy par exemple)
Pour gerer Flask, dans le terminal:

python -m venv venv
source venv/bin/activate
pip install flask flask-sqlalchemy flask-wtf werkzeug
pip install werkzeug
flask run --host=0.0.0.0 --port=5001    (pour lancer le serv)



lien du site deployé par Render: https://eclcapsroyale.onrender.com

postgresql: postgresql://neondb_owner:npg_AWxw6HP8rvFC@ep-lingering-bread-a9askrmq-pooler.gwc.azure.neon.tech/neondb?sslmode=require

https://console.neon.tech/app/projects/autumn-sun-17798779/branches/br-dawn-meadow-a9yerblh/tables?database=neondb

https://dashboard.render.com/web/srv-cugt9d8gph6c73d5uf8g/logs


pour maj du site depuis raspberry:
ssh wflouret@IP_PUBLIQUE_DE_TON_AMI
cd /home/wflouret/capsroyale
./deploy.sh
