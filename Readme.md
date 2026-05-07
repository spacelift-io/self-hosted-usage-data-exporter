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

### Limiting which tables are exported

By default the export covers the full set of tables. Pass `--tables` with a comma-separated list to restrict the dump — for example to ship only what billing needs:

```bash
./export.py --base-url <SELFHOSTED_SPACELIFT_URL> --api-key-id <EXPORT_API_KEY_ID> --api-key-secret <EXPORT_API_KEY_SECRET> --start-date <YYYY-MM-DD> --end-date <YYYY-MM-DD> --tables logins,heartbeats,daily_worker_usages --send-to-spacelift
```

Account details are always part of the response envelope and do not need to be listed. Unknown table names are rejected by the server, which returns the full list of accepted values in its error.

For more details run

```bash
./export.py
```
