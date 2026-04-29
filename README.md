# User Auth API

Django REST Framework asosidagi authentication API. Loyiha telefon OTP, Google Sign-In, JWT refresh/logout va user profile endpointlarini beradi.

## Stack

- Python 3.12
- Django 6
- Django REST Framework
- SimpleJWT
- drf-spectacular
- SQLite development database

## Imkoniyatlar

- Telefon raqam orqali OTP so'rash va tasdiqlash
- Google `id_token` orqali login/register
- JWT access va refresh tokenlar
- Refresh token rotation va blacklist
- Logout orqali refresh tokenni bekor qilish
- Joriy user profile ko'rish va tahrirlash
- Swagger va Redoc API hujjatlari

## O'rnatish

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

`.env.example` faylidan `.env` yarating va qiymatlarni to'ldiring:

```env
SECRET_KEY=change-me-to-a-long-random-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

GOOGLE_CLIENT_SECRET_WEB=
GOOGLE_CLIENT_ID_WEB=
GOOGLE_CLIENT_ID_IOS=
GOOGLE_CLIENT_ID_ANDROID=
```

Migrationlarni qo'llang:

```bash
python manage.py migrate
```

Serverni ishga tushiring:

```bash
python manage.py runserver
```

## API hujjatlari

- Swagger: `http://127.0.0.1:8000/api/docs/`
- Redoc: `http://127.0.0.1:8000/api/redoc/`
- OpenAPI schema: `http://127.0.0.1:8000/api/schema/`

## Auth endpointlar

### OTP so'rash

```http
POST /api/auth/phone/request/
Content-Type: application/json

{
  "phone": "+998901234567"
}
```

### OTP tasdiqlash

```http
POST /api/auth/phone/verify/
Content-Type: application/json

{
  "phone": "+998901234567",
  "code": "1234"
}
```

Javob:

```json
{
  "access": "jwt-access-token",
  "refresh": "jwt-refresh-token",
  "is_new_user": true
}
```

### Google orqali kirish

Client Google Sign-In orqali `id_token` oladi va backendga yuboradi:

```http
POST /api/auth/google/
Content-Type: application/json

{
  "id_token": "google-id-token"
}
```

Backend token signature, `aud`, `iss`, `exp` va `email_verified` qiymatlarini tekshiradi. User mavjud bo'lmasa, Google email, first name va last name orqali yangi user yaratiladi.

### Access token yangilash

```http
POST /api/auth/token/refresh/
Content-Type: application/json

{
  "refresh": "jwt-refresh-token"
}
```

`ROTATE_REFRESH_TOKENS=True` bo'lgani uchun javobda yangi access va yangi refresh token keladi. Eski refresh token blacklist qilinadi.

### Logout

```http
POST /api/auth/logout/
Authorization: Bearer <access-token>
Content-Type: application/json

{
  "refresh": "jwt-refresh-token"
}
```

Logout refresh tokenni SimpleJWT blacklist ro'yxatiga qo'shadi. Access token muddati tugaguncha ishlashi mumkin, shuning uchun productionda access token muddatini qisqa qilish tavsiya etiladi.

## Profile endpoint

```http
GET /api/users/profile/
Authorization: Bearer <access-token>
```

```http
PATCH /api/users/profile/
Authorization: Bearer <access-token>
Content-Type: application/json

{
  "first_name": "Ali",
  "last_name": "Valiyev",
  "country": "UZ"
}
```

## Muhim sozlamalar

`config/settings.py` quyidagi qiymatlarni `.env`dan o'qiydi:

- `SECRET_KEY`
- `DEBUG`
- `ALLOWED_HOSTS`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- `GOOGLE_CLIENT_ID_WEB`
- `GOOGLE_CLIENT_ID_IOS`
- `GOOGLE_CLIENT_ID_ANDROID`

Production uchun tavsiyalar:

- `DEBUG=False`
- `ALLOWED_HOSTS` faqat real domain/IPlar bo'lsin
- `SECRET_KEY` uzun va random bo'lsin
- HTTPS va secure cookie sozlamalarini yoqing
- Access token muddatini 5-15 daqiqaga tushiring

## Testlar

```bash
python manage.py test
```

Schema validatsiya:

```bash
python manage.py spectacular --fail-on-warn --validate
```
