# Dating App (pet project)
 
Pet project I'm building to improve my backend skills.
Dating app with realtime chat, swipes and matching.
 
## Stack
 
- **FastAPI** — main framework
- **PostgreSQL + PostGIS** — database, postgis for geo-queries (nearby search)
- **Redis** — websocket connection manager, user deck storage, celery task queue
- **Celery** — background tasks
- **S3** — photo storage
 
## What's done
 
- registration and auth
- profile photo upload to s3
- user deck is generated in background via celery based on preferences
- swipes, when mutual like happens — conversation is created automatically
- websocket chat between matched users
- messages are saved to db, if user was offline — they get them on reconnect
- migrations via alembic
 
## What I'm planning to add
 
- [ ] docker + docker-compose
- [ ] match notification via websocket
- [ ] push notifications via firebase when user is offline
- [ ] deploy to vps
 
## Running locally
 
*coming soon*