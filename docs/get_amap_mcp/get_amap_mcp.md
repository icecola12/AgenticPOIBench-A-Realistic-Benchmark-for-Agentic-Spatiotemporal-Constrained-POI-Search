This project’s map and POI features call the AMap **Web Service API**. You need to obtain a **Key** from the AMap Open Platform and set it in the environment variable **`AMAP_MCP_KEY`**.

For full walkthroughs, screenshots, and console links, see the official documentation:

- [Get a Key (Web Service API)](https://lbs.amap.com/api/webservice/guide/create-project/get-key)

## Use in this repository

In your terminal or deployment environment (example):

```bash
export AMAP_MCP_KEY="your-key-here"
```

This matches the **Set up API keys** section in the README. With keys set, you can run `./AgenticPOIBench verify --resolve-secrets` to validate configuration and secret resolution.
