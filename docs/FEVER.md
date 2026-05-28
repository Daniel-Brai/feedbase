# Fever API

This document describes the Fever API implementation provided by Feedbase.

Feedbase exposes `/fever` as a Fever-compatible endpoint for syncing feeds, folders, articles, and basic read/star state with Fever clients.

Feedbase implements Fever API version `3`.

## Endpoint

- `POST /fever`
- Content type: `application/x-www-form-urlencoded`
- Response: `application/json`

> Note: Feedbase currently serves Fever responses in JSON only. XML responses are not supported.

## Authentication

Feedbase authenticates Fever requests using the `api_key` form field.

- `api_key` must be provided in the POST body.
- If the API key is missing or invalid, Feedbase returns `auth: 0`.
- If the API key is valid, Feedbase returns `auth: 1`.

### Fever API keys

The Fever API key is generated as the MD5 checksum of the user's email address and password joined by a colon:

```php
$email  = 'you@yourdomain.com';
$pass   = 'b3stp4s4wd3v4';
$api_key = md5($email.':'.$pass);
```

Feedbase stores this value on the user record as `fever_key`.

## Fever login action

Feedbase also supports the undocumented Fever login flow via `action=login`.

- Request: `POST /fever?action=login`
- Form fields:
  - `username`: the user's email address
  - `password`: the user's plain password

If login succeeds, Feedbase returns `auth: 1` and sets a cookie named `fever_auth` equal to the user's API key.

If login fails, Feedbase returns `auth: 0`.

## Request format

Fever requests are sent as a POST to `/fever` with query parameters indicating the requested data and form fields in the body.

Example request:

```http
POST /fever?api=true&items=true&unread_item_ids=true&saved_item_ids=true HTTP/1.1
Content-Type: application/x-www-form-urlencoded

api_key=<user-fever-key>
```

### Supported query parameters

- `api`: boolean
  - A no-op flag used to identify Fever requests.
  - Feedbase accepts `api=true` and requires at least one Fever action flag in the query but does not require `api=true` specifically as `?api` is widely used by Fever clients.

- `action`: `login`
  - Undocumented Fever login action.
  - Requires `username` and `password` in form data.

- `feeds`: boolean
  - Request a list of subscribed feeds.

- `groups`: boolean
  - Request a list of user folders.

- `feeds_groups`: boolean
  - Request feed-to-folder membership mapping.

- `items`: boolean
  - Request a page of article items.

- `links`: boolean
  - Accepted by the schema for compatibility, but Feedbase does not currently populate `links` in the response.

- `unread_item_ids`: boolean
  - Request a comma-separated list of unread article IDs.

- `saved_item_ids`: boolean
  - Request a comma-separated list of saved/starred article IDs.

- `since_id`: integer
  - Forward pagination: return articles with ID greater than this value.

- `max_id`: integer
  - Backward pagination: return articles with ID less than this value.

- `with_ids`: string
  - Comma-separated list of article IDs to fetch.

- `mark`: `item` | `feed` | `group`
  - Mark operation target type.

- `as`: `read` | `unread` | `saved` | `unsaved`
  - Target state for the mark operation.

- `id`: integer
  - ID of the item, feed, or group to mark.

- `before`: integer
  - Unix timestamp used when marking a feed or group as read.

## Request validation

Feedbase requires at least one Fever action flag to be present in the query. Valid Fever actions include:

- `api`
- `feeds`
- `groups`
- `feeds_groups`
- `items`
- `links`
- `unread_item_ids`
- `saved_item_ids`
- mark requests (`mark`, `as`, `id`)
- `action=login`

If none of these is present, validation fails.

For mark requests, Feedbase requires:

- `as` when `mark` is present
- `id` when `mark` is present

## Response structure

Feedbase returns a JSON object containing only the requested Fever fields.

Common response fields:

- `api_version`: `3`
- `auth`: `1` for authenticated requests, `0` otherwise
- `last_refreshed_on_time`: Unix timestamp of the most recently refreshed subscribed feed
- `feeds`: array of feeds
- `feeds_groups`: feed-to-folder membership mapping
- `groups`: array of user folders
- `items`: array of articles
- `total_items`: number of returned items
- `unread_item_ids`: comma-separated unread IDs
- `saved_item_ids`: comma-separated saved IDs

### Fever response models

#### Feed object

Each feed returned by Feedbase contains:

- `id`: feed ID
- `favicon_id`: feed ID reused as favicon ID
- `title`: feed title
- `url`: feed RSS URL
- `site_url`: site URL for the feed
- `is_spark`: `1` when the feed is a Fever spark feed, otherwise `0`
- `last_updated_on_time`: feed update timestamp

