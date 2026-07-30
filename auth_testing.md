# Auth Testing Playbook (Emergent Google Auth)

See `/app/memory/test_credentials.md` for the seeded test session token.

## Protected endpoints
- `POST /api/issuer/credential`
- `POST /api/compliance/gdpr/erasure`

## Testing (mongosh)

```bash
mongosh --eval "
use('eudi_nexus');
var uid = 'test-user-' + Date.now();
var tok = 'test_session_' + Date.now();
db.users.insertOne({user_id: uid, email: 't.'+uid+'@e2e.local', name:'Tester', picture:'', created_at: new Date()});
db.user_sessions.insertOne({user_id: uid, session_token: tok, expires_at: new Date(Date.now()+7*24*3600*1000), created_at: new Date()});
print('SESSION_TOKEN: ' + tok);
"
```

## Curl (Bearer)

```bash
API=https://honor-registry-ai.preview.emergentagent.com
curl -H "Authorization: Bearer $TOKEN" $API/api/auth/me
```

## Playwright (cookie)

```python
await context.add_cookies([{
  "name":"session_token","value":TOKEN,
  "domain":"fa61e2da-c1aa-4cff-90fc-a761ac9856ca.preview.emergentagent.com",
  "path":"/","httpOnly":True,"secure":True,"sameSite":"None"
}])
```
