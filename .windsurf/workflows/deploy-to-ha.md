---
description: Deploy robovac integration to local Home Assistant instance
---

# Deploy to Home Assistant

This workflow deploys the robovac custom component to the local Home Assistant
instance running on Kubernetes.

## Prerequisites

- kubectl configured with `ironstone` context
- Access to `home-automation` namespace

## Steps

// turbo
1. Run tests to verify code is working:

```bash
task test
```

// turbo
2. Create deployment tarball (excludes __pycache__):

```bash
task ha-deploy
```

3. Restart Home Assistant:

```bash
task ha-restart-k8s
```

// turbo
4. Check Home Assistant logs for errors:

```bash
task ha-logs
```

## Verification

After deployment, check:

- No errors in `/config/home-assistant.log` related to robovac
- Vacuum entities are available in Home Assistant
- Integration responds to commands
