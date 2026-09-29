## Design Decisions

### Short code generation

How is a code made?
Postgres assigns each link an auto-incrementing ID, and the ID is converted to base62.
Why not hash the URL?
A hash can produce the same code for two different URLs, so you'd need to check for collisions and retry. A counter can never repeat.
Why base62 rather than base64?
Base64 includes + and /, which have special meaning in URLs.
What's the known weakness?
Codes are sequential, so anyone can guess other links.
