# SimpleForum

Flask forum app with MySQL, Redis, and Nginx.

## Local Setup

1. **Create `.env` file:**
```bash
MYSQL_DATABASE=flaskdb
MYSQL_USER=flask_user
MYSQL_USER_PASSWORD=your_password
MYSQL_ROOT_PASSWORD=root_password
FLASK_SECRET_KEY=your_secret_key
```

2. **Start services:**
```bash
docker-compose up -d
docker exec -it flask_app flask db-init
```

3. **Access:** http://localhost

## Common Commands

```bash
# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild after changes
docker-compose up -d --build

# Database backup
docker exec mysql_db mysqldump -u root -p flaskdb > backup.sql

# Database restore
docker exec -i mysql_db mysql -u root -p flaskdb < backup.sql
```

## Production Deployment

### Prerequisites
- Server with Docker & Docker Compose
- Domain pointing to your server IP

### Step 1: Initial Setup (HTTP only)

1. **Configure environment:**
```bash
# Create .env with strong passwords
nano .env
```

2. **Configure Nginx for HTTP (first.conf):**
```bash
# Edit first.conf with your domain
nano nginx/conf.d/first.conf
# Replace {your domain here} with your actual domain (e.g., example.com)

# Rename default.conf temporarily (we'll use it after SSL)
mv nginx/conf.d/default.conf nginx/conf.d/default.conf.disabled
```

3. **Start services:**
```bash
docker compose up -d --build
```

Your app is now running on **http://yourdomain.com** (no SSL yet).

### Step 2: Get SSL Certificate

Once the app is running with `first.conf`, obtain SSL certificate:

```bash
docker compose run --rm certbot certonly --webroot \
    --webroot-path=/var/www/certbot \
    --email your@email.com \
    --agree-tos \
    -d yourdomain.com
```

### Step 3: Switch to HTTPS (default.conf)

After getting the certificate, switch to the HTTPS configuration:

```bash
# Disable first.conf
mv nginx/conf.d/first.conf nginx/conf.d/first.conf.disabled

# Enable default.conf with SSL
mv nginx/conf.d/default.conf.disabled nginx/conf.d/default.conf

# Edit default.conf with your domain
nano nginx/conf.d/default.conf
# Replace both instances of {your domain here} with your actual domain

# Restart Nginx to apply SSL configuration
docker compose restart nginx
```

Your app is now running on **https://yourdomain.com** with automatic HTTP→HTTPS redirect!

---

## CI/CD - Automated Docker Builds

### Quick Start (Use it Right Now)

1. **Create GitHub repository** (if you haven't):
```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/yourusername/your-repo.git
git push -u origin main
```

2. **Create Docker Hub account**: https://hub.docker.com

3. **Get Docker Hub access token**:
   - Go to Docker Hub → Account Settings → Security → New Access Token
   - Name it "GitHub Actions" and copy the token

4. **Add secrets to GitHub**:
   - Go to your repo → Settings → Secrets and variables → Actions → New repository secret
   - Add `DOCKER_USERNAME` = your Docker Hub username
   - Add `DOCKER_PASSWORD` = the access token you copied

5. **Push to trigger build**:
```bash
git add .
git commit -m "Setup CI/CD"
git push
```

6. **Watch it build**:
   - Go to your GitHub repo → Actions tab
   - You'll see the workflow running
   - After ~5 minutes, your image will be on Docker Hub!

### Using Your CI/CD Images

Once built, update `docker-compose.yml`:

```yaml
services:
  app:
    image: yourusername/flask-forum:latest  # Replace 'build: .'
    container_name: flask_app
    # ... rest stays the same
```

Deploy anywhere:
```bash
docker-compose pull  # Downloads your latest image
docker-compose up -d
```

### Release New Versions

```bash
# Make changes to your code, then:
git add .
git commit -m "Fixed bug"
git push  # Automatically builds and pushes new 'latest' tag

# Or create a version:
git tag v1.0.0
git push origin v1.0.0  # Builds and pushes v1.0.0 + latest
```

