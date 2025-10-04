# API Key Config Flow Diagram

## Request Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client Request                          │
│                                                                 │
│  POST /token                                                    │
│  {                                                              │
│    "username": "user1",                                         │
│    "password": "password123",                                   │
│    "api_key": "key123",           ← Optional                   │
│    "api_key_config": {...}        ← Optional (NEW)             │
│  }                                                              │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    app.py - /token endpoint                     │
│                                                                 │
│  1. Validate username/password                                  │
│  2. Authenticate user                                           │
│  3. Extract api_key and api_key_config from request            │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│           utils/api_key.py - get_additional_claims()            │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Decision: Which config to use?                           │  │
│  │                                                           │  │
│  │  IF api_key_config provided:                             │  │
│  │    ├─► Use inline config (PRIORITY)                      │  │
│  │    └─► key_data = api_key_config                         │  │
│  │                                                           │  │
│  │  ELSE IF api_key provided:                               │  │
│  │    ├─► Load from file: config/api_keys/{api_key}.yaml   │  │
│  │    └─► key_data = yaml.safe_load(file)                   │  │
│  │                                                           │  │
│  │  ELSE:                                                    │  │
│  │    ├─► Load base config                                  │  │
│  │    └─► key_data = base_api_key.yaml                      │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  4. Extract static claims from key_data                         │
│  5. Process dynamic claims (if any)                             │
│  6. Merge static + dynamic claims                               │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    app.py - Token Generation                    │
│                                                                 │
│  1. Merge user_data + api_key_claims                            │
│  2. Handle exp_hours if present                                 │
│  3. Generate JWT tokens:                                        │
│     - access_token (with all claims)                            │
│     - refresh_token                                             │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                         Response                                │
│                                                                 │
│  {                                                              │
│    "access_token": "eyJ0eXAi...",                              │
│    "refresh_token": "eyJ0eXAi..."                              │
│  }                                                              │
└─────────────────────────────────────────────────────────────────┘
```

## Priority Logic

```
┌─────────────────────────────────────────────────────────────────┐
│                      Configuration Priority                     │
└─────────────────────────────────────────────────────────────────┘

Priority 1 (HIGHEST):  api_key_config (inline JSON payload)
         │
         ├─► Provided in request body
         ├─► No file lookup needed
         └─► Takes precedence over everything

Priority 2:            api_key (file reference)
         │
         ├─► Looks up: config/api_keys/{api_key}.yaml
         ├─► Falls back to base if not found
         └─► Traditional method

Priority 3 (LOWEST):   base_api_key.yaml
         │
         ├─► Default configuration
         ├─► Used when nothing else provided
         └─► Fallback option
```

## Use Case Scenarios

### Scenario 1: Control Tower Integration

```
┌──────────────────┐
│  Control Tower   │
│   (Port 8000)    │
└────────┬─────────┘
         │ GET /manifests/project-id
         │
         ▼
┌──────────────────────────────────────────────────────────┐
│  Manifest JSON                                           │
│  {                                                       │
│    "modules": [                                          │
│      {                                                   │
│        "type": "jwt_config",                            │
│        "config": {                                       │
│          "id": "project-jwt",                           │
│          "claims": { ... }                              │
│        }                                                 │
│      }                                                   │
│    ]                                                     │
│  }                                                       │
└────────┬─────────────────────────────────────────────────┘
         │ Extract jwt_config
         │
         ▼
