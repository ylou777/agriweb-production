"""
Module Mail HeliaPV — Interface email complète
- Lecture IMAP (OVH)
- Envoi SMTP avec pièces jointes
- Calendrier (événements JSON)
- Envoi de propositions aux prospects CRM
"""

import os
import json
import imaplib
import smtplib
import email
import uuid
import base64
from email import encoders
from email.header import decode_header, make_header
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import parsedate_to_datetime, formataddr, formatdate, make_msgid
from datetime import datetime, timedelta
from flask import Blueprint, render_template, jsonify, request, session, redirect, url_for

mail_bp = Blueprint('mail_bp', __name__, url_prefix='/mail')

# ─── Helpers config ──────────────────────────────────────────────────────────

def _mail_config():
    return {
        'imap_server': os.environ.get('MAIL_IMAP_SERVER', 'imap.mail.ovh.net'),
        'smtp_server': os.environ.get('MAIL_SERVER', 'ssl0.ovh.net'),
        'smtp_port':   int(os.environ.get('MAIL_PORT', 465)),
        'username':    os.environ.get('MAIL_USERNAME', ''),
        'password':    os.environ.get('MAIL_PASSWORD', ''),
    }

def _require_admin():
    """Retourne None si admin connecté, sinon redirect."""
    session_token = session.get('session_token') or request.cookies.get('session_token')
    if not session_token:
        return redirect('/auth/login')
    try:
        from auth_database import get_auth_db
        conn = get_auth_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT u.is_admin FROM users u
            JOIN user_sessions s ON u.id = s.user_id
            WHERE s.session_token = ? AND s.expires_at > CURRENT_TIMESTAMP
        ''', (session_token,))
        result = cursor.fetchone()
        conn.close()
        if result and result[0]:
            return None  # admin OK
        return redirect('/')  # connecté mais pas admin
    except Exception as e:
        print(f"⚠️ [MAIL AUTH] {e}")
        return redirect('/auth/login')

# ─── IMAP helpers ─────────────────────────────────────────────────────────────

def _imap_connect():
    cfg = _mail_config()
    imap = imaplib.IMAP4_SSL(cfg['imap_server'], 993)
    imap.login(cfg['username'], cfg['password'])
    return imap

def _decode_str(value):
    """Décode un header encodé (UTF-8, latin-1, base64…)."""
    if value is None:
        return ''
    try:
        return str(make_header(decode_header(value)))
    except Exception:
        return str(value)

def _parse_message_headers(raw_msg):
    """Parse un message email et retourne un dict de headers."""
    msg = email.message_from_bytes(raw_msg)
    subject = _decode_str(msg.get('Subject', '(Sans objet)'))
    sender  = _decode_str(msg.get('From', ''))
    to      = _decode_str(msg.get('To', ''))
    date_str = msg.get('Date', '')
    try:
        date = parsedate_to_datetime(date_str).isoformat() if date_str else ''
    except Exception:
        date = date_str
    return {
        'subject': subject,
        'from':    sender,
        'to':      to,
        'date':    date,
        'message_id': msg.get('Message-ID', ''),
    }

def _parse_message_full(raw_msg):
    """Parse un message complet : headers + corps + pièces jointes."""
    msg = email.message_from_bytes(raw_msg)
    headers = _parse_message_headers(raw_msg)

    body_html  = ''
    body_text  = ''
    attachments = []

    for part in msg.walk():
        content_type = part.get_content_type()
        disposition  = str(part.get('Content-Disposition') or '')

        if 'attachment' in disposition:
            filename = _decode_str(part.get_filename() or 'fichier')
            payload  = part.get_payload(decode=True)
            if payload:
                attachments.append({
                    'filename': filename,
                    'mime':     content_type,
                    'data_b64': base64.b64encode(payload).decode('utf-8'),
                    'size':     len(payload),
                })
        elif content_type == 'text/html' and not body_html:
            charset = part.get_content_charset() or 'utf-8'
            try:
                body_html = part.get_payload(decode=True).decode(charset, errors='replace')
            except Exception:
                body_html = part.get_payload(decode=True).decode('utf-8', errors='replace')
        elif content_type == 'text/plain' and not body_text:
            charset = part.get_content_charset() or 'utf-8'
            try:
                body_text = part.get_payload(decode=True).decode(charset, errors='replace')
            except Exception:
                body_text = part.get_payload(decode=True).decode('utf-8', errors='replace')

    return {
        **headers,
        'body_html':   body_html,
        'body_text':   body_text,
        'attachments': attachments,
    }

def _fetch_messages(folder='INBOX', limit=50, search='ALL'):
    """Retourne une liste de messages (headers seulement) depuis IMAP."""
    try:
        imap = _imap_connect()
        imap.select(folder, readonly=True)
        _, data = imap.search(None, search)
        ids = data[0].split()
        ids = ids[-limit:]  # Derniers messages

        messages = []
        for uid in reversed(ids):
            _, msg_data = imap.fetch(uid, '(RFC822.HEADER FLAGS)')
            raw = msg_data[0][1]
            flags = str(msg_data[0][0])
            parsed = _parse_message_headers(raw)
            parsed['uid']    = uid.decode()
            parsed['unread'] = '\\Seen' not in flags
            messages.append(parsed)

        imap.logout()
        return messages
    except Exception as e:
        print(f"⚠️ [MAIL IMAP] Erreur liste messages ({folder}): {e}")
        return []

def _fetch_message_full(uid, folder='INBOX'):
    """Retourne le contenu complet d'un message par UID."""
    try:
        imap = _imap_connect()
        imap.select(folder, readonly=False)
        # Marquer comme lu
        imap.store(uid.encode(), '+FLAGS', '\\Seen')
        _, msg_data = imap.fetch(uid.encode(), '(RFC822)')
        raw = msg_data[0][1]
        parsed = _parse_message_full(raw)
        parsed['uid'] = uid
        imap.logout()
        return parsed
    except Exception as e:
        print(f"⚠️ [MAIL IMAP] Erreur lecture message {uid}: {e}")
        return None

def _list_folders():
    """Liste les dossiers IMAP disponibles."""
    try:
        imap = _imap_connect()
        _, folders = imap.list()
        imap.logout()
        result = []
        for f in folders:
            parts = f.decode().split('"')
            name = parts[-1].strip() if parts else ''
            if name:
                result.append(name)
        return result
    except Exception as e:
        print(f"⚠️ [MAIL IMAP] Erreur liste dossiers: {e}")
        return ['INBOX', 'Sent', 'Trash', 'Drafts']

# ─── SMTP helpers ─────────────────────────────────────────────────────────────

def _find_sent_folder(imap):
    """Trouve le dossier Envoyés en listant les dossiers IMAP réels."""
    try:
        _, folders = imap.list()
        for f in folders:
            decoded = f.decode('utf-8', errors='replace') if isinstance(f, bytes) else f
            # Extrait le nom du dossier (après le dernier séparateur)
            name = decoded.split('"')[-1].strip().strip('/')
            name_lower = name.lower()
            if any(k in name_lower for k in ['sent', 'envoy', 'gesendete']):
                return name
    except Exception:
        pass
    return 'Sent'  # fallback

def _imap_save_sent(raw_bytes):
    """Sauvegarde une copie dans le dossier Sent IMAP."""
    cfg = _mail_config()
    try:
        imap = imaplib.IMAP4_SSL(cfg['imap_server'], 993)
        imap.login(cfg['username'], cfg['password'])
        folder = _find_sent_folder(imap)
        result = imap.append(folder, '\\Seen', imaplib.Time2Internaldate(datetime.now()), raw_bytes)
        if result[0] != 'OK':
            print(f"⚠️ [MAIL SENT] append retourné: {result} pour dossier '{folder}'")
        imap.logout()
    except Exception as e:
        print(f"⚠️ [MAIL SENT] Impossible de sauvegarder dans Sent: {e}")

def _send_smtp(to_list, subject, body_html, body_text='', attachments=None, reply_to=None):
    """
    Envoie un email via SMTP OVH et sauvegarde dans le dossier Sent IMAP.
    attachments: liste de (filename, bytes_content, mime_type)
    """
    cfg = _mail_config()
    if not cfg['username'] or not cfg['password']:
        raise ValueError("Identifiants SMTP non configurés")

    msg = MIMEMultipart('mixed')
    msg['From']       = formataddr(('HeliaPV', cfg['username']))
    msg['To']         = ', '.join(to_list) if isinstance(to_list, list) else to_list
    msg['Subject']    = subject
    msg['Date']       = formatdate(localtime=True)
    msg['Message-ID'] = make_msgid(domain='heliapv.fr')
    if reply_to:
        msg['Reply-To'] = reply_to

    # Signature HTML
    signature_html = '''
