# self-hosted-usage-data-exporter

A handy script allowing usage data export from Spacelift self hosted instances.
Simply fill placeholders and run the script to export data directly to Spacelift.

## Requirements

```bash
pip install -r requirements.txt
```

Example usage

```bash
./export.py --base-url <SELFHOSTED_SPACELIFT_URL> --api-key-id <EXPORT_API_KEY_ID> --api-key-secret <EXPORT_API_KEY_SECRET> --start-date <YYYY-MM-DD> --end-date <YYYY-MM-DD> --skip-tls-verification --batch-size 7 --send-to-spacelift
```

For more details run

```bash
./export.py
```
