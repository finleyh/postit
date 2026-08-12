# PostIt

A lightweight image drop/paste service backed by MySQL.

## Features

- Upload any number of images in one post.
- Paste images directly from the clipboard.
- Drag and drop images.
- Generates a UUID for every post and every image.
- Post page: `/posts/<post-uuid>`.
- Direct image URL: `/posts/<post-uuid>/images/<image-uuid>`.
- Copy a direct image URL or Markdown image embed from the post page.
- Images are stored in MySQL as base64 in a MySQL `LONGTEXT` column.
- Posts have no user-facing deletion mechanism.
- No login/account system.

## Run locally

Copy `.env.example` to `.env` if desired, change the passwords, then:

```bash
docker compose up -d --build
```

Open `http://localhost:8080`.

## Deploying

Put the app behind your reverse proxy at:

`https://postit.trashcollector.dev`

No application setting needs to know the hostname; Flask builds absolute URLs from the incoming request.

For production, set strong values for:

- `MYSQL_PASSWORD`
- `MYSQL_ROOT_PASSWORD`

Example:

```bash
MYSQL_PASSWORD='a-long-random-password'
MYSQL_ROOT_PASSWORD='another-long-random-password'
```

## Storage note

The requested base64-in-MySQL approach is implemented. Base64 increases storage requirements by roughly 33% compared with storing the original binary bytes. The application now uses MySQL `LONGTEXT` for the base64 payload, so there is no application-level image-size cap. MySQL's normal storage/table limits still apply.

## Important production considerations

This deliberately has no delete endpoint and no authentication. That means anyone who obtains a post UUID can view the post, and anyone can create posts.

The next hardening steps I would consider before exposing it publicly are:

1. Reverse-proxy request/body limits.
2. Rate limiting.
3. Optional maximum image dimensions.
4. Image decoding/re-encoding to remove dangerous or unexpected image payloads.
5. Monitoring and database backups.
6. Optional administrative-only deletion.
