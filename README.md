To run the app

uv run uvicorn app.main:app --reload --port 8000


for validation

Complete Terraform
       ↓
Terraform validation
       ↓
Diagnostics
       ↓
Determine affected units
       ↓
Regenerate affected units
       ↓
Regenerate dependent units if their interface changed
       ↓
Validate complete Terraform again


context regenerator gets

GLOBAL
├── Architecture
└── Cloud provider

CURRENT UNIT
├── database
├── purpose
├── resources
├── inputs
├── outputs
└── files

CURRENT CODE
├── main.tf
├── variables.tf
└── outputs.tf

DEPENDENCY CONTEXT
└── relevant outputs from network/security

DOCS
└── only database Terraform docs

VALIDATION
├── stage
├── diagnostics
└── failing file(s)

User
 ↓
Intent
 ↓
SRS
 ↓
Architecture Agent
 ├── architecture Markdown
 ├── cloud provider
 └── Terraform resource types
 ↓
Project Planner
 └── ordered generation units
 ↓
┌───────────────────────────────┐
│       Generation Loop         │
│                               │
│  Current Unit                 │
│       ↓                       │
│  Retrieve Unit Docs           │
│       ↓                       │
│  Get Dependency Context       │
│       ↓                       │
│  Generate Complete Unit       │
│       ↓                       │
│  More units? ─── yes ─────────┘
└───────────────┬───────────────┘
                │ no
                ↓
        Complete Terraform
                ↓
           Validation
                ↓
        ┌───────┴────────┐
        │                │
      passed           failed
        │                │
        ↓                ↓
       END       Identify affected units
                         ↓
                  Regenerate units
                         ↓
                  Validate again




                PROJECT PLANNER
                      ↓
             Ordered Unit Plan
                      ↓
              ┌──────────────┐
              │   GENERATE   │
              │   ONE UNIT   │
              └──────┬───────┘
                     ↓
               More units?
                /       \
              yes        no
               │          │
               └──→       ↓
                     COMPLETE PROJECT
                           ↓
                       VALIDATE
                           ↓
                     ┌─────┴─────┐
                   PASS         FAIL
                    ↓             ↓
                   END      Identify unit
                                  ↓
                           Regenerate unit
                                  ↓
                        Update generated_units
                                  ↓
                           Validate entire
                              project
                                  ↓
                              repeat