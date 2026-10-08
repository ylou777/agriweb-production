"""Tests du mode « Cibles chaleur News Solar » (accès restreint + données).

Lancement (depuis la racine du dépôt) :
    python -m unittest tests.test_cibles_chaleur -v

Aucune base de production n'est utilisée : l'authentification réelle est
exercée sur une base SQLite temporaire (auth_database en mode local), la copie
dans le CRM est simulée.
"""
import json
import os
import sys
import tempfile
import unittest
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ.pop('DATABASE_URL', None)  # jamais de PostgreSQL dans les tests

from flask import Flask  # noqa: E402

import auth_database  # noqa: E402
import cibles_chaleur  # noqa: E402

DATA = cibles_chaleur.DEFAULT_PATH


def make_app(calls):
    app = Flask(__name__, template_folder=os.path.join(ROOT, 'templates'))
    app.secret_key = 'test'
    app.config['TESTING'] = True

    def fake_ajouter(r, uid):
        calls.append((r, uid))
        return 4242, True

    cibles_chaleur.register_cibles_chaleur_routes(app, fake_ajouter)
    return app


class _AuthDB:
    """Base d'authentification SQLite temporaire avec 3 comptes."""

    def __enter__(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.patch = mock.patch.object(auth_database, 'SQLITE_PATH', os.path.join(self.tmp.name, 'u.db'))
        self.patch.start()
        auth_database.init_auth_tables()
        conn = auth_database.get_auth_db()
        cur = conn.cursor()
        for uid, email, admin in ((1, 'admin@news-solar.com', 1), (2, 'client@autre-installateur.fr', 0),
                                  (3, 'commercial@news-solar.com', 0)):
            cur.execute("INSERT INTO users (id, email, name, password_hash, salt, is_admin) VALUES (?,?,?,?,?,?)",
                        (uid, email, email, 'x', 'y', admin))
            cur.execute("INSERT INTO user_sessions (user_id, session_token, expires_at) VALUES (?,?,?)",
                        (uid, f'tok{uid}', '2099-01-01 00:00:00'))
        cur.execute("INSERT INTO user_sessions (user_id, session_token, expires_at) VALUES (?,?,?)",
                    (1, 'expire', '2000-01-01 00:00:00'))
        conn.commit()
        conn.close()
        return self

    def __exit__(self, *a):
        self.patch.stop()
        self.tmp.cleanup()


def env(**kw):
    base = {'FEATURE_CIBLES_CHALEUR': '', 'CIBLES_CHALEUR_USERS': '', 'CIBLES_CHALEUR_PATH': ''}
    base.update(kw)
    return mock.patch.dict(os.environ, base)


class TestAcces(unittest.TestCase):
    URL = '/api/industriel/cibles-chaleur'

    def setUp(self):
        self.calls = []
        self.app = make_app(self.calls)
        self.db = _AuthDB().__enter__()

    def tearDown(self):
        self.db.__exit__()

    def get(self, token=None, view_as=None):
        c = self.app.test_client()
        if token:
            c.set_cookie('session_token', token)
        if view_as:
            with c.session_transaction() as s:
                s['admin_view_as_user_id'] = view_as
        return c.get(self.URL)

    def test_flag_absent_refuse_meme_admin(self):
        with env():
            self.assertEqual(self.get('tok1').status_code, 404)

    def test_anonyme_401(self):
        with env(FEATURE_CIBLES_CHALEUR='1'):
            self.assertEqual(self.get().status_code, 401)
            self.assertEqual(self.get('expire').status_code, 401)

    def test_admin_autorise_si_liste_vide(self):
        with env(FEATURE_CIBLES_CHALEUR='1'):
            r = self.get('tok1')
            self.assertEqual(r.status_code, 200)
            self.assertEqual(r.headers['Cache-Control'], 'private, no-store')
            gj = json.loads(r.data)
            self.assertEqual(gj['type'], 'FeatureCollection')

    def test_autre_locataire_refuse(self):
        with env(FEATURE_CIBLES_CHALEUR='1'):
            self.assertEqual(self.get('tok2').status_code, 404)
        with env(FEATURE_CIBLES_CHALEUR='1', CIBLES_CHALEUR_USERS='commercial@news-solar.com'):
            self.assertEqual(self.get('tok2').status_code, 404)

    def test_liste_blanche(self):
        with env(FEATURE_CIBLES_CHALEUR='true', CIBLES_CHALEUR_USERS='Commercial@News-Solar.com, x@y.fr'):
            self.assertEqual(self.get('tok3').status_code, 200)
            # liste non vide : l'admin n'y figurant pas est refusé
            self.assertEqual(self.get('tok1').status_code, 404)

    def test_admin_view_as_refuse(self):
        """Admin en vue « voir comme le client » : le mode ne doit pas apparaître."""
        with env(FEATURE_CIBLES_CHALEUR='1'):
            self.assertEqual(self.get('tok1', view_as=2).status_code, 404)

    def test_visible_pour_gabarit(self):
        with env(FEATURE_CIBLES_CHALEUR='1'):
            with self.app.test_request_context(headers={'Cookie': 'session_token=tok1'}):
                self.assertTrue(cibles_chaleur.cibles_chaleur_visible())
            with self.app.test_request_context(headers={'Cookie': 'session_token=tok2'}):
                self.assertFalse(cibles_chaleur.cibles_chaleur_visible())

    def test_ajout_crm(self):
        url = self.URL + '/ajouter-au-crm'
        with open(DATA, encoding='utf-8') as f:
            gj = json.load(f)
        site = next(f for f in gj['features'] if f['properties']['kind'] == 'site')
        with env(FEATURE_CIBLES_CHALEUR='1'):
            c = self.app.test_client()
            c.set_cookie('session_token', 'tok2')
            self.assertEqual(c.post(url, json={'id': site['id']}).status_code, 404)
            self.assertEqual(self.calls, [])
            c.set_cookie('session_token', 'tok1')
            self.assertEqual(c.post(url, json={'id': 'inexistant'}).status_code, 404)
            self.assertEqual(c.post(url, json={}).status_code, 400)
            # un éventuel e-mail cible est ignoré : la cible est toujours le compte courant
            r = c.post(url, json={'id': site['id'], 'email': 'client@autre-installateur.fr'})
            self.assertEqual(r.status_code, 200, r.data)
            self.assertEqual(json.loads(r.data)['prospect_id'], 4242)
            ligne, uid = self.calls[-1]
            self.assertEqual(uid, 1)
            self.assertEqual(ligne['operateur_nom'], site['properties'].get('raison_sociale') or 'Exploitant à identifier')
            self.assertEqual(json.loads(ligne['data_json'])['cible_chaleur_id'], site['id'])


class TestGabarit(unittest.TestCase):
    def render(self, flag):
        app = make_app([])
        with app.test_request_context():
            from flask import render_template
            return render_template('crm_carte.html', is_admin=False, cibles_chaleur=flag)

    def test_mode_absent_du_html_sans_droit(self):
        html = self.render(False)
        self.assertNotIn('cibles-chaleur', html)
        self.assertNotIn('Cibles chaleur', html)
        self.assertNotIn('mChaleur', html)

    def test_mode_present_avec_droit(self):
        html = self.render(True)
        self.assertIn('/api/industriel/cibles-chaleur', html)
        self.assertIn('id="mChaleur"', html)


class TestDonnees(unittest.TestCase):
    """Validation structurelle du GeoJSON embarqué."""

    @classmethod
    def setUpClass(cls):
        cls.size = os.path.getsize(DATA)
        with open(DATA, encoding='utf-8') as f:
            cls.gj = json.load(f)

    def test_taille(self):
        self.assertLess(self.size, 2_000_000)

    def test_geojson_valide(self):
        gj = self.gj
        self.assertEqual(gj['type'], 'FeatureCollection')
        ids = set()
        for f in gj['features']:
            self.assertEqual(f['type'], 'Feature')
            self.assertEqual(f['geometry']['type'], 'Point')
            lon, lat = f['geometry']['coordinates']
            # France métropolitaine (ordre RFC 7946 : lon, lat)
            self.assertTrue(-5.5 <= lon <= 9.8 and 41.2 <= lat <= 51.2, (f['id'], lon, lat))
            self.assertNotIn(f['id'], ids)
            ids.add(f['id'])
            self.assertIn(f['properties']['kind'], ('site', 'poste_source'))

    def test_sites_et_postes(self):
        sites = [f for f in self.gj['features'] if f['properties']['kind'] == 'site']
        postes = {f['properties']['code'] for f in self.gj['features'] if f['properties']['kind'] == 'poste_source'}
        self.assertGreater(len(sites), 1000)
        sirets = [f['properties'].get('siret') for f in sites if f['properties'].get('siret')]
        self.assertEqual(len(sirets), len(set(sirets)), 'doublons SIRET')
        for f in sites:
            p = f['properties']
            self.assertTrue(0 <= p['score'] <= 100)
            self.assertIn(p['ps_code'], postes)
            self.assertTrue(0 <= p['ps_distance_km'] < 60)
        self.assertEqual(self.gj['metadata']['n_sites'], len(sites))


if __name__ == '__main__':
    unittest.main()
