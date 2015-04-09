import smtplib
import pystache
import os
import html.parser
import threading
from email.mime.text import MIMEText
from werkzeug.utils import secure_filename
from flask import url_for

from KerbalStuff.database import db
from KerbalStuff.objects import User
from KerbalStuff.config import _cfg, _cfgi


def sendEmail(message,emailto):
    smtp = smtplib.SMTP(_cfg("smtp-host"), _cfgi("smtp-port"))
    smtp.starttls()
    smtp.ehlo()
    smtp.login(_cfg("smtp-user"), _cfg("smtp-password"))
    smtp.sendmail("donotreply@planetrimworld.com", [ emailto ], message.as_string())
    smtp.quit()

def send_confirmation(user, followMod=None):
    if _cfg("smtp-host") == "":
        return
    with open("emails/confirm-account") as f:
        if followMod != None:
            message = MIMEText(pystache.render(f.read(), { 'user': user, "domain": _cfg("domain"),\
                    'confirmation': user.confirmation + "?f=" + followMod }))
        else:
            message = MIMEText(html.parser.HTMLParser().unescape(\
                    pystache.render(f.read(), { 'user': user, "domain": _cfg("domain"), 'confirmation': user.confirmation })))
    message['X-MC-Important'] = "true"
    message['X-MC-PreserveRecipients'] = "false"
    message['Subject'] = "Welcome to Planet RimWorld Mods!"
    message['From'] = "donotreply@planetrimworld.com"
    message['To'] = user.email
    sendEmail(message,user.email)

def send_reset(user):
    if _cfg("smtp-host") == "":
        return
    with open("emails/password-reset") as f:
        message = MIMEText(html.parser.HTMLParser().unescape(\
                pystache.render(f.read(), { 'user': user, "domain": _cfg("domain"), 'confirmation': user.passwordReset })))
    message['X-MC-Important'] = "true"
    message['X-MC-PreserveRecipients'] = "false"
    message['Subject'] = "Reset your password on Planet RimWorld Mods"
    message['From'] = "donotreply@planetrimworld.com"
    message['To'] = user.email
    sendEmail(message,user.email)

def send_grant_notice(mod, user):
    if _cfg("smtp-host") == "":
        return
    with open("emails/grant-notice") as f:
        message = MIMEText(html.parser.HTMLParser().unescape(\
                pystache.render(f.read(), { 'user': user, "domain": _cfg("domain"),\
                'mod': mod, 'url': url_for('mods.mod', id=mod.id, mod_name=mod.name) })))
    message['X-MC-Important'] = "true"
    message['X-MC-PreserveRecipients'] = "false"
    message['Subject'] = "You've been asked to co-author a mod on Planet RimWorld Mods"
    message['From'] = "donotreply@planetrimworld.com"
    message['To'] = user.email
    sendEmail(message,user.email)

def send_update_notification(mod, version, user):
    if _cfg("smtp-host") == "":
        return
    t = threading.Thread(target=send_update_notification_sync, args=(mod, version, user.username), kwargs={})
    t.start()

def send_update_notification_sync(mod, version, user):
    followers = [u.email for u in mod.followers]
    changelog = version.changelog
    if changelog:
        changelog = '\n'.join(['    ' + l for l in changelog.split('\n')])

    targets = list()
    for follower in followers:
        targets.append(follower)
    if len(targets) == 0:
        return
    with open("emails/mod-updated") as f:
        message = MIMEText(html.parser.HTMLParser().unescape(pystache.render(f.read(),
            {
                'mod': mod,
                'user': user,
                'domain': _cfg("domain"),
                'latest': version,
                'url': '/mod/' + str(mod.id) + '/' + secure_filename(mod.name)[:64],
                'changelog': changelog
            })))
    message['X-MC-PreserveRecipients'] = "false"
    message['Subject'] = user + " has just updated " + mod.name + "!"
    message['From'] = "donotreply@planetrimworld.com"
    message['To'] = ";".join(targets)
    sendEmail(message,user.email)

def send_autoupdate_notification(mod):
    if _cfg("smtp-host") == "":
        return
    followers = [u.email for u in mod.followers]
    changelog = mod.default_version().changelog
    if changelog:
        changelog = '\n'.join(['    ' + l for l in changelog.split('\n')])

    targets = list()
    for follower in followers:
        targets.append(follower)
    if len(targets) == 0:
        return
    with open("emails/mod-autoupdated") as f:
        message = MIMEText(html.parser.HTMLParser().unescape(pystache.render(f.read(),
            {
                'mod': mod,
                'domain': _cfg("domain"),
                'latest': mod.default_version(),
                'url': '/mod/' + str(mod.id) + '/' + secure_filename(mod.name)[:64],
                'changelog': changelog
            })))
    message['X-MC-PreserveRecipients'] = "false"
    message['Subject'] = mod.name + " is compatible with RimWorld " + mod.versions[0].ksp_version + "!"
    message['From'] = "donotreply@planetrimworld.com"
    message['To'] = ";".join(targets)
    sendEmail(message,targets)

def send_bulk_email(users, subject, body):
    if _cfg("smtp-host") == "":
        return
    targets = list()
    for u in users:
        targets.append(u)
    message = MIMEText(body)
    message['X-MC-PreserveRecipients'] = "false"
    message['Subject'] = subject
    message['From'] = "donotreply@planetrimworld.com"
    message['To'] = ";".join(targets)
    sendEmail(message,targets)
