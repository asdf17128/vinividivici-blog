# Yuan Zhan Technical Blog

Static files for `https://blog.vinividivici.top`.

The site is intentionally plain HTML and CSS. There is no build step, no Node runtime, no database, and no background process on the VPS. nginx serves the files from `/var/www/blog`.

## Structure

```text
site/
  index.html
  projects.html
  about.html
  posts/
  assets/styles.css
  rss.xml
  sitemap.xml
  robots.txt
nginx/
  blog.vinividivici.top.conf
scripts/
  deploy-blog.sh
tests/
  validate_static_site.py
```

## Local Preview

```bash
cd blog
python3 -m http.server 8080 -d site
```

Open `http://127.0.0.1:8080`.

## Validate

```bash
python3 blog/tests/validate_static_site.py
```

From inside this directory:

```bash
python3 tests/validate_static_site.py
```

## Deploy To VPS

The default deploy target is `root@192.129.183.208:/var/www/blog/` over SSH port `2221`.

```bash
blog/scripts/deploy-blog.sh
```

Override the target when needed:

```bash
BLOG_REMOTE=root@example.com BLOG_REMOTE_DIR=/var/www/blog/ blog/scripts/deploy-blog.sh
```

Override the SSH port when needed:

```bash
BLOG_SSH_PORT=22 blog/scripts/deploy-blog.sh
```

nginx does not need to restart for content updates. Only reload nginx after changing the config file:

```bash
sudo nginx -t
sudo systemctl reload nginx
```

## nginx

Install the example config from `nginx/blog.vinividivici.top.conf` into the server's nginx sites directory. Keep the `/sub/` location before the generic `/` location so subscription links continue to proxy to `127.0.0.1:8443`.

Do not change DNS away from the relay VPS and do not enable Cloudflare proxy mode for this hostname. The blog uses nginx over TCP 443; the existing relay continues to use UDP 443.

## Publish The Blog Source To GitHub

Use this directory as a separate public repository. Do not publish the parent `sb-server` repository because it contains private operations files.

```bash
cd blog
git init
git add .
git commit -m "Initial static technical blog"
gh repo create asdf17128/vinividivici-blog --public --source=. --remote=origin --push
```

After that, updates are the normal GitHub flow:

```bash
git add .
git commit -m "Update blog"
git push
scripts/deploy-blog.sh
```
