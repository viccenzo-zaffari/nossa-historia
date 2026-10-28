"""
Script de lembrete de aniversário — Nossa História
Roda diariamente via GitHub Actions.

Envia e-mail via Resend para casais cujo aniversário de relacionamento
cai nos próximos 3 dias (e no próprio dia).

Dependências: pip install psycopg2-binary resend python-dotenv
Variáveis de ambiente: DATABASE_URL, RESEND_API_KEY, APP_URL
"""

import os
import sys
from datetime import date, timedelta

import psycopg2
import resend

# ── CONFIG ──
DATABASE_URL = os.environ["DATABASE_URL"]
RESEND_API_KEY = os.environ["RESEND_API_KEY"]
APP_URL = os.environ.get("APP_URL", "https://nossahistoria.com")
FROM_EMAIL = "Nossa História <noreply@nossahistoria.com>"

resend.api_key = RESEND_API_KEY


def get_upcoming_anniversaries(days_ahead: int = 3) -> list[dict]:
    """
    Retorna álbuns cujo aniversário de relacionamento cai
    nos próximos `days_ahead` dias (inclusive hoje).
    """
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    today = date.today()
    upcoming = []

    for delta in range(0, days_ahead + 1):
        target = today + timedelta(days=delta)
        # Compara mês e dia (ignora o ano)
        cur.execute(
            """
            SELECT id, name1, name2, owner_email, start_date, slug
            FROM albums
            WHERE is_active = TRUE
              AND start_date IS NOT NULL
              AND EXTRACT(MONTH FROM start_date) = %s
              AND EXTRACT(DAY FROM start_date) = %s
            """,
            (target.month, target.day),
        )
        rows = cur.fetchall()
        for row in rows:
            album_id, name1, name2, email, start_date, slug = row
            years = today.year - start_date.year
            if delta == 0 and today.month == target.month and today.day == target.day:
                # Já passou o aniversário esse ano?
                anos_completos = years if (today >= date(today.year, start_date.month, start_date.day)) else years - 1
            else:
                anos_completos = today.year - start_date.year
            upcoming.append({
                "album_id": str(album_id),
                "name1": name1,
                "name2": name2,
                "email": email,
                "start_date": start_date,
                "slug": slug or "",
                "days_until": delta,
                "years": anos_completos,
            })

    cur.close()
    conn.close()
    return upcoming


def build_email_today(album: dict) -> dict:
    """E-mail para o dia do aniversário."""
    name1 = album["name1"]
    name2 = album["name2"]
    years = album["years"]
    album_url = f"{APP_URL}/nossa_historia_album.html?slug={album['slug']}" if album["slug"] else APP_URL

    subject = f"🎉 Hoje é o aniversário de {name1} & {name2}! ♥ {years} anos juntos"

    html = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head><meta charset="UTF-8">
