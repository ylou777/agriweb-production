# run_app.py

# Import du fichier Python modifié au lieu du module compilé
import agriweb_source

if __name__ == '__main__':
    # Lance le serveur Flask et ouvre le navigateur sur l'IP réelle
    agriweb_source.main_server()