┌──────────────────┐
│   JWT Service    │
│   (Port 5000)    │
│                  │
│  POST /token     │
│  {               │
│    "username",   │
│    "password",   │
│    "api_key_     │
│     config": ... │
│  }               │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│   JWT Token      │
│   (with claims)  │
└──────────────────┘
```

### Scenario 2: Multi-Tenant Application

```
┌─────────────────────────────────────────────────────────────┐
│  Application Logic                                          │
│                                                             │
│  for tenant in tenants:                                     │
│      config = generate_tenant_config(tenant)                │
│      token = get_jwt_token(user, pass, config)             │
│      store_token(tenant, token)                             │
└─────────────────────────────────────────────────────────────┘
         │
         │ Multiple requests with different configs
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│  JWT Service                                                │
│                                                             │
│  Request 1: Tenant A config → Token A (tier: enterprise)   │
│  Request 2: Tenant B config → Token B (tier: standard)     │
│  Request 3: Tenant C config → Token C (tier: premium)      │
└─────────────────────────────────────────────────────────────┘
```

### Scenario 3: Dynamic Configuration

```
┌─────────────────────────────────────────────────────────────┐
│  Runtime Decision Logic                                     │
│                                                             │
│  user_tier = get_user_tier(user_id)                        │
│  allowed_models = get_allowed_models(user_tier)            │
│  rate_limit = calculate_rate_limit(user_tier, usage)       │
│                                                             │
│  config = {                                                 │
│    "claims": {                                              │
│      "static": {                                            │
│        "tier": user_tier,                                   │
│        "models": allowed_models,                            │
│        "rate_limit": rate_limit                             │
│      }                                                       │
│    }                                                         │
│  }                                                           │
│                                                             │
│  token = get_jwt_token(username, password, config)         │
└─────────────────────────────────────────────────────────────┘
```

## Configuration Structure

```
api_key_config
│
├── id (string)                    - Identifier for this config
│
├── owner (string)                 - Owner/team name
│
├── claims (object)
│   │
│   ├── static (object)            - Claims directly in JWT
│   │   ├── key                    - Consumer key for gateway
│   │   ├── tier                   - Service tier
│   │   ├── models                 - Allowed models array
│   │   ├── rate_limit             - Rate limit value
│   │   ├── exp_hours              - Token expiration hours
│   │   └── [custom claims]        - Any additional claims
│   │
│   └── dynamic (object)           - Runtime computed claims
│       ├── claim_name
│       │   ├── type: "function"
│       │   ├── module: "path.to.module"
│       │   ├── function: "function_name"
│       │   └── args: {...}
│       │
│       └── another_claim
│           ├── type: "api"
│           ├── url: "http://..."
│           ├── method: "GET"
│           └── response_field: "data.field"
│
└── metadata (object)              - NOT in JWT, for functions
    ├── description
    ├── version
    └── [custom metadata]
```

## Integration Points

```
┌─────────────────────────────────────────────────────────────────┐
│                     DSP AI Ecosystem                            │
│                                                                 │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐ │
│  │   Control    │      │     JWT      │      │  Front Door  │ │
│  │    Tower     │─────▶│   Service    │─────▶│   (APISIX)   │ │
│  │  (Manifests) │      │  (Tokens)    │      │  (Gateway)   │ │
│  └──────────────┘      └──────────────┘      └──────────────┘ │
│         │                      │                      │         │
│         │                      │                      │         │
│         ▼                      ▼                      ▼         │
│  Store configs          Generate tokens        Route requests  │
│  Validate deps          Apply claims           Enforce policies│
│  Manage versions        Handle auth            Load balance    │
└─────────────────────────────────────────────────────────────────┘

Flow:
1. Control Tower stores project manifests with JWT configs
2. Client fetches manifest and extracts JWT config
3. Client requests token with inline config
4. JWT Service generates token with claims
5. Client uses token to access services via Front Door
6. Front Door validates token and routes to backend
```

## Benefits Summary

```
┌─────────────────────────────────────────────────────────────────┐
│                         BENEFITS                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ✅ No File Management                                          │
│     └─► No need to create/update YAML files                    │
│                                                                 │
│  ✅ Dynamic Configuration                                       │
│     └─► Generate configs at runtime based on conditions        │
│                                                                 │
│  ✅ Control Tower Integration                                   │
│     └─► Use manifest configs directly                          │
│                                                                 │
│  ✅ Multi-Tenant Support                                        │
│     └─► Different configs per tenant without file overhead     │
│                                                                 │
│  ✅ Testing & Development                                       │
│     └─► Rapid experimentation with different configs           │
│                                                                 │
│  ✅ Backward Compatible                                         │
│     └─► Existing file-based method still works                 │
│                                                                 │
│  ✅ Secure                                                      │
│     └─► Authentication still required, same validation         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```