<style>
  body {{ font-family: 'Georgia', serif; background: #f7f4f1; margin: 0; padding: 0; }}
  .wrap {{ max-width: 560px; margin: 0 auto; background: white; border-radius: 16px; overflow: hidden; }}
  .header {{ background: linear-gradient(135deg, #b5604a, #c9a96e); padding: 48px 32px; text-align: center; color: white; }}
  .header h1 {{ font-size: 28px; margin: 0 0 8px; }}
  .header p {{ font-size: 16px; margin: 0; opacity: 0.9; }}
  .body {{ padding: 40px 32px; color: #3d2f28; line-height: 1.7; }}
  .years-badge {{ background: #f2e4de; color: #b5604a; border-radius: 100px; padding: 12px 24px; font-size: 22px; font-weight: bold; display: inline-block; margin: 16px 0; }}
  .cta {{ display: block; background: #b5604a; color: white !important; text-decoration: none; border-radius: 100px; padding: 16px 32px; text-align: center; font-size: 16px; margin: 32px 0 16px; }}
  .footer {{ padding: 24px 32px; text-align: center; font-size: 12px; color: #9a857a; border-top: 1px solid #ecddd5; }}
</style>
</head>
<body>
<div class="wrap">
  <div class="header">
    <div style="font-size:48px;margin-bottom:16px">💕</div>
    <h1>Feliz Aniversário!</h1>
    <p>{name1} & {name2}</p>
  </div>
  <div class="body">
    <p>Hoje é um dia muito especial! <strong>{name1} & {name2}</strong> estão completando:</p>
    <div style="text-align:center">
      <div class="years-badge">🎂 {years} {'ano' if years == 1 else 'anos'} juntos</div>
    </div>
    <p>Cada dia ao lado de quem amamos é um presente. Que essa data seja celebrada com muito carinho, amor e cumplicidade.</p>
    <p>Revisitem os momentos que vocês guardam no álbum e relembrem os melhores capítulos da história de vocês. ♥</p>
    <a href="{album_url}" class="cta">Ver nosso álbum ♥</a>
    <p style="font-size:13px;color:#9a857a;text-align:center">Compartilhe esse link com quem você ama.</p>
  </div>
  <div class="footer">
    Nossa História · feito com amor<br>
    <a href="{APP_URL}" style="color:#b5604a">nossahistoria.com</a>
  </div>
</div>
</body>
</html>
"""
    return {"subject": subject, "html": html}


def build_email_upcoming(album: dict) -> dict:
    """E-mail para lembrete (1–3 dias antes)."""
    name1 = album["name1"]
    name2 = album["name2"]
    years = album["years"]
    days = album["days_until"]
    album_url = f"{APP_URL}/nossa_historia_album.html?slug={album['slug']}" if album["slug"] else APP_URL

    days_str = f"em {days} {'dia' if days == 1 else 'dias'}"
    subject = f"💕 Lembrete: aniversário de {name1} & {name2} {days_str}!"

    html = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head><meta charset="UTF-8">
<style>
  body {{ font-family: 'Georgia', serif; background: #f7f4f1; margin: 0; padding: 0; }}
  .wrap {{ max-width: 560px; margin: 0 auto; background: white; border-radius: 16px; overflow: hidden; }}
  .header {{ background: linear-gradient(135deg, #3d2f28, #b5604a); padding: 40px 32px; text-align: center; color: white; }}
  .header h1 {{ font-size: 24px; margin: 0 0 8px; }}
  .header p {{ font-size: 15px; margin: 0; opacity: 0.85; }}
  .body {{ padding: 36px 32px; color: #3d2f28; line-height: 1.7; }}
  .countdown {{ background: #faf3e6; border: 1px solid #e8d8b8; border-radius: 12px; padding: 20px; text-align: center; margin: 20px 0; }}
  .countdown-num {{ font-size: 48px; font-family: 'Playfair Display', serif; color: #c9a96e; font-style: italic; }}
  .cta {{ display: block; background: #b5604a; color: white !important; text-decoration: none; border-radius: 100px; padding: 16px 32px; text-align: center; font-size: 16px; margin: 28px 0 16px; }}
  .footer {{ padding: 24px 32px; text-align: center; font-size: 12px; color: #9a857a; border-top: 1px solid #ecddd5; }}
</style>
</head>
<body>
<div class="wrap">
  <div class="header">
    <div style="font-size:40px;margin-bottom:12px">⏰</div>
    <h1>Lembrete de aniversário</h1>
    <p>{name1} & {name2}</p>
  </div>
  <div class="body">
    <p>Ei! O aniversário de <strong>{name1} & {name2}</strong> está chegando:</p>
    <div class="countdown">
      <div class="countdown-num">{days}</div>
      <div style="font-size:14px;color:#9a857a">{'dia' if days == 1 else 'dias'} para o aniversário ♥</div>
      <div style="font-size:13px;color:#c9a96e;margin-top:4px">{years} {'ano' if years == 1 else 'anos'} juntos</div>
    </div>
    <p>Que tal revisitar o álbum de vocês e relembrar os momentos mais especiais antes da data?</p>
    <a href="{album_url}" class="cta">Visitar nosso álbum ♥</a>
  </div>
  <div class="footer">
    Nossa História · feito com amor<br>
    <a href="{APP_URL}" style="color:#b5604a">nossahistoria.com</a>
  </div>
</div>
</body>
</html>
"""
    return {"subject": subject, "html": html}


def send_reminders():
    albums = get_upcoming_anniversaries(days_ahead=3)
    if not albums:
        print("Nenhum aniversário nos próximos 3 dias.")
        return

    sent = 0
    errors = 0

    for album in albums:
        try:
            if album["days_until"] == 0:
                content = build_email_today(album)
            else:
                content = build_email_upcoming(album)

            resend.Emails.send({
                "from": FROM_EMAIL,
                "to": [album["email"]],
                "subject": content["subject"],
                "html": content["html"],
            })

            print(f"✓ E-mail enviado para {album['email']} ({album['name1']} & {album['name2']}, {album['days_until']} dias)")
            sent += 1

        except Exception as e:
            print(f"✗ Erro ao enviar para {album['email']}: {e}", file=sys.stderr)
            errors += 1

    print(f"\nResumo: {sent} enviados, {errors} erros.")
    if errors > 0:
        sys.exit(1)


if __name__ == "__main__":
    send_reminders()