#### Group object

Each group returned by Feedbase contains:

- `id`: folder ID
- `title`: folder name

Feedbase also adds an `Uncategorised` group with `id: 0` when `groups=true`.

#### Feed group membership object

Each `feeds_group` object contains:

- `group_id`: folder ID
- `feed_ids`: comma-separated list of feed IDs in that folder

Group `0` represents uncategorized feeds.

#### Item object

Each item returned by Fever contains:

- `id`: article ID
- `feed_id`: feed ID
- `title`: article title
- `author`: article author
- `html`: article HTML content or summary
- `url`: article URL
- `is_saved`: `1` if saved/starred, otherwise `0`
- `is_read`: `1` if read, otherwise `0`
- `created_on_time`: Unix timestamp when the article was published or created

## Supported Fever operations

### Groups: `groups=true`

Requesting `groups` returns:

- `groups`: list of user folders plus an `Uncategorised` folder
- `feeds_groups`: feed-to-folder membership mapping

### Feeds: `feeds=true`

Requesting `feeds` returns:

- `feeds`: list of subscribed feeds
- `feeds_groups`: feed-to-folder membership mapping

### Items: `items=true`

Requesting `items` returns:

- `items`: list of articles
- `total_items`: number of returned articles

Filtering options for `items`:

- `since_id` for items newer than a known article ID
- `max_id` for items older than a known article ID
- `with_ids` for explicit item ID lists

### Unread and saved IDs

`unread_item_ids=true` returns:

- `unread_item_ids`: comma-separated unread article IDs

`saved_item_ids=true` returns:

- `saved_item_ids`: comma-separated saved article IDs

### Marking items

To update a single item, use:

- `mark=item`
- `as=read|unread|saved|unsaved`
- `id=<item id>`

### Marking feeds and groups as read

To mark a feed as read:

- `mark=feed`
- `as=read`
- `id=<feed id>`
- `before=<timestamp>`

To mark a folder as read:

- `mark=group`
- `as=read`
- `id=<group id>`
- `before=<timestamp>`

To mark uncategorized items as read:

- `mark=group`
- `as=read`
- `id=0`
- `before=<timestamp>`

To mark sparks as read:

- `mark=group`
- `as=read`
- `id=-1`
- `before=<timestamp>`

> Note: Feedbase currently applies feed/group mark requests only as read operations.

## Undocumented login support

Feedbase supports the Fever login extension used by some Fever clients.

Request:

```http
POST /fever?action=login HTTP/1.1
Content-Type: application/x-www-form-urlencoded

username=<email>&password=<password>
```

Response:

- `auth`: `1` when login succeeds, otherwise `0`
- `fever_auth` cookie set to the API key when successful

## Limitations and notes

- Feedbase currently returns JSON only; XML is not supported.
- `links` is recognized in queries but not populated in responses.
- `favicons` is not supported by Feedbase.
- `api_key` authentication uses the MD5 hash of `email:password`.
- `feeds_groups` is returned for both feed and group requests when available.
- `is_spark` is exposed on feeds and may be `0` or `1`.
- Only the supported Fever operations listed above are implemented.

## Examples

Request items and status IDs:

```http
POST /fever?api=true&items=true&unread_item_ids=true&saved_item_ids=true HTTP/1.1
Content-Type: application/x-www-form-urlencoded

api_key=<user-fever-key>
```

Example response:

```json
{
  "api_version": 3,
  "auth": 1,
  "items": [
    {
      "id": 101,
      "feed_id": 20,
      "title": "Example article",
      "author": "Jane Doe",
      "html": "<p>Article content</p>",
      "url": "https://example.org/article/101",
      "is_saved": 0,
      "is_read": 1,
      "created_on_time": 1710000000
    }
  ],
  "total_items": 1,
  "unread_item_ids": "101",
  "saved_item_ids": ""
}
```

Login example:

```http
POST /fever?action=login HTTP/1.1
Content-Type: application/x-www-form-urlencoded

username=you@yourdomain.com&password=b3stp4s4wd3v4
```

Successful login returns `auth: 1` and sets `fever_auth` cookie to the API key.

## Glossary

- `Fever key`: the API key stored on the user record used to authenticate Fever clients.
- `group_id: 0`: uncategorized feeds.
- `group_id: -1`: Sparks group when marking read.
- `is_saved`: saved or starred article status.
- `is_read`: read/unread article status.