<br><br>
<div style="color:#888;font-size:13px;border-top:1px solid #ddd;padding-top:10px;margin-top:10px">
  <strong>Yann Laurent</strong><br>
  HeliaPV — Solutions photovoltaïques<br>
  📧 info@heliapv.fr &nbsp;|&nbsp; 🌐 www.heliapv.fr
</div>'''

    # Ajoute la signature seulement si pas déjà présente
    if 'info@heliapv.fr' not in body_html:
        body_html = body_html + signature_html

    # Corps alternatif (text + html)
    alt = MIMEMultipart('alternative')
    if body_text:
        alt.attach(MIMEText(body_text, 'plain', 'utf-8'))
    alt.attach(MIMEText(body_html, 'html', 'utf-8'))
    msg.attach(alt)

    # Pièces jointes
    if attachments:
        for filename, content, mime_type in attachments:
            main_type, sub_type = mime_type.split('/') if '/' in mime_type else ('application', 'octet-stream')
            part = MIMEBase(main_type, sub_type)
            part.set_payload(content)
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', 'attachment', filename=filename)
            msg.attach(part)

    recipients = to_list if isinstance(to_list, list) else [to_list]
    raw = msg.as_bytes()
    port = cfg['smtp_port']
    # Port 465 = SSL direct ; port 587/25 = STARTTLS
    if port == 465:
        with smtplib.SMTP_SSL(cfg['smtp_server'], port, timeout=30) as server:
            server.login(cfg['username'], cfg['password'])
            server.sendmail(cfg['username'], recipients, raw)
    else:
        with smtplib.SMTP(cfg['smtp_server'], port, timeout=30) as server:
            server.ehlo()
            server.starttls()
            server.login(cfg['username'], cfg['password'])
            server.sendmail(cfg['username'], recipients, raw)

    # Sauvegarde dans dossier Sent IMAP
    _imap_save_sent(raw)

# ─── Calendrier (JSON) ────────────────────────────────────────────────────────

EVENTS_FILE = os.path.join(os.path.dirname(__file__), 'static', 'data', 'calendar_events.json')

def _load_events():
    os.makedirs(os.path.dirname(EVENTS_FILE), exist_ok=True)
    if not os.path.exists(EVENTS_FILE):
        return []
    try:
        with open(EVENTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []

def _save_events(events):
    os.makedirs(os.path.dirname(EVENTS_FILE), exist_ok=True)
    with open(EVENTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(events, f, ensure_ascii=False, indent=2)

# ─── Routes principales ───────────────────────────────────────────────────────

@mail_bp.route('/')
def mail_index():
    auth = _require_admin()
    if auth:
        return auth
    return render_template('mail_interface.html')

@mail_bp.route('/inbox')
def mail_inbox():
    auth = _require_admin()
    if auth:
        return auth
    return render_template('mail_interface.html', active_folder='INBOX')

# ─── API : Messages ───────────────────────────────────────────────────────────

@mail_bp.route('/api/messages')
def api_messages():
    auth = _require_admin()
    if auth:
        return jsonify({'error': 'Non authentifié'}), 401

    folder = request.args.get('folder', 'INBOX')
    limit  = min(int(request.args.get('limit', 50)), 200)
    search = request.args.get('search', '')

    if search:
        imap_search = f'(OR SUBJECT "{search}" FROM "{search}")'
    else:
        imap_search = 'ALL'

    messages = _fetch_messages(folder=folder, limit=limit, search=imap_search)
    return jsonify({'messages': messages, 'folder': folder, 'count': len(messages)})

@mail_bp.route('/api/message/<uid>')
def api_message(uid):
    auth = _require_admin()
    if auth:
        return jsonify({'error': 'Non authentifié'}), 401

    folder = request.args.get('folder', 'INBOX')
    msg = _fetch_message_full(uid, folder=folder)
    if not msg:
        return jsonify({'error': 'Message introuvable'}), 404
    return jsonify(msg)

@mail_bp.route('/api/message/<uid>', methods=['DELETE'])
def api_delete_message(uid):
    auth = _require_admin()
    if auth:
        return jsonify({'error': 'Non authentifié'}), 401

    folder = request.args.get('folder', 'INBOX')
    try:
        imap = _imap_connect()
        imap.select(folder)
        imap.store(uid.encode(), '+FLAGS', '\\Deleted')
        imap.expunge()
        imap.logout()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@mail_bp.route('/api/folders')
def api_folders():
    auth = _require_admin()
    if auth:
        return jsonify({'error': 'Non authentifié'}), 401
    return jsonify({'folders': _list_folders()})

# ─── API : Envoi ──────────────────────────────────────────────────────────────

@mail_bp.route('/api/send', methods=['POST'])
def api_send():
    auth = _require_admin()
    if auth:
        return jsonify({'error': 'Non authentifié'}), 401

    # Supporte multipart/form-data (avec pièces jointes) et JSON
    if request.content_type and 'multipart' in request.content_type:
        to      = request.form.get('to', '')
        subject = request.form.get('subject', '')
        body    = request.form.get('body', '')
        reply_to = request.form.get('reply_to', '')

        attachments = []
        for f in request.files.getlist('attachments'):
            content = f.read()
            mime = f.content_type or 'application/octet-stream'
            attachments.append((f.filename, content, mime))
    else:
        data    = request.get_json(force=True) or {}
        to      = data.get('to', '')
        subject = data.get('subject', '')
        body    = data.get('body', '')
        reply_to = data.get('reply_to', '')
        attachments = []

    if not to or not subject:
        return jsonify({'error': 'Destinataire et objet requis'}), 400

    try:
        to_list = [t.strip() for t in to.split(',') if t.strip()]
        _send_smtp(to_list, subject, body, attachments=attachments or None, reply_to=reply_to or None)
        return jsonify({'success': True, 'message': f'Email envoyé à {to}'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ─── API : Envoi de proposition CRM ───────────────────────────────────────────

@mail_bp.route('/api/send-proposal', methods=['POST'])
def api_send_proposal():
    auth = _require_admin()
    if auth:
        return jsonify({'error': 'Non authentifié'}), 401

    data = request.get_json(force=True) if request.is_json else dict(request.form)

    to          = data.get('to', '') if isinstance(data.get('to'), str) else data.get('to', [''])[0]
    prospect_name = data.get('prospect_name', 'Prospect') if isinstance(data.get('prospect_name'), str) else data.get('prospect_name', ['Prospect'])[0]
    subject     = data.get('subject', f'Proposition solaire HeliaPV — {prospect_name}')
    body        = data.get('body', '')

    if not to:
        return jsonify({'error': 'Email destinataire requis'}), 400

    # Corps par défaut si vide
    if not body:
        body = f"""<p>Bonjour,</p>
<p>Veuillez trouver ci-joint notre proposition commerciale pour votre projet photovoltaïque.</p>
<p>Notre équipe reste à votre disposition pour tout renseignement complémentaire.</p>
<br>
<p>Cordialement,<br>
<strong>HeliaPV</strong><br>
contact@heliapv.fr</p>"""

    attachments = []

    # Pièce jointe PDF depuis l'upload ou depuis un fichier existant
    pdf_file = request.files.get('pdf') if request.files else None
    if pdf_file:
        attachments.append((pdf_file.filename, pdf_file.read(), 'application/pdf'))
    else:
        # Chercher la proposition déjà générée (génération dynamique)
        pdf_path = data.get('pdf_path', '') if isinstance(data.get('pdf_path'), str) else ''
        if pdf_path and os.path.exists(pdf_path):
            with open(pdf_path, 'rb') as f:
                fname = os.path.basename(pdf_path)
                attachments.append((fname, f.read(), 'application/pdf'))

    try:
        _send_smtp([to], subject, body, attachments=attachments or None)
        return jsonify({'success': True, 'message': f'Proposition envoyée à {to}'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ─── API : Prospects (pour autocomplétion envoi) ──────────────────────────────

@mail_bp.route('/api/prospects')
def api_prospects():
    auth = _require_admin()
    if auth:
        return jsonify({'error': 'Non authentifié'}), 401

    try:
        from database_adapter import execute_query
        results = execute_query(
            "SELECT id, data_json FROM agriweb_prospects ORDER BY id DESC LIMIT 200",
            fetch_all=True
        )
        prospects = []
        for row in (results or []):
            try:
                d = json.loads(row.get('data_json') or '{}')
                email_addr = d.get('email') or d.get('contact_email') or d.get('email_contact', '')
                nom = d.get('nom') or d.get('name') or d.get('raison_sociale') or d.get('commune', '')
                if email_addr:
                    prospects.append({
                        'id':    row.get('id'),
                        'nom':   nom,
                        'email': email_addr,
                    })
            except Exception:
                continue
        return jsonify({'prospects': prospects})
    except Exception as e:
        return jsonify({'error': str(e), 'prospects': []}), 200

# ─── API : Calendrier ─────────────────────────────────────────────────────────

@mail_bp.route('/api/events', methods=['GET'])
def api_events_list():
    auth = _require_admin()
    if auth:
        return jsonify({'error': 'Non authentifié'}), 401
    events = _load_events()
    return jsonify(events)

@mail_bp.route('/api/events', methods=['POST'])
def api_events_create():
    auth = _require_admin()
    if auth:
        return jsonify({'error': 'Non authentifié'}), 401

    data = request.get_json(force=True) or {}
    event = {
        'id':    str(uuid.uuid4()),
        'title': data.get('title', '(Sans titre)'),
        'start': data.get('start', ''),
        'end':   data.get('end', ''),
        'color': data.get('color', '#3b82f6'),
        'description': data.get('description', ''),
        'created_at': datetime.now().isoformat(),
    }
    events = _load_events()
    events.append(event)
    _save_events(events)
    return jsonify(event), 201

@mail_bp.route('/api/events/<event_id>', methods=['PUT'])
def api_events_update(event_id):
    auth = _require_admin()
    if auth:
        return jsonify({'error': 'Non authentifié'}), 401

    data   = request.get_json(force=True) or {}
    events = _load_events()
    for ev in events:
        if ev.get('id') == event_id:
            ev.update({k: v for k, v in data.items() if k != 'id'})
            _save_events(events)
            return jsonify(ev)
    return jsonify({'error': 'Événement introuvable'}), 404

@mail_bp.route('/api/events/<event_id>', methods=['DELETE'])
def api_events_delete(event_id):
    auth = _require_admin()
    if auth:
        return jsonify({'error': 'Non authentifié'}), 401

    events = _load_events()
    events = [ev for ev in events if ev.get('id') != event_id]
    _save_events(events)
    return jsonify({'success': True})
