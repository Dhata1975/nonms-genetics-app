# Cloudflare note

If you want a branded URL like genetics.nonms.com:

1. Host the Streamlit app on a VM/container or supported platform.
2. Put Cloudflare in front of it.
3. Route a subdomain to the app origin.
4. Optionally use Cloudflare Tunnel if the app is running on a private machine/server.
