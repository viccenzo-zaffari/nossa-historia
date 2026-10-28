# Nossa História API 💕

Backend FastAPI para o projeto Nossa História — álbuns de casal personalizados.

## Stack

- **Backend**: FastAPI + SQLAlchemy + psycopg2
- **Banco**: PostgreSQL (Railway)
- **Pagamentos**: Stripe
- **Fotos**: Cloudinary
- **E-mail**: Resend
- **Deploy**: Railway (backend) + Netlify (frontend)

## Variáveis de Ambiente

```
DATABASE_URL=postgresql://user:pass@host:port/db
SECRET_KEY=sua-chave-secreta
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_BASIC=price_...
STRIPE_PRICE_PREMIUM=price_...
FRONTEND_URL=https://nossahistoria.netlify.app
ADMIN_TOKEN=seu-token-admin-seguro
```

## Rodar localmente

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

## Deploy (Railway)

O Railway faz deploy automático a cada push na branch `main`.

## GitHub Actions — Lembretes de Aniversário

Adicione os secrets no GitHub:
- `DATABASE_URL`
- `RESEND_API_KEY`  
- `APP_URL`

O workflow roda diariamente às 08:00 BRT e envia e-mails para casais com aniversário nos próximos 3 dias.

## Admin Panel

Acesse: `https://seu-site.netlify.app/nossa_historia_admin.html`  
Token: valor de `ADMIN_TOKEN` (padrão de desenvolvimento: `nossahistoria-admin-2026`)
